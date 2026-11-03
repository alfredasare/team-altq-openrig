#!/usr/bin/python3
"""Team guard: Claude Code PreToolUse hook for Bash commands.

Reads the hook JSON on stdin and decides per command:
  deny -> exit 2 with the reason on stderr (the command never runs)
  ask  -> prints a permissionDecision "ask" (Alfred must approve, even in auto mode)
  none -> exits 0 silently, so the normal permission rules and mode apply

The tiers are in knowledge/approvals.md. Run `guard.py --selftest` after any change.
The command parsing is the Gaya and 4th-IR teams' guard (~/Gaya/team-gaya/hooks/guard.py); the checks are 40act's:
Google Cloud and the filings bucket, Mongo through bin/db.sh, model re-reads that cost money, Stripe.
"""
import json
import os
import re
import shlex
import subprocess
import sys

ROOT = "/Users/alfredamoah/AltQ/team-altq"
BIN_DIR = ROOT + "/bin/"

# Nobody pushes to these: main is promoted from development outside the team, and feature/new-sync is sync v2's
# integration branch, which takes pull requests.
PROTECTED_BRANCHES = {"main", "master", "development", "feature/new-sync"}
# Alfred's own containers: 40act's Redis and Gaya's database.
OWN_CONTAINERS = re.compile(r"^(40act-redis|gaya-[\w.-]+)$")
# Folders an agent may rm -rf without asking: temp space and the team's own worktrees.
SAFE_RM = ("/tmp/", "/private/tmp/", "/var/folders/", "/Users/alfredamoah/AltQ/.worktrees/")

# Any mention asks: OpenRig's launch allow list lets cat/head/tail/grep/rg/find run without a prompt.
SECRET_PATH = re.compile(
    r"(^|[\s/'\"=@])\.secrets(/|\b)|\.pem\b|\bid_(rsa|ed25519|ecdsa)\b|-sa\.json\b|"
    r"(^|[\s/'\"=@])\.env(?!\.(example|sample|template)\b)(\.[\w-]+)?\b|"
    r"\.(ssh|aws)/|\.config/(gh|gcloud)/|\.docker/config\.json|\.(netrc|npmrc|pgpass)\b|\.openrig/secrets|"
    r"\.credentials\.json|application_default_credentials|MONGODB_URI")
# `bun --env-file=<file> run|test …` hands the file to the process without printing it, so the mention alone doesn't
# ask; with -e/--eval/--print the command itself could print a value, so it does.
ENV_FILE_ARG = re.compile(r"--env-file[= ]\S+")
PRINTS = re.compile(r"(^|\s)(-e|--eval|-p|--print)(\s|$)")
WRAPPERS = {"sudo", "time", "nohup", "command", "builtin", "exec", "nice", "env", "xargs", "stdbuf"}
SHELLS = {"bash", "sh", "zsh"}
INTERPRETERS = {"python", "python3", "node", "ruby", "perl"}
RUNNERS = WRAPPERS | {"timeout", "watch", "parallel", "script", "su", "find", "flock", "caffeinate", "unbuffer"}
CHECKED = SHELLS | INTERPRETERS | {"eval", "gh", "git", "curl", "wget", "rm", "security", "docker", "gcloud", "gsutil",
                                   "mongosh", "mongo", "atlas", "auth0", "stripe", "bun", "db.sh", "pkill", "killall"}
SENSITIVE_TOOLS = re.compile(r"\b(gh|gcloud|gsutil|mongosh|atlas|auth0|stripe|pkill|killall)\b|"
                             r"git\b.{0,40}\bpush\b|curl\b.{0,80}-X|docker\b.{0,40}\b(compose|rm|stop|exec)\b|"
                             r"\b(insert(One|Many)?|update(One|Many)?|delete(One|Many)|replaceOne|bulkWrite|drop)\s*\(")

# gcloud: these only read. Anything else (deploy, execute, submit, IAM, create, delete…) asks.
GCLOUD_READ_VERBS = {"list", "describe", "read", "log", "logs", "get-iam-policy", "get-value", "info", "ls", "cat",
                     "du", "tail", "print-settings", "versions"}
GCLOUD_CREDENTIAL = {("auth", "print-access-token"), ("auth", "print-identity-token"),
                     ("auth", "application-default", "print-access-token")}
DB_WRITE_TARGETS = {"prod-write": "the prod database", "dev-write": "the shared dev database (40act_dev)"}


class Decision(Exception):
    def __init__(self, kind, reason):
        super().__init__(reason)
        self.kind, self.reason = kind, reason


def deny(reason):
    raise Decision("deny", reason)


class Asks:
    def __init__(self):
        self.reasons = []

    def add(self, reason):
        if reason not in self.reasons:
            self.reasons.append(reason)


def split_segments(cmd):
    """Split on ; | & newline ( ) outside quotes, like the shell. $( and backticks start a new segment even inside
    double quotes, because the shell runs them there too."""
    segs, cur, quote, i = [], [], None, 0
    while i < len(cmd):
        c = cmd[i]
        if quote == "'":
            quote = None if c == "'" else quote
        elif c == "\\" and i + 1 < len(cmd):
            cur.append(cmd[i:i + 2])
            i += 2
            continue
        elif cmd.startswith("$(", i) or c == "`":
            segs.append("".join(cur))
            cur = []
            i += 2 if c == "$" else 1
            continue
        elif quote == '"':
            quote = None if c == '"' else quote
        elif c in "'\"":
            quote = c
        elif c in ";|&\n()":
            segs.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    segs.append("".join(cur))
    return segs


def tokens_of(segment):
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return [t.strip("\"'") for t in segment.split()]


def strip_wrappers(toks):
    """Drop leading VAR=value assignments and wrappers like `timeout 30`, `env`, `sudo`."""
    i = 0
    while i < len(toks):
        t = toks[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t):
            i += 1
        elif t in WRAPPERS:
            i += 1
        elif t == "timeout" and i + 1 < len(toks):
            i += 2
        else:
            break
    return toks[i:]


def assignments(toks):
    """The VAR=value pairs that prefix a command (`MONGODB_DB=40act_dev bun test`)."""
    out = {}
    for t in toks:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", t)
        if not m:
            break
        out[m.group(1)] = m.group(2)
    return out


def words_of(args):
    """Positional words, with each long flag's value dropped (`--project x list` gives ['list'])."""
    skip, out = False, []
    for a in args:
        if skip:
            skip = False
            continue
        if a.startswith("--") and "=" not in a:
            skip = a not in ("--quiet", "--recursive", "--help", "--version", "--json", "--no-clobber")
            continue
        if a.startswith("-"):
            continue
        out.append(a)
    return out


def git_current_branch(repo_dir):
    try:
        out = subprocess.run(["git", "-C", repo_dir, "rev-parse", "--abbrev-ref", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def check_git(args, asks, repo_dir):
    i, sub = 0, None
    while i < len(args):
        a = args[i]
        if a == "-C" and i + 1 < len(args):
            repo_dir = os.path.join(repo_dir, os.path.expanduser(args[i + 1]))
            i += 2
            continue
        if a == "-c" and i + 1 < len(args):
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        sub = a
        break
    if sub is None:
        return
    sargs = args[i + 1:]
    if sub == "push":
        if any(a in ("--force", "-f", "--force-if-includes") or a.startswith("--force-with-lease")
               or (re.match(r"^-[a-zA-Z]+$", a) and "f" in a) for a in sargs):
            deny("force push is never allowed")
        positional = [a for a in sargs if not a.startswith("-")]
        if any(p.startswith("+") for p in positional[1:]):
            deny("force push (+refspec) is never allowed")
        if any(a in ("--mirror", "--all", "--tags", "--delete", "-d", "--prune") for a in sargs) or \
                any(p.startswith(":") for p in positional[1:]):
            asks.add("git push with --all/--tags/--mirror/--delete")
        refspecs = positional[1:]
        if refspecs:
            targets = []
            for r in refspecs:
                dst = r.split(":", 1)[1] if ":" in r else r
                dst = dst.replace("refs/heads/", "")
                if dst == "HEAD":
                    dst = git_current_branch(repo_dir)
                targets.append(dst)
        else:
            targets = [git_current_branch(repo_dir) or "unknown"]
        hit = [t for t in targets if t in PROTECTED_BRANCHES or t in ("", "unknown")]
        if hit:
            asks.add("git push to %s (nobody pushes to main, development or feature/new-sync; push your own branch "
                     "and open a pull request)" % ", ".join(sorted(set(hit))))
    elif sub == "reset" and "--hard" in sargs:
        asks.add("git reset --hard discards work")
    elif sub == "clean" and any(re.match(r"^-[a-zA-Z]*f", a) for a in sargs):
        asks.add("git clean deletes untracked files")
    elif sub == "branch" and any(a in ("-D", "--delete") for a in sargs):
        asks.add("deletes a git branch")
    elif sub in ("checkout", "restore") and "." in sargs:
        asks.add("discards local changes")
    elif sub in ("filter-branch", "filter-repo"):
        deny("history rewriting is never allowed")


def check_gh(args, asks, whole):
    a0 = args[0] if args else ""
    a1 = args[1] if len(args) > 1 else ""
    if a0 == "repo" and a1 == "delete":
        deny("gh repo delete is never allowed")
    if a0 == "auth" and a1 == "token":
        deny("printing the GitHub token is never allowed")
    if a0 == "auth" and a1 in ("logout", "refresh", "login", "switch", "setup-git"):
        asks.add("changes the GitHub CLI login")
    if a0 == "pr" and a1 == "merge":
        asks.add("merges a pull request (Alfred merges)")
    if a0 == "pr" and a1 == "review" and any(a in ("--approve", "-a") for a in args):
        asks.add("approves a pull request")
    if a0 == "repo" and a1 in ("create", "edit", "rename", "archive", "unarchive", "transfer", "fork"):
        asks.add("gh repo %s" % a1)
    if a0 in ("secret", "variable") and a1 in ("set", "delete", "remove"):
        asks.add("changes GitHub %ss" % a0)
    if a0 == "workflow" and a1 in ("run", "enable", "disable"):
        asks.add("gh workflow %s" % a1)
    if a0 == "run" and a1 in ("rerun", "cancel", "delete"):
        asks.add("gh run %s" % a1)
    if a0 == "release" and a1 in ("create", "delete", "edit", "upload"):
        asks.add("gh release %s" % a1)
    if a0 == "api":
        method = None
        for j, a in enumerate(args):
            if a in ("-X", "--method") and j + 1 < len(args):
                method = args[j + 1].upper()
            elif a.startswith("--method="):
                method = a.split("=", 1)[1].upper()
            elif re.match(r"^-X[A-Za-z]+$", a):
                method = a[2:].upper()
        has_body = any(a in ("-f", "-F", "--field", "--raw-field", "--input") or
                       a.startswith(("--field=", "--raw-field=", "--input=")) for a in args)
        if "graphql" in args:
            if re.search(r"\bmutation\b", whole):
                asks.add("GitHub GraphQL mutation")
        elif (method and method != "GET") or (method is None and has_body):
            asks.add("GitHub API write (%s)" % (method or "POST"))


def check_storage_copy(sub, words, asks):
    """cp/mv/rsync with gsutil or gcloud storage: a gs:// destination writes the filings bucket (shared with prod)."""
    if sub == "mv":
        asks.add("moves objects in the filings bucket (it deletes the source)")
    elif words and words[-1].startswith("gs://"):
        asks.add("writes to the filings bucket, which dev and prod share (%s %s)" % (sub, words[-1]))


def check_gcloud(args, asks):
    words = words_of(args)
    if tuple(words[:3]) in GCLOUD_CREDENTIAL or tuple(words[:2]) in GCLOUD_CREDENTIAL:
        deny("printing a Google credential is never allowed")
    if words[:1] == ["auth"] and words[1:2] != ["list"]:
        asks.add("changes the Google sign-in (Alfred runs `gcloud auth application-default login` himself)")
        return
    if words[:3] == ["secrets", "versions", "access"]:
        asks.add("prints a secret from Secret Manager")
        return
    if words[:1] == ["storage"]:
        sub = words[1] if len(words) > 1 else ""
        if sub in ("rm", "delete") or words[1:3] in (["buckets", "delete"], ["objects", "delete"]):
            deny("deleting from the filings bucket (shared by dev and prod) is never allowed")
        if sub in ("cp", "mv", "rsync"):
            check_storage_copy(sub, words[2:], asks)
            return
        if sub in GCLOUD_READ_VERBS or (len(words) > 2 and words[2] in GCLOUD_READ_VERBS):
            return
        asks.add("gcloud storage %s (not a read)" % sub)
        return
    if words[:1] == ["config"] and words[1:2] in (["list"], ["get"], ["get-value"], ["configurations"]):
        return
    if any(w in GCLOUD_READ_VERBS for w in words[1:]):
        return
    asks.add("gcloud %s: a deploy, a job run or another change (only reads run without asking)" % " ".join(words[:3]))


def check_gsutil(args, asks):
    words = words_of(args)
    sub = words[0] if words else ""
    if sub == "rm":
        deny("deleting from the filings bucket (shared by dev and prod) is never allowed")
    if sub in ("cp", "mv", "rsync"):
        check_storage_copy(sub, words[1:], asks)
    elif sub not in ("ls", "cat", "stat", "du", "version", "help"):
        asks.add("gsutil %s (not a read)" % sub)


def check_docker(args, asks):
    a = [x for x in args if not x.startswith("--context") and x != "orbstack"]
    sub = next((x for x in a if not x.startswith("-")), "")
    rest = a[a.index(sub) + 1:] if sub in a else []
    if sub == "compose" or (sub == "container" and rest[:1] == ["prune"]):
        if any(x in ("-v", "--volumes") or re.match(r"^-[a-zA-Z]*v[a-zA-Z]*$", x) for x in rest):
            deny("`docker compose … -v` deletes every volume in the project")
    if sub in ("system", "volume") and any(x in ("prune", "rm") for x in rest):
        asks.add("removes Docker volumes or data (docker %s %s)" % (sub, " ".join(rest[:2])))
    if sub in ("rm", "stop", "kill", "restart", "exec", "pause") or \
            (sub == "container" and rest[:1] and rest[0] in ("rm", "stop", "kill", "restart", "exec")):
        names = [x for x in rest if not x.startswith("-")]
        if any(OWN_CONTAINERS.match(n) for n in names):
            asks.add("touches one of Alfred's own containers (%s)" % ", ".join(n for n in names if OWN_CONTAINERS.match(n)))


def check_http(args, asks):
    url = next((a for a in args if re.match(r"^https?://", a)), "")
    if "api.stripe.com" not in url:
        return
    method = None
    for j, a in enumerate(args):
        if a in ("-X", "--request") and j + 1 < len(args):
            method = args[j + 1].upper()
        elif re.match(r"^-X[A-Za-z]+$", a):
            method = a[2:].upper()
    body = any(a in ("-d", "--data", "--data-raw", "--data-binary", "--data-urlencode", "-F", "--form",
                     "--json", "-T", "--upload-file") or a.startswith(("--data", "--json", "--form")) for a in args)
    if (method and method not in ("GET", "HEAD", "OPTIONS")) or (method is None and body):
        asks.add("a write to Stripe (%s %s)" % (method or "POST", url))


def check_bun(args, env, asks, whole):
    words = words_of(args)
    if "test" in words[:1] and env.get("MONGODB_DB", "") == "40act_dev":
        asks.add("tests against 40act_dev write to the shared dev database (integration suites wiped the tier fund "
                 "lists on 27 Oct 2026); use MONGODB_DB=40act_test")
    if any(w.endswith("migrate.ts") for w in words) and env.get("MONGODB_DB") != "40act_test":
        asks.add("a migration against a database other than 40act_test changes validators and indexes for everyone")
    if any(w.endswith("sync-v2.ts") for w in words) and any(a in ("--fresh", "--reread") for a in args):
        asks.add("sync v2 with %s reads every filing with the model again, which costs money"
                 % " ".join(a for a in args if a in ("--fresh", "--reread")))
    if ENV_FILE_ARG.search(whole) and PRINTS.search(whole):
        asks.add("evaluates code with an env file loaded, which could print a secret")


def check_segment(seg, asks, state, whole):
    raw = tokens_of(seg.strip())
    env = assignments(raw)
    while raw and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", raw[0]):
        raw = raw[1:]
    # Programs that run another command after their own options (`sudo -u x sh -c …`, `watch -n5 '…'`, `find -exec …`).
    if raw and os.path.basename(raw[0]) in RUNNERS:
        for i, a in enumerate(raw[1:], 1):
            if os.path.basename(a) in CHECKED:
                check_segment(shlex.join(raw[i:]), asks, state, whole)
                break
            if " " in a:
                for r in decide(a, state["dir"]):
                    asks.add(r)
    toks = strip_wrappers(raw)
    if not toks:
        return
    prog = os.path.basename(toks[0])
    args = toks[1:]
    if prog == "cd" and args:
        state["dir"] = os.path.join(state["dir"], os.path.expanduser(args[0]))
        return
    # Code the guard can't see on the command line: check inline code recursively, ask for unknown scripts.
    if prog in SHELLS and args:
        if args[0] == "-c" and len(args) > 1:
            for r in decide(args[1], state["dir"]):
                asks.add(r)
            return
        if not args[0].startswith("-") and not os.path.abspath(os.path.join(state["dir"], args[0])).startswith(BIN_DIR):
            asks.add("runs script %s (the guard can't inspect what it does)" % args[0])
            return
    if prog == "eval" and args:
        for r in decide(" ".join(args), state["dir"]):
            asks.add(r)
        return
    if prog in INTERPRETERS and any(a in ("-c", "-e") for a in args):
        for m in re.finditer(r"\b(?:python3?|node|ruby|perl)\s+-[ce]\s+([\"'])(.*?)\1", whole, re.S):
            if SENSITIVE_TOOLS.search(m.group(2)):
                asks.add("inline %s code that calls git, cloud, database or container tools" % prog)
        return
    if prog in ("source", ".") and args and args[0].endswith(".sh"):
        asks.add("sources script %s" % args[0])
    if prog in ("pkill", "killall"):
        deny("stop a process by PID (lsof -nP -iTCP:<port> -sTCP:LISTEN -t), never by name or pattern")
    if prog == "git":
        check_git(args, asks, state["dir"])
    elif prog == "gh":
        check_gh(args, asks, whole)
    elif prog == "gcloud":
        check_gcloud(args, asks)
    elif prog == "gsutil":
        check_gsutil(args, asks)
    elif prog == "docker":
        check_docker(args, asks)
    elif prog in ("curl", "wget", "http", "xh"):
        check_http(args, asks)
    elif prog == "bun":
        check_bun(args, env, asks, whole)
    elif prog == "db.sh":
        target = args[0] if args else ""
        if target in DB_WRITE_TARGETS:
            asks.add("writes to %s" % DB_WRITE_TARGETS[target])
    elif prog in ("mongosh", "mongo", "mongoexport", "mongoimport", "mongodump", "mongorestore"):
        if not any(a in ("--version", "--help", "-h") for a in args):
            asks.add("a direct Mongo connection: use %sdb.sh <dev|test|prod>, which reads the address without printing "
                     "it and refuses prod writes" % BIN_DIR)
    elif prog == "atlas" and not any(a in ("--version", "--help", "-h") for a in args):
        asks.add("the Atlas CLI changes clusters, users or the access list")
    elif prog == "auth0" and not any(a in ("--version", "--help", "-h") for a in args):
        asks.add("the Auth0 CLI changes tenant settings or users")
    elif prog == "stripe":
        if "--live" in args:
            asks.add("the Stripe CLI against live mode")
    elif prog == "security" and args and args[0] in ("find-generic-password", "find-internet-password", "dump-keychain"):
        asks.add("reads a secret from the macOS Keychain")
    elif prog == "rm" and any(re.match(r"^-[a-zA-Z]*r", a) for a in args) and any(re.match(r"^-[a-zA-Z]*f", a) for a in args):
        targets = [a for a in args if not a.startswith("-")]
        if any(not os.path.abspath(os.path.join(state["dir"], os.path.expanduser(t))).startswith(SAFE_RM) for t in targets):
            asks.add("rm -rf outside a temp folder or the team's worktrees")


def decide(cmd, cwd):
    asks = Asks()
    state = {"dir": cwd or os.getcwd()}
    if re.search(r"\bsk_live_", cmd):
        deny("a live Stripe key never goes on a command line")
    scrubbed = cmd if PRINTS.search(cmd) else ENV_FILE_ARG.sub("", cmd)
    if SECRET_PATH.search(scrubbed):
        asks.add("touches a credentials file or a connection string")
    for seg in split_segments(cmd):
        check_segment(seg, asks, state, cmd)
    return asks.reasons


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command") or ""
    try:
        reasons = decide(cmd, data.get("cwd") or "")
    except Decision as d:
        if d.kind == "deny":
            sys.stderr.write("BLOCKED by the team guard: %s\n" % d.reason)
            return 2
        reasons = [d.reason]
    if reasons:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": "Team guard: " + "; ".join(reasons)}}))
    return 0


# ----------------------------------------------------------------------------- self-test
DB = BIN_DIR + "db.sh"
CASES = [
    # (command, expected: "deny" | "ask" | "none")
    ("git status", "none"),
    ("git -C ~/AltQ/40act log --oneline -5", "none"),
    ("git -C ~/AltQ/.worktrees/gideon/fix-x push origin fix/x", "none"),
    ("git push --dry-run origin fix/x", "none"),
    ("git push origin development", "ask"),
    ("git push origin main", "ask"),
    ("git push origin feature/new-sync", "ask"),
    ("git push origin HEAD:development", "ask"),
    ("git push --force origin feat", "deny"),
    ("git push --force-with-lease origin feat", "deny"),
    ("git push origin +feat", "deny"),
    ("git reset --hard origin/development", "ask"),
    ("git filter-repo --path x", "deny"),
    ("gh pr create --base development --fill", "none"),
    ("gh pr view 437 -R 94562352QuebecInc/40act", "none"),
    ("gh pr merge 437 --merge", "ask"),
    ("gh pr review 437 --approve", "ask"),
    ("gh repo delete 94562352QuebecInc/40act --yes", "deny"),
    ("gh auth token", "deny"),
    ("gh run list -R 94562352QuebecInc/40act", "none"),
    ("gh run rerun 123 --failed", "ask"),
    ("gh api repos/94562352QuebecInc/40act/pulls", "none"),
    ("gh api repos/94562352QuebecInc/40act/pulls/437/merge -X PUT", "ask"),
    ("gcloud auth list", "none"),
    ("gcloud auth print-access-token", "deny"),
    ("gcloud auth application-default print-access-token", "deny"),
    ("gcloud auth application-default login", "ask"),
    ("gcloud storage ls gs://act-498418-sec-raw/2061233/", "none"),
    ("gcloud storage cat gs://act-498418-sec-raw/2061233/0001580642-26-003682/norm/norm-v2/morganstanley_ncsr.htm.md", "none"),
    ("gcloud storage cp gs://act-498418-sec-raw/2061233/a.md /tmp/a.md", "none"),
    ("gcloud storage cp /tmp/a.md gs://act-498418-sec-raw/2061233/a.md", "ask"),
    ("gcloud storage rm gs://act-498418-sec-raw/2061233/a.md", "deny"),
    ("gsutil cat gs://act-498418-sec-raw/x", "none"),
    ("gsutil rm -r gs://act-498418-sec-raw/x", "deny"),
    ("gcloud run services list --project act-498418", "none"),
    ("gcloud run services describe act-worker --region us-east1", "none"),
    ("gcloud builds list --limit 5", "none"),
    ("gcloud logging read 'resource.type=cloud_run_revision' --limit 20", "none"),
    ("gcloud run deploy act-api --image x", "ask"),
    ("gcloud run jobs execute act-sync", "ask"),
    ("gcloud builds submit --config infra/web/cloudbuild.yaml", "ask"),
    ("gcloud secrets versions access latest --secret mongo", "ask"),
    (DB + " prod --eval 'db.facts_v2.countDocuments({})'", "none"),
    (DB + " dev --eval 'db.funds.countDocuments({})'", "none"),
    (DB + " test --eval 'db.x.insertOne({a:1})'", "none"),
    (DB + " prod-write --eval 'db.facts_v2.insertOne({})'", "ask"),
    (DB + " dev-write --eval 'db.funds.updateOne({},{})'", "ask"),
    ("mongosh --version", "none"),
    ("mongosh mongodb+srv://u:p@40act.jpjv34a.mongodb.net/ --eval 1", "ask"),
    ("cat ~/AltQ/40act/apps/api/.env", "ask"),
    ("grep MONGODB_URI_REVIEW apps/api/.env", "ask"),
    ("cat .env.example", "none"),
    ("FACTS_COLLECTION_SUFFIX=_v2 MONGODB_DB=40act_dev bun --env-file=apps/worker/.env run apps/worker/src/cli/sync-v2.ts --only 2061233 --out /tmp/x", "none"),
    ("FACTS_COLLECTION_SUFFIX=_v2 MONGODB_DB=40act_dev bun --env-file=apps/worker/.env run apps/worker/src/cli/sync-v2.ts --only 2061233 --fresh", "ask"),
    ("FACTS_COLLECTION_SUFFIX=_v2 MONGODB_DB=40act_dev bun --env-file=apps/worker/.env run apps/worker/src/cli/sync-v2.ts --only 2061233 --steps statements --reread", "ask"),
    ("bun --env-file=apps/api/.env -e 'console.log(process.env.MONGODB_URI)'", "ask"),
    ("MONGODB_DB=40act_test bun --env-file=apps/api/.env test packages/db/src/repositories/syncV2Indexes.integration.test.ts", "none"),
    ("MONGODB_DB=40act_dev bun test packages/db", "ask"),
    ("MONGODB_DB=40act_test bun run packages/db/src/migrate.ts", "none"),
    ("MONGODB_DB=40act_dev bun run packages/db/src/migrate.ts", "ask"),
    ("bun test --path-ignore-patterns='**/*.integration.test.ts'", "none"),
    ("bun run lint", "none"),
    ("curl -s -A 'AltQ Research aamoah@altq.ai' https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany", "none"),
    ("curl -s https://api.stripe.com/v1/customers -u sk_test_x:", "none"),
    ("curl -s -X POST https://api.stripe.com/v1/refunds -u sk_test_x:", "ask"),
    ("curl https://api.stripe.com/v1/charges -u sk_live_abc:", "deny"),
    ("stripe listen --forward-to localhost:3390/api/stripe", "none"),
    ("atlas accessLists create 1.2.3.4", "ask"),
    ("docker ps", "none"),
    ("docker restart 40act-redis", "ask"),
    ("docker compose down -v", "deny"),
    ("pkill -f 'next dev'", "deny"),
    ("killall node", "deny"),
    ("kill 48213", "none"),
    ("cat ~/.config/gcloud/application_default_credentials.json", "ask"),
    ("cat ~/AltQ/40act/sync-v2-sa.json", "ask"),
    ("rm -rf /Users/alfredamoah/AltQ/.worktrees/gideon/fix-x", "none"),
    ("rm -rf /tmp/scratch", "none"),
    ("rm -rf ~/AltQ/40act", "ask"),
    ('bash -c "git push origin development"', "ask"),
    ("sh deploy.sh", "ask"),
    ("/Users/alfredamoah/AltQ/team-altq/bin/desk.sh status", "none"),
    ('echo "$(gh pr merge 1 -R a/b)"', "ask"),
    ("xargs -I{} sh -c 'git push origin main'", "ask"),
    ('eval "gh pr merge 1 -R a/b"', "ask"),
    ("python3 -c \"import subprocess; subprocess.run(['gcloud','run','deploy'])\"", "ask"),
    ("node -e \"db.facts.deleteMany({})\"", "ask"),
    ("python3 -c \"print(1)\"", "none"),
    ('rig queue handoff q1 --to kezess-review@altq --note "ready; do not run gh pr merge"', "none"),
    ("ls -la && git status", "none"),
]


def selftest():
    failures = 0
    for cmd, expected in CASES:
        try:
            got = "ask" if decide(cmd, "/tmp") else "none"
        except Decision as d:
            got = d.kind
        mark = "ok " if got == expected else "FAIL"
        if got != expected:
            failures += 1
        print("%s %-5s %s" % (mark, got, cmd))
    print("\n%d/%d passed" % (len(CASES) - failures, len(CASES)))
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    sys.exit(main())
