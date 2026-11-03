# Tests and gates

The definition of done is in 40act's `CLAUDE.md`. This is how to run it from a worktree.

## Unit tests and the gates (what CI runs)
```
bun test --path-ignore-patterns='**/*.integration.test.ts'    # ~5 min, ~49,700 tests
bun run lint
bun run typecheck
bun run typecheck:scripts
bun run --cwd apps/web build                                  # when apps/web changed
```
Run from the worktree root. A test that fails only in the full run but passes alone is usually Atlas contention:
re-run the file alone and report both.

## Integration tests (the Mongo-backed seams)
- **Only against `40act_test`,** never `40act_dev`. On 27 Oct 2026 API suites pointed at dev called `setTierScopes`,
  which writes a revision for all three tiers. That emptied every dev tier's fund list, which Florian, Nil and Alfred
  rely on.
- **From a worktree,** which has no `.env`, pass Alfred's root one:
  ```
  MONGODB_DB=40act_test bun --env-file=/Users/alfredamoah/AltQ/40act/.env test packages/db
  MONGODB_DB=40act_test bun --env-file=/Users/alfredamoah/AltQ/40act/apps/api/.env test <file>.integration.test.ts
  ```
- **A new collection or a changed contract** needs the migration on `40act_test` first:
  `MONGODB_DB=40act_test bun --env-file=/Users/alfredamoah/AltQ/40act/.env run packages/db/src/migrate.ts`. Until
  then a unique-index assertion fails, or Mongo answers "Document failed validation" naming no field. That is the
  test working.
- **New integration tests assert the connection in their first test,** so an unset `MONGODB_URI` is a red suite,
  not a silent skip (see `packages/db/src/repositories/sl/returnSeries.integration.test.ts`).
- **The `runs` suite** needs Redis on :6379. Exclude it, or ask Alfred (his `40act-redis` container is his).

## NAV
Touching a NAV reader, fact selection or `packages/contracts/src/nav.ts` adds
`bun run check:nav --expect-host=<cluster>` against `40act_dev` (a read). It fails when any reader shows a different
fund NAV from the one rule.

## Reporting
Say what ran and what passed, with the counts. Say what could not run and why. Never imply coverage that doesn't
exist.
