# Quality review and clean-ups

40act carries junk from fast work: unused files and exports, duplicated helpers, old fallbacks. New work must not add
to it. Kezess checks quality in every review, in the same pass as correctness.

## The checklist, per diff
1. **Reuse.** For each new function, helper, type, constant or component, search the repo (`git grep -n '<name or
   key phrase>'`, then by behaviour). If one exists, the finding names it and the change uses it. Re-implementing
   what exists a few files over is the most common failure.
2. **Nothing unused.** Every new export has an importer (`git grep`). There is:
   - no dead branch;
   - no commented-out code;
   - no option, flag or config that nothing sets;
   - no scaffolding "for later";
   - no test helper used once that could be inline.
3. **The smallest change.** Can a branch, a file, a layer or a parameter go? Name it.
4. **The repo's structure rules** (40act `CLAUDE.md`):
   - one exported component or class per file;
   - a file past about 250 lines is split before it grows;
   - web feature code lives in `features/<area>/`, and `components/ui/` holds primitives only;
   - API routes are thin;
   - internal helpers stay unexported.
5. **Comments say why:** constraints, incidents, rejected alternatives. Never "added X", "fixed Y", or a restatement of
   the code.
6. **Tests prove the change:** each would fail if the code broke, and they cover the real edge cases, not only the
   happy path.

Findings: numbered, `file:line`, what to delete or reuse instead, severity.

## Clean-ups
- **Candidates** go in `../backlog.md` under **Clean-ups**: the path, what to delete or fold, the evidence it's unused
  or duplicated (the `git grep` that shows no importer), and the risk.
- **A clean-up is its own change** (Gideon), never folded into a feature.
  - Behaviour stays identical, and the tests show it: the full unit suite, lint, typecheck, and the web build for web
    code.
  - "Unused" is shown, not assumed: no importer, no dynamic import, no script or CI step that names it.
- **Kezess reviews a clean-up like any change:** did anything still use what was deleted?
