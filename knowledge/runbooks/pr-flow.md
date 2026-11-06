# From change to pull request

1. **Branch:** a worktree from `origin/development` (sync v2 too, since `feature/new-sync` merged on 4 Nov 2026), or
   the integration branch Arthur names:
   ```
   git -C /Users/alfredamoah/AltQ/40act fetch origin
   git -C /Users/alfredamoah/AltQ/40act worktree add /Users/alfredamoah/AltQ/.worktrees/<seat>/<branch> -b <branch> origin/development
   ```
   Then `bun install` at its root.
2. **Build** in small, understood steps, each with its test. Record a defect, then reproduce it, then fix it.
   A new page, flow or significant component is built to Rinia's picked design (her folder in
   `exports/rinia/designs/`, named in the plan).
3. **Commit:**
   - Conventional Commits scoped by workspace: `feat(facts): …`, `fix(worker): …`, `test(web): …`;
   - a contract change in its own commit, with its fixtures;
   - files added by name, never `git add -A`;
   - no `Co-Authored-By` or `Claude-Session` lines;
   - the message says what changed and why, in plain words.
4. **Checks, as queue items of their own:**
   - Kezess always;
   - Varay for the gates;
   - Ellie for UI;
   - Agrona when a page's values change;
   - Seris for auth, tiers or billing.

   Fix what they find, and send it back to whoever found it.
5. **Bring the branch up to date** with its target (`git fetch`, then rebase or merge, as the branch's history uses),
   and re-run the gates if anything came in.
6. **Push by name, dry run first:**
   ```
   git -C <worktree> push --dry-run origin <branch>
   git -C <worktree> push origin <branch>
   ```
   Never to `main` or `development`: the guard asks.
7. **Open the PR** into the target branch:
   - `gh pr create --base development --head <branch>`;
   - a title in the commit style;
   - a body that says what, why, and how it was tested (what ran, what passed), plus what is not tested;
   - no attribution lines.

   A contract change says whether its validator change is backward-safe and which databases need the migration
   before deploy.
8. **Alfred merges.** After the merge, remove the worktree (`git -C /Users/alfredamoah/AltQ/40act worktree remove <path>`).
