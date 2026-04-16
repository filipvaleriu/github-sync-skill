# HTML Report Template Reference

When the bundled Python script doesn't fit the data format, generate HTML directly following these guidelines:

## Required layout

The report uses a CSS Grid layout with main content + right sidebar:

```css
.container {
  max-width: 1440px; margin: 0 auto; padding: 32px 24px;
  display: grid; grid-template-columns: 1fr 300px; gap: 24px;
}
.main-content { min-width: 0; }
```

### Sticky navigation bar

Always include a sticky nav at the top of `.container`, spanning both columns:

```css
.nav-wrapper {
  position: sticky; top: 0; z-index: 100; background: var(--bg);
  padding: 12px 24px 0; grid-column: 1 / -1;
}
.nav-tabs {
  display: flex; gap: 8px; flex-wrap: wrap;
  padding-bottom: 16px; border-bottom: 2px solid var(--gray-light);
}
.nav-tab {
  padding: 8px 18px; border-radius: 20px; font-size: 0.84rem; font-weight: 500;
  cursor: pointer; border: 1px solid var(--gray-light); background: white;
  color: var(--text-secondary); transition: all 0.2s; text-decoration: none;
}
.nav-tab:hover, .nav-tab.active { background: var(--primary-color); color: white; border-color: var(--primary-color); }
```

Generate nav links for each section (Sumar, Metoda, 1, 2, 3... etc.) with `href="#sectionId"`.

### Responsive breakpoints

```css
@media (max-width: 900px) {
  .container { grid-template-columns: 1fr; }
  .sidebar { position: static; max-height: none; }
  .nav-wrapper { grid-column: 1; }
}
@media print {
  .container { grid-template-columns: 1fr; }
  .nav-wrapper, .nav-tabs { display: none; }
  .sidebar { display: none; }
}
```

## Required sections (main content)

1. **Header**: gradient background, title, subtitle, period metadata
2. **Executive summary**: KPI cards with total conversions, contacted conversions, truly incremental (range), organic
3. **Methodology**: explain counterfactual, show formula, document both baselines with their labels and rates
4. **Per-group table**: group name, leads, conversions, rate, expected @baseline A, expected @baseline B, increment range, interpretation
5. **Stacked bar chart**: Chart.js, incremental (purple) + organic (gray) per group
6. **Rate comparison chart**: bar chart with rates per group, color-coded (purple=positive lift, gray=below baseline, blue=baseline)
7. **Business-specific answers**: answer whatever the stakeholder asked (e.g., "how many intervention-attributed conversions would have been organic anyway?")
8. **Limitations**: table with severity badges

## Right sidebar — methodology references

The sidebar is sticky (`position: sticky; top: 80px;`) and contains academic/industry references organized by method category. It scrolls independently from the main content.

```css
.sidebar {
  position: sticky; top: 80px; align-self: start;
  max-height: calc(100vh - 100px); overflow-y: auto; scrollbar-width: thin;
}
.sidebar-card {
  background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06); border-top: 3px solid var(--blue);
}
.sidebar-card h3 { font-size: 0.95rem; color: var(--blue); margin-bottom: 12px; }
.ref-item { margin-bottom: 14px; padding-bottom: 14px; border-bottom: 1px solid #F0F0F0; }
.ref-item:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
.ref-item a { color: var(--blue); text-decoration: none; font-weight: 600; font-size: 0.85rem; display: block; margin-bottom: 3px; }
.ref-item a:hover { text-decoration: underline; }
.ref-item .ref-meta { font-size: 0.78rem; color: var(--text-secondary); }
.ref-item .ref-desc { font-size: 0.8rem; color: var(--text); margin-top: 3px; }
.confidence-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; }
.confidence-canonical { background: #E8F5E9; color: var(--green); }
.confidence-high { background: #E3F2FD; color: var(--blue); }
.confidence-industry { background: var(--orange-pale, #FFF3E8); color: var(--orange, #FF6B00); }
```

### Reference cards (always include these 6 cards)

**Card 1 — Fundament Teoretic**

| Title | Author | Badge | Description |
|---|---|---|---|
| [Rubin Causal Model](https://en.wikipedia.org/wiki/Rubin_causal_model) | Potential Outcomes Framework | Canonic | Fundamentul tuturor metodelor de incrementalitate: Y(1) vs Y(0) |
| [Mostly Harmless Econometrics](https://press.princeton.edu/books/paperback/9780691120355/mostly-harmless-econometrics) | Angrist & Pischke, 2008 | Canonic | Referinta academica pentru DiD si inferenta cauzala din date observationale |
| [Experimental and Quasi-Experimental Designs](https://books.google.com/books/about/Experimental_and_Quasi_experimental_Desi.html?id=o7jaAAAAMAAJ) | Shadish, Cook & Campbell, 2002 | Canonic | Standard pentru designuri quasi-experimentale fara randomizare |

**Card 2 — Counterfactual / DiD**

| Title | Author | Badge | Description |
|---|---|---|---|
| [Causal Inference: The Mixtape — DiD](https://mixtape.scunning.com/09-difference_in_differences) | Cunningham, 2021 | Academic | Explicatie accesibila a DiD cu exemple practice |
| [DiD with Multiple Time Periods](https://arxiv.org/abs/1803.09015) | Callaway & Sant'Anna, 2021 | Academic | Extensie pentru perioade multiple si tratament escalonat |

**Card 3 — Lift / Incrementality Testing**

| Title | Author | Badge | Description |
|---|---|---|---|
| [Google: Incrementality Testing](https://business.google.com/us/think/measurement/incrementality-testing/) | Google, 2024 | Standard Industrie | Ghid Google pentru masurarea incrementalitatii campaniilor marketing |
| [Measuring Incrementality on Facebook](https://arxiv.org/abs/1806.02588) | Liu, 2018 | Academic | Paper Meta/Facebook despre design experimente incrementalitate in advertising |
| [Robust Causal Inference for iROAS](https://arxiv.org/abs/1908.02922) | Naik et al., 2019 | Academic | Inferenta cauzala robusta pentru ROAS incremental |

**Card 4 — Intent-to-Treat (ITT)**

| Title | Author | Badge | Description |
|---|---|---|---|
| [Incrementality Tests 101: ITT, PSA, Ghost Ads](https://www.remerge.io/blog-post/incrementality-tests-101-intent-to-treat-psa-ghost-ads-and-ghost-bids) | Remerge, 2024 | Standard Industrie | Comparatie metode: ITT, PSA, Ghost Ads |
| [Quasi-Experimental Designs for Causal Inference](https://pmc.ncbi.nlm.nih.gov/articles/PMC6086368/) | NIH/PMC | Academic | Review designuri quasi-experimentale fara randomizare |

**Card 5 — Dual Control Groups**

| Title | Author | Badge | Description |
|---|---|---|---|
| [Universal Control Groups in Marketing](https://zyabkina.com/universal-control-groups-and-advanced-experiments-in-marketing/) | Zyabkina, 2024 | Standard Industrie | Folosirea a doua grupuri de control si prezentarea ca range |
| [Microsoft: Incrementality Toolkit](https://learn.microsoft.com/en-us/xandr/data-science-toolkit/incrementality) | Microsoft Learn, 2024 | Standard Industrie | Toolkit Microsoft pentru incrementalitate in advertising digital |

**Card 6 — "Ce metode am aplicat noi" (accent color, not blue)**

Use intervention accent color for border-top. Content summarizes which methods from above were actually applied in this specific analysis (counterfactual cu dual baseline, lift analysis per grup, ITT, quasi-experimental). End with the main limitation (e.g., selection bias).

## Styling conventions

- Primary color for incremental: `#7B1FA2` (purple) / `#AB47BC` (light purple)
- Organic/baseline: `#E0E0E0` (gray)
- Positive lift: `#2E7D32` (green)
- Below baseline: `#9E9E9E` (gray)
- Not contacted baseline: `#42A5F5` (blue)
- Use `font-variant-numeric: tabular-nums` for number columns
- KPI cards: 200px min width, grid layout
- Charts: Chart.js 4.x from cdnjs.cloudflare.com
- Responsive: stack on mobile, print-friendly

## Chart.js patterns

Stacked bar for increment decomposition:
```javascript
datasets: [
  { label: 'Increment @X%', data: [...], backgroundColor: '#AB47BC', stacked },
  { label: 'Increment extra @Y%', data: [...], backgroundColor: '#CE93D8', stacked },
  { label: 'Organic', data: [...], backgroundColor: '#E0E0E0', stacked }
]
```

Rate comparison (non-stacked):
```javascript
backgroundColor: rates.map(r => r > baseline ? '#AB47BC' : '#9E9E9E')
// Last bar (baseline) always '#42A5F5'
```
