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
                desc = row["description"].strip()
                # For ln, move a leading parenthesized tag like "(Seas)" or
                # "(Unadj)" to the end so the real description starts at pos 0
                # and ranks correctly by first-word-matches-early.
                if code == "ln" and desc.startswith("("):
                    end = desc.find(")")
                    if end > 0:
                        tag = desc[:end+1]
                        rest = desc[end+1:].lstrip()
                        desc = f"{rest} {tag}" if rest else tag
                rows.append([row["series_id"].strip(), desc])
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
#results li .add-btn {{ flex-shrink: 0; padding: 1px 8px; font-size: 0.78rem; border: 1px solid #ccc; border-radius: 4px; background: #fff; color: #555; cursor: pointer; }}
#results li .add-btn:hover {{ background: #e8f0fe; border-color: #4a90d9; color: #4a90d9; }}
#results li .add-btn.added {{ background: #e8f0fe; border-color: #4a90d9; color: #4a90d9; }}
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
/* Selected series panel */
#selected-panel {{ display: none; background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 14px 18px; margin-top: 14px; }}
#selected-panel.visible {{ display: block; }}
#selected-panel h3 {{ font-size: 0.9rem; font-weight: 600; margin-bottom: 8px; }}
#selected-list {{ list-style: none; margin-bottom: 10px; }}
#selected-list li {{ display: flex; gap: 8px; align-items: baseline; padding: 4px 0; border-bottom: 1px solid #f0f0f0; font-size: 0.85rem; }}
#selected-list li .sel-id {{ font-family: "SF Mono", "Cascadia Code", "Consolas", monospace; font-size: 0.8rem; color: #555; flex-shrink: 0; }}
#selected-list li .sel-desc {{ flex: 1; color: #333; }}
#selected-list li .sel-remove {{ flex-shrink: 0; padding: 0 6px; font-size: 0.8rem; border: none; background: none; color: #c00; cursor: pointer; }}
#selected-list li .sel-remove:hover {{ color: #f00; }}
.selected-actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.selected-actions button {{ padding: 5px 12px; font-size: 0.82rem; border-radius: 5px; cursor: pointer; border: 1px solid #ccc; background: #fff; color: #333; }}
.selected-actions button:hover {{ background: #f5f5f5; }}
.selected-actions .flash {{ color: #2a7; border-color: #2a7; }}

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
  <div id="results-header"><span class="h-sid">Series ID</span><span class="h-desc">Description</span></div>
  <ul id="results"></ul>
  <div id="no-results">No series matched your query.</div>
  <div id="selected-panel">
    <h3>Selected Series (<span id="sel-count">0</span>)</h3>
    <ul id="selected-list"></ul>
    <div class="selected-actions">
      <button onclick="copySelected('ids')">Copy IDs</button>
      <button onclick="copySelected('quoted')">Copy IDs as Quoted List</button>
      <button onclick="copySelected('both')">Copy IDs + Descriptions</button>
      <button onclick="downloadSelected()">Download CSV</button>
      <button onclick="clearSelected()">Clear All</button>
    </div>
  </div>
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
const selected = new Map(); // id -> desc

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
  let runLen = 0;
  for (let ti = startIdx; ti < tLen && ci < pLen; ti++) {{
    if (tLower[ti] === pLower[ci]) {{
      positions.push(ti);
      score += 1;
      if (ti === prevMatch + 1) {{
        runLen++;
        // Reward contiguous runs quadratically: each added char in a run
        // contributes 2*runLen points, so a run of length k adds k*(k+1) total
        score += 2 * runLen;
      }} else {{
        runLen = 0;
      }}
      if (ti === 0 || " _-.,()".includes(text[ti - 1])) score += 5;
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
  if (pLen === 0) return {{ score: 0, positions: [], wholeWord: false, wholeWordIdx: -1 }};

  // Look for whole-word match first
  const wordSep = " _-.,()";
  let wholeWordIdx = -1;
  let searchFrom = 0;
  while (true) {{
    const idx = tLower.indexOf(pLower, searchFrom);
    if (idx < 0) break;
    const before = idx === 0 || wordSep.includes(text[idx - 1]);
    const afterIdx = idx + pLen;
    const after = afterIdx === tLen || wordSep.includes(text[afterIdx]);
    if (before && after) {{ wholeWordIdx = idx; break; }}
    searchFrom = idx + 1;
  }}

  if (wholeWordIdx >= 0) {{
    const positions = [];
    let score = 0;
    for (let i = 0; i < pLen; i++) positions.push(wholeWordIdx + i);
    score += pLen;
    score += pLen * (pLen - 1);
    score += 5;
    if (wholeWordIdx === 0) score += 10;
    score += wholeWordIdx === 0 ? 35 : 20;
    score += 80;
    return {{ score, positions, wholeWord: true, wholeWordIdx }};
  }}

  // Subsequence/partial match fallback
  let best = null;
  for (let start = 0; start <= tLen - pLen; start++) {{
    if (tLower[start] === pLower[0]) {{
      const result = scoreFrom(pLower, tLower, text, start);
      if (result && (!best || result.score > best.score)) best = result;
    }}
  }}
  if (!best) return null;

  const substringIdx = tLower.indexOf(pLower);
  if (substringIdx >= 0) {{
    best.score += substringIdx === 0 ? 35 : 20;
  }}

  return {{ score: best.score, positions: best.positions, wholeWord: false, wholeWordIdx: -1 }};
}}

// Composite scoring with strict level hierarchy. Levels are combined into a
// single number with large multipliers so each tier strictly dominates the
// next. Ranking order:
//   1. Number of whole-word matches (higher is better)
//   2. Position ordering of whole-word matches (earlier + in-order is better)
//   3. Total characters covered by whole-word matches (more is better)
//   4. Greedy/partial match score (higher is better)
//   5. Aggregate preference (more 0's in id + shorter text)
// The zero/brevity tie-breaker is applied at search time (not here) since
// it depends on the series id and not just the description text.
function fuzzyMatch(query, text) {{
  const tokens = query.trim().split(/\\s+/).filter(t => t.length > 0);
  if (tokens.length === 0) return {{ score: 0, positions: [], wholeWordCount: 0, orderBonus: 0, wholeWordChars: 0, partialScore: 0, textLen: text.length }};

  const allPositions = new Set();
  let wholeWordCount = 0;
  let wholeWordChars = 0;
  let partialScore = 0;
  const wwIndices = [];

  for (const token of tokens) {{
    const result = fuzzyMatchToken(token, text);
    if (!result) return null;
    result.positions.forEach(p => allPositions.add(p));
    if (result.wholeWord) {{
      wholeWordCount++;
      wholeWordChars += token.length;
      wwIndices.push(result.wholeWordIdx);
    }} else {{
      wwIndices.push(null);
    }}
    partialScore += result.score;
  }}

  // Level 2: order of whole-word matches.
  // Reward when whole-word matches appear earlier and in the same order as
  // the query tokens. We compute an "orderBonus": larger is better.
  //
  // For each consecutive pair of whole-word matches in the query, if the
  // second match in the text comes after the first, that's +1. Also
  // subtract the average position of whole-word matches (earlier = higher
  // bonus). This handles both sub-requirements of the user's rule #2:
  //   - 'Rent' matches earlier in 'Rent of primary residence' than in
  //     "Owners' equivalent rent"
  //   - 'all items food and energy' keeps tokens in order, favoring
  //     'all items less food and energy' over rearranged variants
  let orderBonus = 0;
  let prevIdx = -1;
  let wwSum = 0;
  let wwN = 0;
  for (const idx of wwIndices) {{
    if (idx === null) continue;
    wwSum += idx;
    wwN++;
    if (prevIdx >= 0 && idx > prevIdx) orderBonus += 1000;
    prevIdx = idx;
  }}
  // Earlier average position → higher bonus (subtract avg position)
  if (wwN > 0) orderBonus -= Math.round(wwSum / wwN);

  return {{
    score: 0, // computed at search time with zero/brevity adjustments
    positions: allPositions,
    wholeWordCount,
    orderBonus,
    wholeWordChars,
    partialScore,
    textLen: text.length,
  }};
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
        // Level 5: aggregate preference — zero count in id + brevity bonus
        let aggregate = 0;
        if (ZERO_BONUS_PROGRAMS.has(currentProgram)) {{
          for (let j = 0; j < s[0].length; j++) {{ if (s[0][j] === "0") aggregate += 30; }}
        }}
        // brevity: shorter text is slightly favored at the aggregate tier
        aggregate += Math.max(0, 200 - m.textLen);
        scored.push({{
          id: s[0], desc: s[1],
          wholeWordCount: m.wholeWordCount,
          orderBonus: m.orderBonus,
          wholeWordChars: m.wholeWordChars,
          partialScore: m.partialScore,
          aggregate,
          // Displayed score: compact summary of tier values (for UI only)
          score: m.wholeWordCount * 1000 + m.wholeWordChars * 10 + m.partialScore,
        }});
      }}
    }}
    // Hierarchical sort: each tier strictly dominates the next.
    scored.sort((a, b) => {{
      if (a.wholeWordCount !== b.wholeWordCount) return b.wholeWordCount - a.wholeWordCount;
      if (a.orderBonus !== b.orderBonus) return b.orderBonus - a.orderBonus;
      if (a.wholeWordChars !== b.wholeWordChars) return b.wholeWordChars - a.wholeWordChars;
      if (a.partialScore !== b.partialScore) return b.partialScore - a.partialScore;
      return b.aggregate - a.aggregate;
    }});
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
    const isAdded = selected.has(r.id);
    const addBtn = `<button class="add-btn${{isAdded ? " added" : ""}}" data-id="${{escHtml(r.id)}}" onclick="toggleSelect(this, event)">${{isAdded ? "Added" : "+ Add"}}</button>`;
    html += `<li data-i="${{i}}" class="${{i === activeIdx ? "active" : ""}}"><span class="sid">${{hId}}</span><span class="desc">${{hDesc}}</span>${{addBtn}}</li>`;
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

// ── Selected series ──
function toggleSelect(btn, e) {{
  e.stopPropagation();
  const id = btn.dataset.id;
  if (selected.has(id)) {{
    selected.delete(id);
    btn.classList.remove("added");
    btn.textContent = "+ Add";
  }} else {{
    const item = filtered.find(r => r.id === id);
    if (item) selected.set(id, item.desc);
    btn.classList.add("added");
    btn.textContent = "Added";
  }}
  renderSelected();
}}

function renderSelected() {{
  const panel = document.getElementById("selected-panel");
  const list = document.getElementById("selected-list");
  document.getElementById("sel-count").textContent = selected.size;
  if (selected.size === 0) {{
    panel.classList.remove("visible");
    return;
  }}
  panel.classList.add("visible");
  let html = "";
  for (const [id, desc] of selected) {{
    html += `<li><span class="sel-id">${{escHtml(id)}}</span><span class="sel-desc">${{escHtml(desc)}}</span><button class="sel-remove" onclick="removeSel('${{id}}')">&times;</button></li>`;
  }}
  list.innerHTML = html;
}}

function removeSel(id) {{
  selected.delete(id);
  renderSelected();
  // Update add button in results if visible
  const btn = resultsEl.querySelector(`button[data-id="${{id}}"]`);
  if (btn) {{ btn.classList.remove("added"); btn.textContent = "+ Add"; }}
}}

function clearSelected() {{
  selected.clear();
  renderSelected();
  resultsEl.querySelectorAll(".add-btn.added").forEach(btn => {{
    btn.classList.remove("added");
    btn.textContent = "+ Add";
  }});
}}

function copySelected(mode) {{
  let text;
  if (mode === "ids") {{
    text = [...selected.keys()].join("\\n");
  }} else if (mode === "quoted") {{
    text = "[" + [...selected.keys()].map(id => `'${{id}}'`).join(", ") + "]";
  }} else {{
    text = [...selected].map(([id, desc]) => `${{id}}\\t${{desc}}`).join("\\n");
  }}
  navigator.clipboard.writeText(text).then(() => {{
    const btns = document.querySelectorAll(".selected-actions button");
    const btn = mode === "ids" ? btns[0] : mode === "quoted" ? btns[1] : btns[2];
    const orig = btn.textContent;
    btn.textContent = "Copied!";
    btn.classList.add("flash");
    setTimeout(() => {{ btn.textContent = orig; btn.classList.remove("flash"); }}, 1500);
  }});
}}

function downloadSelected() {{
  let csv = "series_id,description\\n";
  for (const [id, desc] of selected) {{
    csv += `"${{id}}","${{desc.replace(/"/g, '""')}}"\\n`;
  }}
  const blob = new Blob([csv], {{ type: "text/csv" }});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "bls_series.csv";
  a.click();
  URL.revokeObjectURL(a.href);
}}

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
