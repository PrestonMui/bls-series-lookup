#!/usr/bin/env python3
"""Parse BLS series CSVs and bake them into a single index.html."""

import csv
import json
import os

PROGRAMS = {
    "ce": "Current Employment Statistics",
    "ci": "Employment Cost Index",
    "cu": "Consumer Price Index",
    "cx": "Consumer Expenditures Survey",
    "ei": "Import/Export Price Indices",
    "jt": "Job Openings, Layoffs and Turnover Survey",
    "ln": "Current Population Survey",
    "pc": "Producer Price Index (Industry)",
    "tu": "Time-use Survey",
    "wp": "Producer Price Index (Commodity)",
}

def load_data():
    data = {}
    for code, name in PROGRAMS.items():
        path = os.path.join("data", f"series_{code}.csv")
        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append([row["series_id"].strip(), row["description"].strip()])
        data[code] = rows
        print(f"  {code}: {len(rows)} series")
    return data

def build_html(data):
    programs_json = json.dumps({code: PROGRAMS[code] for code in PROGRAMS})
    data_json = json.dumps(data, separators=(",", ":"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BLS Series Lookup</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f0f1f3; color: #1a1a1a; padding: 16px; }}
.container {{ max-width: 820px; margin: 0 auto; }}
h1 {{ font-size: 1.3rem; font-weight: 600; margin-bottom: 12px; }}
h1 span {{ color: #666; font-weight: 400; }}

/* Program selector */
.program-row {{ display: flex; gap: 8px; margin-bottom: 12px; align-items: center; }}
.program-row label {{ font-size: 0.85rem; font-weight: 600; white-space: nowrap; }}
.program-row select {{ flex: 1; padding: 7px 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 0.9rem; background: #fff; }}

/* Search mode toggle */
.search-mode {{ display: flex; margin-bottom: 10px; }}
.search-mode button {{ flex: 1; padding: 7px 0; font-size: 0.85rem; border: 1px solid #ccc; background: #fff; color: #555; cursor: pointer; transition: background 0.12s, color 0.12s; }}
.search-mode button:first-child {{ border-radius: 6px 0 0 6px; }}
.search-mode button:last-child {{ border-radius: 0 6px 6px 0; border-left: none; }}
.search-mode button.active {{ background: #4a90d9; color: #fff; border-color: #4a90d9; }}

/* SA filter */
.sa-filter {{ display: none; margin-bottom: 10px; }}
.sa-filter.visible {{ display: flex; }}
.sa-filter button {{ flex: 1; padding: 7px 0; font-size: 0.85rem; border: 1px solid #ccc; background: #fff; color: #555; cursor: pointer; transition: background 0.12s, color 0.12s; }}
.sa-filter button:first-child {{ border-radius: 6px 0 0 6px; }}
.sa-filter button:nth-child(2) {{ border-left: none; }}
.sa-filter button:last-child {{ border-radius: 0 6px 6px 0; border-left: none; }}
.sa-filter button.active {{ background: #4a90d9; color: #fff; border-color: #4a90d9; }}

/* Search */
#search {{ width: 100%; padding: 10px 14px; font-size: 1rem; border: 2px solid #d0d0d0; border-radius: 8px; outline: none; transition: border-color 0.15s; }}
#search:focus {{ border-color: #4a90d9; }}
.hint {{ font-size: 0.78rem; color: #888; margin-top: 4px; margin-bottom: 10px; }}
.hint b {{ color: #555; }}

/* Detail panel */
#detail {{ display: none; background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px; }}
#detail.visible {{ display: block; }}
#detail .series-id {{ font-family: "SF Mono", "Cascadia Code", "Consolas", monospace; font-size: 1.05rem; font-weight: 600; margin-bottom: 4px; }}
#detail .title {{ font-size: 0.92rem; color: #333; margin-bottom: 8px; }}
#detail .meta {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
#detail .badge {{ display: inline-block; padding: 2px 9px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; color: #fff; }}
#detail .actions {{ margin-top: 10px; display: flex; gap: 8px; }}
#detail .actions a, #detail .actions button {{ padding: 5px 12px; font-size: 0.82rem; border-radius: 5px; cursor: pointer; text-decoration: none; border: 1px solid #ccc; background: #fff; color: #333; }}
#detail .actions a:hover, #detail .actions button:hover {{ background: #f5f5f5; }}
#detail .actions .copied {{ color: #2a7; border-color: #2a7; }}

/* Results list */
#results {{ list-style: none; }}
#results li {{ background: #fff; border: 1px solid transparent; border-radius: 6px; padding: 8px 12px; margin-bottom: 2px; cursor: pointer; display: flex; gap: 10px; align-items: baseline; transition: background 0.1s; }}
#results li:hover {{ background: #f7f8fa; }}
#results li.active {{ background: #fff; border-color: #4a90d9; }}
#results li .sid {{ font-family: "SF Mono", "Cascadia Code", "Consolas", monospace; font-size: 0.82rem; color: #555; white-space: nowrap; flex-shrink: 0; }}
#results li .desc {{ font-size: 0.88rem; color: #333; flex: 1; }}
#results li .score {{ font-family: "SF Mono", "Cascadia Code", "Consolas", monospace; font-size: 0.75rem; color: #aaa; white-space: nowrap; flex-shrink: 0; }}
#results-header {{ display: none; padding: 4px 12px; font-size: 0.75rem; color: #999; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; gap: 10px; align-items: baseline; }}
#results-header.visible {{ display: flex; }}
#results-header .h-sid {{ white-space: nowrap; flex-shrink: 0; }}
#results-header .h-desc {{ flex: 1; }}
#results-header .h-score {{ white-space: nowrap; flex-shrink: 0; }}
mark {{ background: #fce8a5; color: inherit; border-radius: 2px; padding: 0 1px; }}

#no-results {{ display: none; text-align: center; color: #999; padding: 32px 0; font-size: 0.95rem; }}
.byline {{ font-size: 0.82rem; color: #888; margin-bottom: 14px; }}
.byline a {{ color: #4a90d9; text-decoration: none; }}
.byline a:hover {{ text-decoration: underline; }}
footer {{ text-align: center; font-size: 0.78rem; color: #aaa; margin-top: 24px; padding-top: 12px; border-top: 1px solid #e0e0e0; }}
</style>
</head>
<body>
<div class="container">
  <h1>BLS Series Lookup <span>— search by series ID or description</span></h1>
  <div class="byline">Created by Preston Mui. <a href="https://github.com/PrestonMui/bls-series-lookup" target="_blank" rel="noopener">View on GitHub</a></div>
  <div class="program-row">
    <label for="program">Program:</label>
    <select id="program"></select>
  </div>
  <div class="search-mode">
    <button id="mode-desc" class="active" onclick="setMode('desc')">Search by Description</button>
    <button id="mode-id" onclick="setMode('id')">Search by Series ID</button>
  </div>
  <div class="sa-filter" id="sa-filter">
    <button class="active" onclick="setSA('all')">All</button>
    <button onclick="setSA('sa')">Seasonally Adjusted</button>
    <button onclick="setSA('nsa')">Not Seasonally Adjusted</button>
  </div>
  <input type="text" id="search" placeholder="Type to search descriptions…" autocomplete="off">
  <div class="hint"><span id="count"></span> &nbsp;|&nbsp; <b>&uarr;&darr;</b> navigate &nbsp; <b>Enter</b> select &nbsp; <b>Esc</b> clear</div>
  <div id="detail">
    <div class="series-id" id="d-id"></div>
    <div class="title" id="d-title"></div>
    <div class="meta"><span class="badge" id="d-badge"></span></div>
    <div class="actions">
      <button id="d-copy" onclick="copyId()">Copy ID</button>
      <a id="d-link" target="_blank" rel="noopener">View on BLS &nearr;</a>
    </div>
  </div>
  <div id="results-header"><span class="h-sid">Series ID</span><span class="h-desc">Description</span><span class="h-score">Score</span></div>
  <ul id="results"></ul>
  <div id="no-results">No series matched your query.</div>
  <footer>Built with Claude Code</footer>
</div>
<script>
// ── Data ──
const PROGRAMS = {programs_json};
const DATA = {data_json};

// ── Program colours ──
const programCodes = Object.keys(PROGRAMS);
const programColors = {{}};
programCodes.forEach((c, i) => {{
  programColors[c] = `hsl(${{Math.round(i * 360 / programCodes.length)}}, 55%, 45%)`;
}});

// ── DOM refs ──
const programEl = document.getElementById("program");
const searchEl = document.getElementById("search");
const resultsEl = document.getElementById("results");
const countEl = document.getElementById("count");
const detailEl = document.getElementById("detail");
const noResultsEl = document.getElementById("no-results");

const SA_PROGRAMS = new Set(["ce", "ci", "cu", "jt", "ln", "wp"]);
const ZERO_BONUS_PROGRAMS = new Set(["ce", "ci", "cu", "jt", "ln"]);

let currentProgram = programCodes[0];
let searchMode = "desc"; // "id" or "desc"
let saFilter = "all"; // "all", "sa", "nsa"
let filtered = [];
let activeIdx = -1;

function setMode(mode) {{
  searchMode = mode;
  document.getElementById("mode-id").classList.toggle("active", mode === "id");
  document.getElementById("mode-desc").classList.toggle("active", mode === "desc");
  searchEl.placeholder = mode === "id" ? "Type to search series IDs\u2026" : "Type to search descriptions\u2026";
  activeIdx = -1;
  hideDetail();
  runSearch();
  searchEl.focus();
}}

function setSA(mode) {{
  saFilter = mode;
  document.querySelectorAll("#sa-filter button").forEach((btn, i) => {{
    btn.classList.toggle("active", mode === ["all", "sa", "nsa"][i]);
  }});
  activeIdx = -1;
  hideDetail();
  runSearch();
  searchEl.focus();
}}

function updateSAVisibility() {{
  const el = document.getElementById("sa-filter");
  if (SA_PROGRAMS.has(currentProgram)) {{
    el.classList.add("visible");
  }} else {{
    el.classList.remove("visible");
    saFilter = "all";
    document.querySelectorAll("#sa-filter button").forEach((btn, i) => {{
      btn.classList.toggle("active", i === 0);
    }});
  }}
}}

// ── Populate dropdown ──
programCodes.forEach(c => {{
  const opt = document.createElement("option");
  opt.value = c;
  opt.textContent = `${{c}} — ${{PROGRAMS[c]}}`;
  programEl.appendChild(opt);
}});

programEl.addEventListener("change", () => {{
  currentProgram = programEl.value;
  activeIdx = -1;
  hideDetail();
  updateSAVisibility();
  runSearch();
  searchEl.focus();
}});

// ── Fuzzy matching ──
function scoreFrom(pLower, tLower, text, startIdx) {{
  const pLen = pLower.length;
  const tLen = tLower.length;
  const positions = [];
  let score = 0;
  let ci = 0;
  let prevMatch = -2;
  for (let ti = startIdx; ti < tLen && ci < pLen; ti++) {{
    if (tLower[ti] === pLower[ci]) {{
      positions.push(ti);
      score += 1;
      if (ti === prevMatch + 1) score += 8;
      if (ti === 0 || " _-.".includes(text[ti - 1])) score += 5;
      if (ti === 0 && ci === 0) score += 10;
      prevMatch = ti;
      ci++;
    }}
  }}
  if (ci < pLen) return null;
  return {{ score, positions }};
}}

function fuzzyMatchToken(token, text) {{
  const tLower = text.toLowerCase();
  const pLower = token.toLowerCase();
  const pLen = pLower.length;
  const tLen = tLower.length;
  if (pLen === 0) return {{ score: 0, positions: [] }};

  // Try starting the match at every position where the first char matches,
  // keep the best scoring alignment
  let best = null;
  for (let start = 0; start <= tLen - pLen; start++) {{
    if (tLower[start] === pLower[0]) {{
      const result = scoreFrom(pLower, tLower, text, start);
      if (result && (!best || result.score > best.score)) best = result;
    }}
  }}
  if (!best) return null;

  // Exact substring bonus
  const substringIdx = tLower.indexOf(pLower);
  if (substringIdx >= 0) {{
    best.score += substringIdx === 0 ? 35 : 20;
  }}

  return best;
}}

function fuzzyMatch(query, text) {{
  const tokens = query.trim().split(/\\s+/).filter(t => t.length > 0);
  if (tokens.length === 0) return {{ score: 0, positions: [] }};

  let totalScore = 0;
  const allPositions = new Set();
  let queryLen = 0;

  for (const token of tokens) {{
    const result = fuzzyMatchToken(token, text);
    if (!result) return null;
    totalScore += result.score;
    result.positions.forEach(p => allPositions.add(p));
    queryLen += token.length;
  }}

  // Brevity: normalize by text length so concise matches rank above verbose ones.
  // Multiply by 1000 and round to keep integer scores readable.
  totalScore = Math.round(totalScore * 1000 / text.length);

  return {{ score: totalScore, positions: allPositions }};
}}

// ── Highlighting ──
function highlightMatch(query, id, desc) {{
  if (searchMode === "id") {{
    const match = fuzzyMatch(query, id);
    const positions = match ? match.positions : new Set();
    let hId = "";
    for (let i = 0; i < id.length; i++) {{
      hId += positions.has(i) ? `<mark>${{escHtml(id[i])}}</mark>` : escHtml(id[i]);
    }}
    return [hId, escHtml(desc)];
  }} else {{
    const match = fuzzyMatch(query, desc);
    const positions = match ? match.positions : new Set();
    let hDesc = "";
    for (let i = 0; i < desc.length; i++) {{
      hDesc += positions.has(i) ? `<mark>${{escHtml(desc[i])}}</mark>` : escHtml(desc[i]);
    }}
    return [escHtml(id), hDesc];
  }}
}}

function escHtml(c) {{
  return c === "<" ? "&lt;" : c === ">" ? "&gt;" : c === "&" ? "&amp;" : c === '"' ? "&quot;" : c;
}}

// ── Search ──
function runSearch() {{
  const query = searchEl.value.trim();
  let series = DATA[currentProgram];
  if (saFilter === "sa") series = series.filter(s => s[0][2] === "S");
  else if (saFilter === "nsa") series = series.filter(s => s[0][2] === "U");

  if (!query) {{
    filtered = [];
    render(query);
    return;
  }} else {{
    const scored = [];
    for (let i = 0; i < series.length; i++) {{
      const s = series[i];
      const searchStr = searchMode === "id" ? s[0] : s[1];
      const m = fuzzyMatch(query, searchStr);
      if (m) {{
        let sc = m.score;
        if (ZERO_BONUS_PROGRAMS.has(currentProgram)) {{
          for (let j = 0; j < s[0].length; j++) {{ if (s[0][j] === "0") sc += 200; }}
        }}
        scored.push({{ id: s[0], desc: s[1], score: sc }});
      }}
    }}
    scored.sort((a, b) => b.score - a.score);
    filtered = scored.slice(0, 25);
  }}

  render(query);
}}

// ── Render ──
function render(query) {{
  let totalSeries = DATA[currentProgram].length;
  if (saFilter === "sa") totalSeries = DATA[currentProgram].filter(s => s[0][2] === "S").length;
  else if (saFilter === "nsa") totalSeries = DATA[currentProgram].filter(s => s[0][2] === "U").length;
  const headerEl = document.getElementById("results-header");
  if (filtered.length === 0) {{
    resultsEl.innerHTML = "";
    headerEl.classList.remove("visible");
    noResultsEl.style.display = query ? "block" : "none";
    countEl.textContent = query ? "0 results" : `${{totalSeries.toLocaleString()}} series — start typing to search`;
    return;
  }}
  noResultsEl.style.display = "none";
  headerEl.classList.toggle("visible", !!query);
  countEl.textContent = `${{filtered.length}} of ${{totalSeries.toLocaleString()}} series`;

  let html = "";
  for (let i = 0; i < filtered.length; i++) {{
    const r = filtered[i];
    let hId, hDesc;
    if (query) {{
      [hId, hDesc] = highlightMatch(query, r.id, r.desc);
    }} else {{
      hId = escHtml(r.id);
      hDesc = escHtml(r.desc);
    }}
    const scoreHtml = query ? `<span class="score">${{r.score}}</span>` : "";
    html += `<li data-i="${{i}}" class="${{i === activeIdx ? "active" : ""}}"><span class="sid">${{hId}}</span><span class="desc">${{hDesc}}</span>${{scoreHtml}}</li>`;
  }}
  resultsEl.innerHTML = html;

  if (activeIdx >= 0 && activeIdx < filtered.length) showDetail(filtered[activeIdx]);
}}

// ── Detail panel ──
function showDetail(item) {{
  document.getElementById("d-id").textContent = item.id;
  document.getElementById("d-title").textContent = item.desc;
  const badge = document.getElementById("d-badge");
  badge.textContent = currentProgram.toUpperCase() + " — " + PROGRAMS[currentProgram];
  badge.style.background = programColors[currentProgram];
  document.getElementById("d-link").href = "https://data.bls.gov/timeseries/" + item.id;
  document.getElementById("d-copy").textContent = "Copy ID";
  document.getElementById("d-copy").classList.remove("copied");
  detailEl.classList.add("visible");
}}

function hideDetail() {{
  detailEl.classList.remove("visible");
}}

function copyId() {{
  const id = document.getElementById("d-id").textContent;
  navigator.clipboard.writeText(id).then(() => {{
    const btn = document.getElementById("d-copy");
    btn.textContent = "Copied!";
    btn.classList.add("copied");
  }});
}}

// ── Keyboard nav ──
searchEl.addEventListener("keydown", (e) => {{
  if (e.key === "ArrowDown") {{
    e.preventDefault();
    if (activeIdx < filtered.length - 1) {{
      activeIdx++;
      updateActive();
    }}
  }} else if (e.key === "ArrowUp") {{
    e.preventDefault();
    if (activeIdx > 0) {{
      activeIdx--;
      updateActive();
    }}
  }} else if (e.key === "Enter") {{
    if (activeIdx >= 0 && activeIdx < filtered.length) {{
      showDetail(filtered[activeIdx]);
    }}
  }} else if (e.key === "Escape") {{
    activeIdx = -1;
    hideDetail();
    updateActive();
  }}
}});

function updateActive() {{
  const items = resultsEl.children;
  for (let i = 0; i < items.length; i++) {{
    items[i].classList.toggle("active", i === activeIdx);
  }}
  if (activeIdx >= 0 && activeIdx < filtered.length) {{
    showDetail(filtered[activeIdx]);
    items[activeIdx]?.scrollIntoView({{ block: "nearest" }});
  }}
}}

// ── Click on row ──
resultsEl.addEventListener("click", (e) => {{
  const li = e.target.closest("li");
  if (!li) return;
  activeIdx = parseInt(li.dataset.i);
  updateActive();
}});

// ── Input ──
searchEl.addEventListener("input", () => {{
  activeIdx = -1;
  hideDetail();
  runSearch();
}});

// ── Init ──
updateSAVisibility();
runSearch();
searchEl.focus();
</script>
</body>
</html>"""

if __name__ == "__main__":
    print("Loading CSVs…")
    data = load_data()
    total = sum(len(v) for v in data.values())
    print(f"Total: {total} series")
    html = build_html(data)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote index.html ({len(html):,} bytes)")
