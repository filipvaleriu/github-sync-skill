---
name: incrementality-analysis
description: >
  Analyze the true incremental impact of any intervention (sales team, campaign, partner channel)
  on conversion rates. Use this skill whenever someone asks about attribution, incrementality,
  "how much did X really contribute", "would these conversions have happened anyway", "what's the
  real impact of our sales team / campaign / partner", or wants to separate organic from influenced
  conversions. Also trigger when you see conversion data split into contacted vs non-contacted groups,
  or when someone has CRM/sales data and wants to know the true ROI of an outreach effort.
  Generates an interactive HTML report with charts and tables, ready to present to stakeholders.
---

# Incrementality Analysis Skill

## What this skill does

This skill answers the fundamental business question: **"Of all the conversions attributed to an intervention (sales team, campaign, partner), how many would have happened anyway without it?"**

It replaces naive mechanical attribution (e.g., "they touched it, so they get credit") with a **counterfactual analysis** that estimates what would have happened in the absence of the intervention. The difference — the increment — is the true contribution worth rewarding.

## Why this matters

Mechanical attribution (assigning credit based on invoice series, CRM tags, or last-touch) systematically overstates contributions. A sales team that calls 7,000 leads and "generates" 1,000 conversions may actually only be responsible for 400 of them — the other 600 would have converted organically. Conversely, mechanical attribution misses indirect effects: leads who refused the call but were influenced by the awareness it created.

The counterfactual method catches both problems: it subtracts the organic baseline from every group AND discovers hidden contributions in groups previously labeled "organic."

## Core Method: Counterfactual Incrementality

### Step 1: Identify the groups

From the data, identify these populations:

1. **Contacted + outcome known** — leads where the intervention happened and we know the result (e.g., "Accepted offer", "Refused", "Interested", "No answer")
2. **Contacted + outcome unknown** — leads contacted but with no recorded outcome (e.g., missing CRM tag)
3. **Not contacted** — leads in the eligible universe that were never reached by the intervention

For each group, you need: number of leads and number of conversions.

### Step 2: Establish the counterfactual baseline

The baseline answers: "At what rate would these leads have converted if the intervention never existed?"

Always compute TWO baselines and present a range:

**Baseline A — "Failed intervention" group** (conservative)
Use leads where the intervention was attempted but failed to make meaningful contact. Examples: "No answer" + "Wrong number" + "Refused conversation". These share the same selection criteria as successfully contacted leads (same targeting, same timing) but received no effective intervention. This is your best natural control group — same selection bias, zero treatment effect.

Nuance: if "Refused" implies a real conversation happened (not just "refused to pick up"), its conversion rate may contain some indirect influence from the call. In that case, consider using only "No answer" + "Wrong number" as a purer control. Document this choice.

**Baseline B — "Not contacted" group** (alternative)
Use all eligible leads that were never contacted. Zero intervention, but potentially different profile (e.g., older accounts, different channels). This baseline may underestimate organic rate if the intervention targeted higher-quality leads.

Present both baselines and the resulting range. The truth is between them.

### Step 3: Calculate increment per group

For each subgroup of contacted leads:

```
Expected organic = Number of leads × Baseline rate
Increment = Actual conversions − Expected organic
If increment ≤ 0 → report as 0 (not negative)
```

The `increment ≤ 0 → 0` rule exists because a negative increment means the group converts below baseline — the intervention didn't help, but it also didn't cause harm (the leads would have converted at baseline rate regardless). Don't punish the intervention for groups it didn't influence.

**However**, also compute and report the NET increment across all groups (allowing negatives to cancel positives). This is the most honest single number.

### Step 4: Answer the key business questions

Structure conclusions around these specific questions:

1. **Total truly incremental conversions** — range, using both baselines
2. **For directly attributed conversions (e.g., invoices on the intervention's series): how many would have existed anyway?**
   - From the "Accepted" group: `proportion_incremental = (actual - expected) / actual`
   - Apply this proportion to the directly attributed subset
3. **For "refused but converted" cases: how many were influenced by the contact?**
   - If group rate > baseline → lift exists → some were influenced
   - Estimate: `influenced = actual - expected`
4. **For unknown-outcome contacts: estimate the intervention's share**
   - Same lift method: `rate_unknown - baseline_rate` × number of leads
5. **Incremental conversion rate** — from contacted leads, what's the NET rate the intervention adds beyond organic?

### Step 5: Generate the output

Run the bundled Python script to produce an interactive HTML report:

```bash
python <skill-path>/scripts/incrementality_report.py \
  --data input_data.json \
  --output report.html \
  --title "Your Report Title" \
  --period "Nov 2025 - Mar 2026"
```

If the script is not appropriate for the data format, generate the HTML directly following the template in `references/html_template.md`. The report must include:

1. **Sticky navigation bar** at the top, always visible, with links to each section. Uses `position: sticky; top: 0; z-index: 100;` and `grid-column: 1 / -1` to span full width.
2. **Executive summary** with KPI cards showing: total conversions, total from contacted, truly incremental (range), would-have-converted-anyway
3. **Methodology section** explaining counterfactual approach and baseline choices
4. **Per-group incrementality table** with: group name, leads, actual conversions, rate, expected @baseline A, expected @baseline B, increment range, interpretation
5. **Stacked bar chart** showing incremental vs organic per group (Chart.js)
6. **Specific answers** to the business questions (with formulas shown)
7. **Funnel** recalculated with incrementality (not mechanical attribution)
8. **Limitations and assumptions** with severity ratings
9. **Right sidebar with methodology references** — sticky, scrollable, containing academic and industry references organized by method. See `references/html_template.md` for the full reference list and HTML structure. The sidebar uses CSS Grid (`grid-template-columns: 1fr 300px`) alongside the main content, collapses to single-column on mobile (≤900px), and hides on print.

## Input data format

The skill works with any data that has these elements:

```json
{
  "groups": [
    {
      "name": "Group label (e.g., 'Accepted offer')",
      "leads": 560,
      "conversions": 363,
      "is_baseline_negative": false,
      "is_not_contacted": false,
      "directly_attributed_subset": 339
    }
  ],
  "total_eligible": 45182,
  "total_conversions": 3899,
  "period": "Nov 2025 - Mar 2026",
  "intervention_name": "Sales Team"
}
```

But often the data comes as CSVs, Excel files, or database extracts. In that case, parse it first, build the groups, and then apply the method. The key is to identify which column/field distinguishes contacted from non-contacted, and which field contains the outcome tag.

## When results seem surprising

- **"Interested" group converting below baseline**: This is common. It often means the tag reflects the agent's optimism, not the lead's actual intent. Don't attribute these to the intervention — they're organic.
- **"Refused" group converting above baseline**: This suggests indirect influence (awareness created by the call). Attribute the lift, not all conversions.
- **Very high increment for "No tag" group**: Check if this group has a different profile (e.g., larger companies, different channel). If possible, compare on observable characteristics before attributing the lift.

## Assumptions to always document

1. Which baseline was used and why
2. Whether "Refused" was included in the control group or not (and the reasoning)
3. Whether the contacted group was selected differently from non-contacted (targeting bias)
4. Time period covered and whether it includes seasonal effects
5. Any external factors (promotions, campaigns) that affect both groups differently
