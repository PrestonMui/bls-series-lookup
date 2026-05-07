# BLS Series Lookup — Project Notes

A static single-file HTML tool for searching BLS series codes. Built by running `python build.py`, which reads the CSV catalogs in `data/` and generates `index.html` with the data baked in as inline JSON. Deployed on GitHub Pages.

## Future considerations

A running list of improvements worth revisiting. Not prioritized — each is a standalone enhancement.

### Search quality

- **Spelling tolerance.** Current matcher requires every character to appear in sequence. Typos like "unemplyment" won't match. Could add a Levenshtein-distance fallback for tokens that completely fail to match.
- **Plurals / stemming.** "employees" won't whole-word-match "employee". Minor but noticeable.
- **Synonyms and abbreviations.** "CPI" won't match "Consumer Price Index" descriptions; "US" vs "U.S." matters; "SF" vs "San Francisco". A small synonym map could help.
- **Parenthesized prefix normalization in other programs.** The `ln` program has `(Seas)` / `(Unadj)` prefixes moved to the end in `build.py`. Worth checking if `ce`, `cx`, `tu`, `wp` have similar prefixes that interfere with ranking.

### Performance

- **Debouncing.** With 385K rows in `cx`, every keystroke runs the full matcher. On slow devices this can stutter. A 100ms debounce on the input would be safer.
- **File size.** The generated HTML is ~44 MB. Slow initial load on mobile. Lazy-loading per-program data via `fetch` at first program-switch would drop initial load to a few MB.

### UX

- **Deep linking / shareable URLs.** No way to share a search or a selected list. Could use a URL hash like `#?program=ln&q=unemployment&selected=LNS14000000,LNS14000001`.
- **Persistence.** Selected series are lost on refresh. `localStorage` would preserve them across reloads.
- **Mobile layout.** Results rows have `Series ID | Description | + Add` in a flex row. On narrow screens the description may wrap oddly — needs a real mobile pass.
- **Result count cap.** Always 25. No way to see more. Could add a "Load more" button or make it configurable.
- **Default state when query is empty.** Currently nothing displays. Could show the first 25 of the program or a curated list of most-used series.
- **Accessibility.** No `aria-label` on the add buttons, no `role="listbox"` on results, no live region announcing result counts for screen readers.
- **Clear button.** No `×` inside the search input to quickly clear it.

### Correctness / edge cases

- **Duplicate series IDs across programs.** Some series appear in more than one catalog. Not a problem today since search is scoped to one program, but worth awareness if that ever changes.
- **Frequency indicator.** Can't tell from looking at a series whether it's monthly, quarterly, or annual. A small badge would help.

### Maintenance

- **README is stale.** Doesn't document selection, copy/download, the SA filter, or the ranking algorithm.
- **CSV updates.** No script here to refresh the catalogs from BLS. `macrotools` has `scripts/generate_series_lists.py` — either point to it or copy the relevant pieces so refreshing data is a documented step.
- **Rebuild-on-edit.** `python build.py` is a manual step. A tiny watcher or `just build` target would speed iteration.

### Graphing and transforms (larger feature)

Earlier exploration produced a plan for adding graphing capabilities (line charts of selected series with per-series transforms like moving averages, annualized growth rates, etc.). The architecture concluded was: a lightweight serverless function (Cloudflare Workers + R2, Vercel, or AWS Lambda + S3) that reads pre-built data files (stored in Parquet or columnar JSON) and returns only the requested columns. Plan draft lives in `C:\Users\prest\.claude\plans\pure-giggling-ullman.md`.

Status: not built. Revisit when ready.

## Ranking algorithm (current behavior)

Results are sorted by a 5-tier hierarchical comparison. Each tier strictly dominates the next — lower tiers are tiebreakers only.

1. **Whole-word match count** — how many query tokens appear as complete words (bordered by space/punctuation) in the target text. More is better.
2. **Order bonus** — rewards whole-word matches that appear in the same order as the query, and prefers earlier positions in the text.
3. **Whole-word character count** — total chars covered by whole-word matches.
4. **Partial/greedy match score** — the character-by-character subsequence score with consecutive-run, word-boundary, prefix, and exact-substring bonuses.
5. **Aggregate preference** — +30 per `0` in the series id (for `ce`, `ci`, `cu`, `jt`, `ln`) plus a small brevity bonus. Favors aggregate series (e.g., `LNS14000000`) over detailed breakdowns when all other tiers tie.

## Build

- `python build.py` reads `data/series_{program}.csv` files and writes `index.html`.
- Global CLAUDE.md rule: use single quotes for Python strings.
