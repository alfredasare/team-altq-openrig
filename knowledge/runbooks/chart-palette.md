# Chart colours

40act's chart design guidelines document (`docs/260818_chart_design_guidelines.md`) does not exist. It was never
committed, though several chart files still cite it. The working substitutes:
- `apps/web/lib/charts/chartTokens.ts`: the token palette, with each token's job in its comments. Use its tokens;
  never guess a hex value.
- `scripts/validate_palette.js`: it encodes the guidelines' §9.1 contrast floors and runs in `bun test` through
  `validate_palette.test.ts`.

**Gate every new or changed chart mark** before review:
```
node scripts/validate_palette.js "#hex,#hex" --pairs all --surface "#hex"
```
It caught two shipped charts whose marks rendered at about a fifth of the required contrast. Those marks were
invisible to every reader, not only colour-blind ones. Kezess checks that the run is in the change's notes; Ellie
checks the marks on screen in both themes.
