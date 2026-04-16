#!/usr/bin/env python3
"""
Incrementality Analysis Report Generator

Takes a JSON input file describing intervention groups and generates
an interactive HTML report with Chart.js visualizations.

Usage:
  python incrementality_report.py --data input.json --output report.html
  python incrementality_report.py --data input.json --output report.html --title "My Analysis" --period "Q1 2026"

Input JSON format:
{
  "intervention_name": "Sales Team",
  "period": "Nov 2025 - Mar 2026",
  "total_eligible": 45182,
  "total_conversions": 3899,
  "groups": [
    {
      "name": "Accepted offer",
      "leads": 560,
      "conversions": 363,
      "is_baseline_negative": false,
      "is_not_contacted": false,
      "directly_attributed_subset": 339
    },
    ...
  ]
}

Groups should be tagged:
  - is_baseline_negative=true for control groups (failed intervention: NR, wrong number, refused)
  - is_not_contacted=true for the non-contacted baseline
  - directly_attributed_subset (optional): subset of conversions with direct attribution (e.g., specific invoice series)
"""

import json
import argparse
import math
import sys
from pathlib import Path


def compute_incrementality(data):
    """Core incrementality computation. Returns enriched data with all calculations."""
    groups = data["groups"]
    total_eligible = data["total_eligible"]
    total_conversions = data["total_conversions"]
    intervention = data.get("intervention_name", "Intervention")

    # Separate groups
    baseline_neg_groups = [g for g in groups if g.get("is_baseline_negative")]
    not_contacted = [g for g in groups if g.get("is_not_contacted")]
    contacted = [g for g in groups if not g.get("is_not_contacted")]

    # Compute baselines
    neg_leads = sum(g["leads"] for g in baseline_neg_groups)
    neg_conv = sum(g["conversions"] for g in baseline_neg_groups)
    baseline_a_rate = neg_conv / neg_leads if neg_leads > 0 else 0

    nc_leads = sum(g["leads"] for g in not_contacted)
    nc_conv = sum(g["conversions"] for g in not_contacted)
    baseline_b_rate = nc_conv / nc_leads if nc_leads > 0 else 0

    # Per-group incrementality
    contacted_leads_total = sum(g["leads"] for g in contacted)
    contacted_conv_total = sum(g["conversions"] for g in contacted)

    results = []
    total_increment_a = 0
    total_increment_b = 0
    total_increment_a_net = 0
    total_increment_b_net = 0
    total_expected_a = 0
    total_expected_b = 0

    for g in contacted:
        leads = g["leads"]
        conv = g["conversions"]
        rate = conv / leads if leads > 0 else 0

        expected_a = round(leads * baseline_a_rate)
        expected_b = round(leads * baseline_b_rate)
        raw_inc_a = conv - expected_a
        raw_inc_b = conv - expected_b
        inc_a = max(0, raw_inc_a)
        inc_b = max(0, raw_inc_b)

        total_increment_a += inc_a
        total_increment_b += inc_b
        total_increment_a_net += raw_inc_a
        total_increment_b_net += raw_inc_b
        total_expected_a += expected_a
        total_expected_b += expected_b

        # Proportion incremental (for directly_attributed_subset)
        prop_inc_a = (conv - expected_a) / conv if conv > 0 and raw_inc_a > 0 else 0
        prop_inc_b = (conv - expected_b) / conv if conv > 0 and raw_inc_b > 0 else 0
        da_subset = g.get("directly_attributed_subset", 0)
        da_inc_a = round(da_subset * prop_inc_a) if da_subset and raw_inc_a > 0 else 0
        da_inc_b = round(da_subset * prop_inc_b) if da_subset and raw_inc_b > 0 else 0

        interp = ""
        if raw_inc_a > 0 and raw_inc_b > 0:
            interp = f"{intervention} a contribuit real"
        elif raw_inc_a <= 0 and raw_inc_b <= 0:
            interp = "Sub baseline — organic"
        else:
            interp = "Marginal — depinde de baseline"

        results.append({
            **g,
            "rate": rate,
            "expected_a": expected_a,
            "expected_b": expected_b,
            "increment_a": inc_a,
            "increment_b": inc_b,
            "raw_increment_a": raw_inc_a,
            "raw_increment_b": raw_inc_b,
            "proportion_incremental_a": prop_inc_a,
            "proportion_incremental_b": prop_inc_b,
            "da_incremental_a": da_inc_a,
            "da_incremental_b": da_inc_b,
            "interpretation": interp,
        })

    # Sort: positive increments first (by inc_a desc), then negatives
    results.sort(key=lambda x: -x["increment_a"])

    return {
        "intervention": intervention,
        "period": data.get("period", ""),
        "title": data.get("title", f"Incrementality Analysis — {intervention}"),
        "total_eligible": total_eligible,
        "total_conversions": total_conversions,
        "contacted_leads": contacted_leads_total,
        "contacted_conversions": contacted_conv_total,
        "baseline_a_rate": baseline_a_rate,
        "baseline_a_label": f"Failed intervention ({neg_leads:,} leads, {baseline_a_rate:.1%})",
        "baseline_b_rate": baseline_b_rate,
        "baseline_b_label": f"Not contacted ({nc_leads:,} leads, {baseline_b_rate:.1%})",
        "total_increment_min": min(total_increment_a_net, total_increment_b_net),
        "total_increment_max": max(total_increment_a_net, total_increment_b_net),
        "total_increment_pos_min": min(total_increment_a, total_increment_b),
        "total_increment_pos_max": max(total_increment_a, total_increment_b),
        "total_expected_min": min(total_expected_a, total_expected_b),
        "total_expected_max": max(total_expected_a, total_expected_b),
        "groups": results,
        "not_contacted_leads": nc_leads,
        "not_contacted_conv": nc_conv,
        "not_contacted_rate": baseline_b_rate,
    }


def generate_html(calc, output_path):
    """Generate interactive HTML report from computed results."""
    g = calc["groups"]
    intervention = calc["intervention"]
    period = calc["period"]

    # Build chart data
    group_labels = [gr["name"] for gr in g]
    inc_a_data = [gr["increment_a"] for gr in g]
    inc_extra = [max(0, gr["increment_b"] - gr["increment_a"]) for gr in g]
    organic_data = [gr["expected_a"] for gr in g]

    # Rate comparison chart
    rate_labels = [gr["name"] for gr in g] + ["Not contacted (baseline)"]
    rate_data = [round(gr["rate"] * 100, 1) for gr in g] + [round(calc["baseline_b_rate"] * 100, 1)]

    # Colors: positive increment = purple, negative = gray
    rate_colors = []
    for gr in g:
        if gr["raw_increment_a"] > 0:
            rate_colors.append("'#AB47BC'")
        elif gr["raw_increment_a"] == 0:
            rate_colors.append("'#FFC107'")
        else:
            rate_colors.append("'#9E9E9E'")
    rate_colors.append("'#42A5F5'")  # baseline

    # Build per-group table rows
    table_rows = ""
    for gr in g:
        inc_min = min(gr["increment_a"], gr["increment_b"])
        inc_max = max(gr["increment_a"], gr["increment_b"])
        css = ""
        inc_class = ""
        if gr["raw_increment_a"] > 0 and gr["raw_increment_b"] > 0:
            css = "background:#F3E5F5;"
            inc_class = "positive"
        elif gr["raw_increment_a"] <= 0 and gr["raw_increment_b"] <= 0:
            inc_class = "negative"

        # Directly attributed subset info
        da_info = ""
        if gr.get("directly_attributed_subset"):
            da_min = min(gr["da_incremental_a"], gr["da_incremental_b"])
            da_max = max(gr["da_incremental_a"], gr["da_incremental_b"])
            da_total = gr["directly_attributed_subset"]
            organic_min = da_total - da_max
            organic_max = da_total - da_min
            da_info = f"<br><small style='color:#757575'>Din {da_total} direct atribuite: {da_min}–{da_max} incremental, {organic_min}–{organic_max} organic</small>"

        table_rows += f"""
        <tr style="{css}">
          <td>{gr['name']}{da_info}</td>
          <td class="num">{gr['leads']:,}</td>
          <td class="num">{gr['conversions']:,}</td>
          <td class="num">{gr['rate']:.1%}</td>
          <td class="num">{gr['expected_a']:,}</td>
          <td class="num">{gr['expected_b']:,}</td>
          <td class="num {inc_class}">{'+' if inc_min > 0 else ''}{inc_min:,} — {'+' if inc_max > 0 else ''}{inc_max:,}</td>
          <td>{gr['interpretation']}</td>
        </tr>"""

    inc_min = calc["total_increment_min"]
    inc_max = calc["total_increment_max"]
    inc_pos_min = calc["total_increment_pos_min"]
    inc_pos_max = calc["total_increment_pos_max"]
    exp_min = calc["total_expected_min"]
    exp_max = calc["total_expected_max"]
    cc = calc["contacted_conversions"]
    cl = calc["contacted_leads"]
    pct_min = inc_min / calc["total_conversions"] * 100 if calc["total_conversions"] else 0
    pct_max = inc_max / calc["total_conversions"] * 100 if calc["total_conversions"] else 0
    inc_rate_min = inc_min / cl * 100 if cl else 0
    inc_rate_max = inc_max / cl * 100 if cl else 0

    html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{calc['title']}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root {{
    --purple: #7B1FA2; --purple-light: #AB47BC; --purple-pale: #F3E5F5;
    --orange: #FF6B00; --orange-pale: #FFF3E8;
    --green: #2E7D32; --blue: #1565C0; --blue-light: #42A5F5;
    --gray: #616161; --gray-light: #E0E0E0; --red: #C62828;
    --bg: #FAFAFA; --text: #212121; --text-secondary: #757575;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', -apple-system, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
  .header {{
    background: linear-gradient(135deg, var(--purple) 0%, var(--purple-light) 100%);
    color: white; padding: 48px 40px 36px; position: relative; overflow: hidden;
  }}
  .header::after {{ content: ''; position: absolute; top: -50%; right: -10%; width: 400px; height: 400px; background: rgba(255,255,255,0.08); border-radius: 50%; }}
  .header h1 {{ font-size: 2rem; font-weight: 700; margin-bottom: 8px; position: relative; z-index: 1; }}
  .header .subtitle {{ font-size: 1.05rem; opacity: 0.92; position: relative; z-index: 1; }}
  .header .meta {{ margin-top: 16px; font-size: 0.85rem; opacity: 0.75; position: relative; z-index: 1; }}
  .container {{ max-width: 1440px; margin: 0 auto; padding: 32px 24px; display: grid; grid-template-columns: 1fr 300px; gap: 24px; }}
  .main-content {{ min-width: 0; }}
  .nav-wrapper {{ position: sticky; top: 0; z-index: 100; background: var(--bg); padding: 12px 24px 0; grid-column: 1 / -1; }}
  .nav-tabs {{ display: flex; gap: 8px; flex-wrap: wrap; padding-bottom: 16px; border-bottom: 2px solid var(--gray-light); }}
  .nav-tab {{ padding: 8px 18px; border-radius: 20px; font-size: 0.84rem; font-weight: 500; cursor: pointer; border: 1px solid var(--gray-light); background: white; color: var(--text-secondary); transition: all 0.2s; text-decoration: none; }}
  .nav-tab:hover, .nav-tab.active {{ background: var(--purple); color: white; border-color: var(--purple); }}
  .sidebar {{ position: sticky; top: 80px; align-self: start; max-height: calc(100vh - 100px); overflow-y: auto; scrollbar-width: thin; }}
  .sidebar-card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); border-top: 3px solid var(--blue-light); }}
  .sidebar-card h3 {{ font-size: 0.95rem; color: var(--blue); margin-bottom: 12px; }}
  .ref-item {{ margin-bottom: 14px; padding-bottom: 14px; border-bottom: 1px solid #F0F0F0; }}
  .ref-item:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
  .ref-item a {{ color: var(--blue); text-decoration: none; font-weight: 600; font-size: 0.85rem; display: block; margin-bottom: 3px; }}
  .ref-item a:hover {{ text-decoration: underline; }}
  .ref-item .ref-meta {{ font-size: 0.78rem; color: var(--text-secondary); }}
  .ref-item .ref-desc {{ font-size: 0.8rem; color: var(--text); margin-top: 3px; }}
  .confidence-badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; }}
  .confidence-canonical {{ background: #E8F5E9; color: var(--green); }}
  .confidence-high {{ background: #E3F2FD; color: var(--blue); }}
  .confidence-industry {{ background: #FFF3E8; color: #FF6B00; }}
  .exec-summary {{ background: white; border-radius: 12px; padding: 32px; margin-bottom: 32px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); border-left: 5px solid var(--purple); }}
  .exec-summary h2 {{ font-size: 1.3rem; color: var(--purple); margin-bottom: 16px; }}
  .kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 24px 0; }}
  .kpi-card {{ border-radius: 10px; padding: 20px; text-align: center; }}
  .kpi-card .value {{ font-size: 2rem; font-weight: 700; }}
  .kpi-card .label {{ font-size: 0.85rem; color: var(--text-secondary); margin-top: 4px; }}
  .section {{ background: white; border-radius: 12px; padding: 32px; margin-bottom: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
  .section-number {{ display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; background: var(--purple); color: white; border-radius: 50%; font-weight: 700; margin-right: 12px; }}
  .section h2 {{ display: flex; align-items: center; font-size: 1.25rem; margin-bottom: 20px; }}
  .chart-container-wide {{ position: relative; max-width: 750px; margin: 24px auto; }}
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 0.92rem; }}
  th {{ background: #F5F5F5; padding: 10px 14px; text-align: left; font-weight: 600; border-bottom: 2px solid var(--gray-light); white-space: nowrap; }}
  td {{ padding: 10px 14px; border-bottom: 1px solid #EEE; }}
  tr:hover {{ background: #FAFAFA; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .positive {{ color: var(--green); font-weight: 600; }}
  .negative {{ color: var(--gray); }}
  .callout {{ border-radius: 8px; padding: 16px 20px; margin: 16px 0; font-size: 0.92rem; line-height: 1.5; }}
  .callout-purple {{ background: var(--purple-pale); border-left: 4px solid var(--purple); }}
  .callout-green {{ background: #E8F5E9; border-left: 4px solid var(--green); }}
  .callout-blue {{ background: #E3F2FD; border-left: 4px solid var(--blue); }}
  .callout-gray {{ background: #F5F5F5; border-left: 4px solid #9E9E9E; }}
  .callout strong {{ color: var(--text); }}
  .formula {{ font-family: 'Consolas', monospace; background: #F5F5F5; padding: 12px 16px; border-radius: 6px; margin: 12px 0; font-size: 0.9rem; border-left: 3px solid var(--blue); }}
  .method-box {{ background: #FFFDE7; border: 2px solid #FBC02D; border-radius: 10px; padding: 20px; margin: 20px 0; }}
  .method-box h4 {{ color: #F57F17; margin-bottom: 8px; }}
  p {{ margin-bottom: 12px; }}
  .footer {{ text-align: center; padding: 24px; font-size: 0.8rem; color: var(--text-secondary); border-top: 1px solid var(--gray-light); margin-top: 16px; }}
  @media (max-width: 900px) {{ .container {{ grid-template-columns: 1fr; }} .sidebar {{ position: static; max-height: none; }} .nav-wrapper {{ grid-column: 1; }} }}
  @media (max-width: 700px) {{ .header {{ padding: 32px 20px; }} .header h1 {{ font-size: 1.5rem; }} .container {{ padding: 20px 12px; }} .kpi-row {{ grid-template-columns: repeat(2, 1fr); }} }}
  @media print {{ .container {{ grid-template-columns: 1fr; }} .section {{ break-inside: avoid; box-shadow: none; border: 1px solid #ddd; }} .nav-wrapper, .nav-tabs {{ display: none; }} .sidebar {{ display: none; }} }}
</style>
</head>
<body>
<div class="header">
  <h1>{calc['title']}</h1>
  <div class="subtitle">Analiza de incrementalitate: cat din conversii e truly incremental vs ce s-ar fi intamplat oricum?</div>
  <div class="meta">{period}</div>
</div>
<div class="container">

  <div class="nav-wrapper">
    <div class="nav-tabs">
      <a class="nav-tab" href="#exec-summary">Sumar</a>
      <a class="nav-tab" href="#section-method">Metoda</a>
      <a class="nav-tab" href="#section-increment">Incrementalitate</a>
      <a class="nav-tab" href="#section-rates">Rate conversie</a>
    </div>
  </div>

  <div class="main-content">

  <div class="exec-summary" id="exec-summary">
    <h2>Sumar Executiv</h2>
    <p>Din totalul de <strong>{calc['total_conversions']:,}</strong> conversii, {intervention} a contactat lead-uri care au generat <strong>{cc:,}</strong> conversii. Aplicand metoda counterfactuala, estimam ca <strong>{inc_min:,} — {inc_max:,} conversii sunt truly incrementale</strong> (aduse NET de {intervention}).</p>
    <div class="kpi-row">
      <div class="kpi-card" style="background:var(--purple-pale);">
        <div class="value" style="color:var(--purple);">{calc['total_conversions']:,}</div>
        <div class="label">Conversii totale</div>
      </div>
      <div class="kpi-card" style="background:var(--orange-pale);">
        <div class="value" style="color:var(--orange);">{cc:,}</div>
        <div class="label">De la contactati {intervention}</div>
      </div>
      <div class="kpi-card" style="background:var(--purple-pale);">
        <div class="value" style="color:var(--purple);">{inc_min:,} — {inc_max:,}</div>
        <div class="label">Truly incremental<br>({pct_min:.1f}% — {pct_max:.1f}%)</div>
      </div>
      <div class="kpi-card" style="background:#E8F5E9;">
        <div class="value" style="color:var(--green);">{exp_min:,} — {exp_max:,}</div>
        <div class="label">Ar fi convertit oricum</div>
      </div>
    </div>
  </div>

  <div class="section" id="section-method">
    <h2><span class="section-number">1</span> Metoda</h2>
    <div class="method-box">
      <h4>Principiul counterfactual</h4>
      <p>Pentru fiecare grup contactat, comparam rata reala cu o rata baseline. Diferenta = increment.</p>
      <div class="formula">Increment = Conversii reale - (Nr. leads x Rata baseline)</div>
    </div>
    <p><strong>Baseline A (conservator):</strong> {calc['baseline_a_label']}</p>
    <p><strong>Baseline B (alternativ):</strong> {calc['baseline_b_label']}</p>
  </div>

  <div class="section" id="section-increment">
    <h2><span class="section-number">2</span> Incrementalitate per Grup</h2>
    <div class="chart-container-wide"><canvas id="chartIncrement"></canvas></div>
    <table>
      <thead>
        <tr>
          <th>Grup</th><th class="num">Leads</th><th class="num">Conv.</th><th class="num">Rata</th>
          <th class="num">Asteptat @{calc['baseline_a_rate']:.1%}</th>
          <th class="num">Asteptat @{calc['baseline_b_rate']:.1%}</th>
          <th class="num">Increment (range)</th><th>Interpretare</th>
        </tr>
      </thead>
      <tbody>{table_rows}</tbody>
      <tfoot>
        <tr style="font-weight:700; border-top:3px solid var(--purple);">
          <td>TOTAL CONTACTAT</td><td class="num">{cl:,}</td><td class="num">{cc:,}</td>
          <td class="num">{cc/cl:.1%}</td>
          <td class="num">{sum(gr['expected_a'] for gr in g):,}</td>
          <td class="num">{sum(gr['expected_b'] for gr in g):,}</td>
          <td class="num" style="color:var(--purple); font-size:1.05rem;">{inc_min:,} — {inc_max:,} (net)</td>
          <td></td>
        </tr>
      </tfoot>
    </table>
    <div class="callout callout-purple">
      <strong>Concluzie:</strong> Din {cc:,} conversii de la contactati, <strong>{exp_min:,}–{exp_max:,} ar fi existat oricum</strong>. {intervention} aduce NET <strong>{inc_min:,}–{inc_max:,} conversii truly incrementale</strong>.
    </div>
  </div>

  <div class="section" id="section-rates">
    <h2><span class="section-number">3</span> Rate de Conversie per Grup</h2>
    <div class="chart-container-wide"><canvas id="chartRates"></canvas></div>
    <div class="callout callout-blue">
      <strong>Citire:</strong> Grupurile cu rata peste baseline au fost influentate de {intervention}. Grupurile cu rata sub baseline au convertit organic — {intervention} nu a adus valoare acolo.
    </div>
  </div>

  </div><!-- end main-content -->

  <div class="sidebar">

    <div class="sidebar-card">
      <h3>Fundament Teoretic</h3>
      <div class="ref-item">
        <a href="https://en.wikipedia.org/wiki/Rubin_causal_model" target="_blank">Rubin Causal Model</a>
        <div class="ref-meta">Potential Outcomes Framework <span class="confidence-badge confidence-canonical">Canonic</span></div>
        <div class="ref-desc">Fundamentul teoretic al tuturor metodelor de incrementalitate: compararea rezultatelor potentiale Y(1) vs Y(0).</div>
      </div>
      <div class="ref-item">
        <a href="https://press.princeton.edu/books/paperback/9780691120355/mostly-harmless-econometrics" target="_blank">Mostly Harmless Econometrics</a>
        <div class="ref-meta">Angrist & Pischke, 2008 <span class="confidence-badge confidence-canonical">Canonic</span></div>
        <div class="ref-desc">Referinta academica principala pentru DiD si inferenta cauzala din date observationale.</div>
      </div>
      <div class="ref-item">
        <a href="https://books.google.com/books/about/Experimental_and_Quasi_experimental_Desi.html?id=o7jaAAAAMAAJ" target="_blank">Experimental and Quasi-Experimental Designs</a>
        <div class="ref-meta">Shadish, Cook & Campbell, 2002 <span class="confidence-badge confidence-canonical">Canonic</span></div>
        <div class="ref-desc">Standard pentru designuri quasi-experimentale cand randomizarea nu e posibila.</div>
      </div>
    </div>

    <div class="sidebar-card">
      <h3>Metoda: Counterfactual / DiD</h3>
      <div class="ref-item">
        <a href="https://mixtape.scunning.com/09-difference_in_differences" target="_blank">Causal Inference: The Mixtape — DiD</a>
        <div class="ref-meta">Cunningham, 2021 <span class="confidence-badge confidence-high">Academic</span></div>
        <div class="ref-desc">Explicatie accesibila a metodei Difference-in-Differences cu exemple practice.</div>
      </div>
      <div class="ref-item">
        <a href="https://arxiv.org/abs/1803.09015" target="_blank">DiD with Multiple Time Periods</a>
        <div class="ref-meta">Callaway & Sant'Anna, 2021 <span class="confidence-badge confidence-high">Academic</span></div>
        <div class="ref-desc">Extensie pentru perioade multiple si tratament escalonat.</div>
      </div>
    </div>

    <div class="sidebar-card">
      <h3>Metoda: Lift / Incrementality Testing</h3>
      <div class="ref-item">
        <a href="https://business.google.com/us/think/measurement/incrementality-testing/" target="_blank">Google: Incrementality Testing</a>
        <div class="ref-meta">Google, 2024 <span class="confidence-badge confidence-industry">Standard Industrie</span></div>
        <div class="ref-desc">Ghid Google pentru masurarea incrementalitatii campaniilor de marketing.</div>
      </div>
      <div class="ref-item">
        <a href="https://arxiv.org/abs/1806.02588" target="_blank">Measuring Incrementality on Facebook</a>
        <div class="ref-meta">Liu, 2018 <span class="confidence-badge confidence-high">Academic</span></div>
        <div class="ref-desc">Paper Meta/Facebook despre designul experimentelor de incrementalitate in advertising.</div>
      </div>
      <div class="ref-item">
        <a href="https://arxiv.org/abs/1908.02922" target="_blank">Robust Causal Inference for iROAS</a>
        <div class="ref-meta">Naik et al., 2019 <span class="confidence-badge confidence-high">Academic</span></div>
        <div class="ref-desc">Inferenta cauzala robusta pentru Return on Ad Spend incremental.</div>
      </div>
    </div>

    <div class="sidebar-card">
      <h3>Metoda: Intent-to-Treat (ITT)</h3>
      <div class="ref-item">
        <a href="https://www.remerge.io/blog-post/incrementality-tests-101-intent-to-treat-psa-ghost-ads-and-ghost-bids" target="_blank">Incrementality Tests 101: ITT, PSA, Ghost Ads</a>
        <div class="ref-meta">Remerge, 2024 <span class="confidence-badge confidence-industry">Standard Industrie</span></div>
        <div class="ref-desc">Comparatie metode: ITT, PSA, Ghost Ads. ITT = metoda folosita de noi.</div>
      </div>
      <div class="ref-item">
        <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC6086368/" target="_blank">Quasi-Experimental Designs for Causal Inference</a>
        <div class="ref-meta">NIH/PMC <span class="confidence-badge confidence-high">Academic</span></div>
        <div class="ref-desc">Review academic al designurilor quasi-experimentale in absenta randomizarii.</div>
      </div>
    </div>

    <div class="sidebar-card">
      <h3>Metoda: Dual Control Groups</h3>
      <div class="ref-item">
        <a href="https://zyabkina.com/universal-control-groups-and-advanced-experiments-in-marketing/" target="_blank">Universal Control Groups in Marketing</a>
        <div class="ref-meta">Zyabkina, 2024 <span class="confidence-badge confidence-industry">Standard Industrie</span></div>
        <div class="ref-desc">Fundamentarea folosirii a doua grupuri de control si prezentarea ca range.</div>
      </div>
      <div class="ref-item">
        <a href="https://learn.microsoft.com/en-us/xandr/data-science-toolkit/incrementality" target="_blank">Microsoft: Incrementality Toolkit</a>
        <div class="ref-meta">Microsoft Learn, 2024 <span class="confidence-badge confidence-industry">Standard Industrie</span></div>
        <div class="ref-desc">Toolkit Microsoft pentru masurarea incrementalitatii in advertising digital.</div>
      </div>
    </div>

    <div class="sidebar-card" style="border-top-color: var(--purple);">
      <h3 style="color: var(--purple);">Ce metode am aplicat</h3>
      <div style="font-size:0.82rem; line-height:1.5;">
        <p><strong>1. Counterfactual cu dual baseline</strong> — comparam rata de conversie a fiecarui grup contactat cu doua baseline-uri (interventie esuata si necontactati), prezentam range.</p>
        <p><strong>2. Lift analysis per grup</strong> — masuram lift-ul (pp) pentru fiecare subgrup. Lift pozitiv = contributie reala, lift negativ = organic.</p>
        <p><strong>3. Intent-to-Treat (ITT)</strong> — folosim grupul de interventie esuata ca grup de control natural (aceleasi criterii selectie, zero interventie reala).</p>
        <p><strong>4. Quasi-experimental</strong> — fara randomizare, comparam cu cel mai apropiat contrafactual disponibil.</p>
        <p style="margin-top:8px; color:var(--text-secondary); font-size:0.78rem;"><em>Limitare principala: selection bias — interventorul poate targeta conturi cu profil diferit fata de necontactati.</em></p>
      </div>
    </div>

  </div><!-- end sidebar -->

  <div class="footer" style="grid-column: 1 / -1;">
    {calc['title']} &nbsp;|&nbsp; {period} &nbsp;|&nbsp; Generated by Incrementality Analysis Skill
  </div>
</div>

<script>
Chart.defaults.font.family = "'Segoe UI', -apple-system, sans-serif";
Chart.defaults.font.size = 13;

new Chart(document.getElementById('chartIncrement'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(group_labels)},
    datasets: [
      {{ label: 'Increment @{calc["baseline_a_rate"]:.1%}', data: {json.dumps(inc_a_data)}, backgroundColor: '#AB47BC', borderRadius: 4, barPercentage: 0.7 }},
      {{ label: 'Increment extra @{calc["baseline_b_rate"]:.1%}', data: {json.dumps(inc_extra)}, backgroundColor: '#CE93D8', borderRadius: 4, barPercentage: 0.7 }},
      {{ label: 'Organic (ar fi existat)', data: {json.dumps(organic_data)}, backgroundColor: '#E0E0E0', borderRadius: 4, barPercentage: 0.7 }}
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{
      title: {{ display: true, text: 'Incremental vs Organic per grup', font: {{ size: 14, weight: '600' }} }},
      legend: {{ position: 'bottom', labels: {{ usePointStyle: true, pointStyle: 'circle', padding: 16 }} }}
    }},
    scales: {{ x: {{ stacked: true, grid: {{ display: false }} }}, y: {{ stacked: true }} }}
  }}
}});

new Chart(document.getElementById('chartRates'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(rate_labels)},
    datasets: [{{ data: {json.dumps(rate_data)}, backgroundColor: [{','.join(rate_colors)}], borderRadius: 6, barPercentage: 0.6 }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      title: {{ display: true, text: 'Rate de conversie per grup vs baseline', font: {{ size: 14, weight: '600' }} }},
      tooltip: {{ callbacks: {{ label: ctx => ctx.parsed.y + '%' }} }}
    }},
    scales: {{
      y: {{ beginAtZero: true, ticks: {{ callback: v => v + '%' }} }},
      x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 11 }} }} }}
    }}
  }}
}});
</script>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"Report generated: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate incrementality analysis report")
    parser.add_argument("--data", required=True, help="Path to input JSON file")
    parser.add_argument("--output", required=True, help="Path for output HTML file")
    parser.add_argument("--title", help="Report title (overrides JSON)")
    parser.add_argument("--period", help="Period label (overrides JSON)")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    if args.title:
        data["title"] = args.title
    if args.period:
        data["period"] = args.period

    calc = compute_incrementality(data)
    generate_html(calc, args.output)


if __name__ == "__main__":
    main()
