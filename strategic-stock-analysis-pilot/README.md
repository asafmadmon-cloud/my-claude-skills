# 📊 strategic-stock-analysis-pilot

> A Senior Investment Strategist skill for Claude Code applying Warren Buffett's "Circle of Competence" framework.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

Every analysis produces a **Buffett Score (0–100)** with a clear buy/hold/sell recommendation backed by data-driven calculations.

---

## 🚀 Modes

| Mode | Trigger | Output |
|------|---------|--------|
| Default | Type a ticker (e.g. `AAPL`) | Full analysis |
| `QUICK: TICKER` | Sniff test | Summary card only |
| `DEEP: TICKER` | Full research | All sections + all calculations shown |
| `MODE2: semiconductors` | Broad question | Sector opportunity scan |

---

## 🏆 The Buffett Score (0–100)

The single most important output. Synthesizes all analysis into one signal.

| Component | Max | How It's Calculated |
|-----------|-----|-------------------|
| 🏰 MOAT Strength | 25 | Sum of 5 MOAT type scores |
| 📈 Fundamentals Quality | 25 | ROE, ROIC vs. WACC, FCF consistency, margin stability |
| 💰 Valuation / Margin of Safety | 25 | MoS ≥ 40% = 25 pts · MoS 20–40% = 15 pts · MoS 0–20% = 5 pts · Negative = 0 |
| 👔 Management Quality | 15 | Buyback history, dilution check, insider ownership ≥5% |
| 📡 Analyst Quality Momentum | 10 | TipRanks quality-weighted consensus + 3-month trend |
| **TOTAL** | **100** | |

**Score → Signal:**

| Score | Verdict |
|-------|---------|
| 80–100 | 🟢 **STRONG BUY** — Wide Moat + Deep Value |
| 65–79 | 🟢 **BUY** — Quality business at fair price |
| 50–64 | 🟡 **HOLD** — Decent business, watch price |
| 35–49 | 🟠 **MONITOR** — Weak moat or overvalued |
| 0–34 | 🔴 **AVOID** — No moat or dangerous balance sheet |

---

## 🏰 MOAT Analysis

<details>
<summary>Click to expand — 5 MOAT types, scored 0–5 each (/25 total)</summary>

| MOAT Type | What It Measures | Example |
|-----------|----------------|---------|
| **Switching Costs** | How painful it is for customers to leave | Adobe, Salesforce |
| **Network Effect** | Product becomes more valuable as more people use it | Visa, Meta |
| **Cost Advantage** | Structurally lower cost to produce/deliver than rivals | Costco, Amazon |
| **Intangible Assets** | Brands, patents, licenses, regulatory moats | Coca-Cola, J&J |
| **Efficient Scale** | Niche market where a second competitor can't profitably enter | Waste management, pipelines |

- **18–25** = Wide Moat (Buffett-quality)
- **10–17** = Narrow Moat (monitor)
- **0–9** = No Moat (avoid)

</details>

---

## 🔍 Buffett's 4-Filter Scorecard

A stock failing 2+ filters = HOLD or AVOID, regardless of analyst consensus.

| # | Filter | Pass Condition |
|---|--------|---------------|
| 1 | Enduring competitive advantage? | MOAT score ≥ 18 |
| 2 | Management quality? | ROE trending up + buybacks + no dilution |
| 3 | Sensible price? | Margin of Safety ≥ 20% |
| 4 | Generates FCF? | Owner Earnings positive in 4 of 5 years |

---

## 💰 Intrinsic Value & Margin of Safety

<details>
<summary>Click to expand — valuation formulas</summary>

### Method 1 — Owner Earnings DCF
Buffett's preferred measure of true cash generation:

```
Owner Earnings = Net Income + D&A − CapEx
```

Projected forward 10 years using an estimated growth rate, then discounted back at 10%. Three scenarios shown:
- **Conservative** — low growth assumption
- **Base** — analyst consensus growth
- **Optimistic** — high growth assumption

### Method 2 — Graham Number
Benjamin Graham's formula for maximum fair price:

```
Graham Number = √(22.5 × EPS × Book Value Per Share)
```

Represents the upper bound of what a defensive investor should pay.

### Margin of Safety

```
Margin of Safety = (Intrinsic Value − Current Price) / Intrinsic Value
```

Buffett typically requires ≥ 20–25% before buying.

</details>

---

## 📡 Analyst Consensus (Multi-Source)

<details>
<summary>Click to expand — 4 sources layered for signal quality</summary>

| Source | What It Provides |
|--------|----------------|
| **Yahoo Finance** | Raw analyst count + rating breakdown (automated) |
| **TipRanks** | Quality-filtered consensus (≥3-star analysts only), Smart Score 1–10, price targets, recent upgrades/downgrades |
| **MarketBeat** | 3-month consensus direction |
| **StockAnalysis.com** | EPS revision trend |

**Pattern flags:**
- 🔴 **Herd Mentality** — high bullishness BUT Buffett Score < 50 → bubble risk
- 🟢 **Undiscovered Gem** — low coverage BUT Buffett Score > 65 → opportunity
- ⚠️ **Underfollowed** — < 5 analysts = Buffett's hunting ground

</details>

---

## ⏱️ Market Timing & Entry Conditions

> *Does not affect the Buffett Score — tells you WHEN to act on a thesis you already believe in.*

| Signal | 🟢 Green | 🟡 Yellow | 🔴 Red |
|--------|---------|---------|------|
| RSI (14-day) | < 30 oversold | 30–70 neutral | > 70 overbought |
| VIX | > 30 (fear zone) | 15–30 normal | < 15 complacency |
| 52-Week Position | < 30% of range | 30–80% | > 80% near highs |
| Earnings Proximity | > 14 days away | — | < 14 days |

3+ green signals on a high Buffett Score = strong entry window.

---

## 🚩 Red Flags

| Badge | Flag |
|-------|------|
| 🔴 Critical | Debt/Equity > 1.0 |
| 🔴 Critical | Negative FCF 2+ consecutive years |
| 🔴 Critical | Share dilution > 2%/yr |
| 🟡 Caution | Margin compression 3+ years |
| 🟡 Caution | Guidance misses 3+ consecutive quarters |
| 🟡 Caution | High EPS variability |

---

## 🗂️ ETF Efficiency Audit (Bucket A)

<details>
<summary>Click to expand — ETF scoring criteria</summary>

| Check | Criteria |
|-------|---------|
| Expense Ratio | ≤ 0.10% ✅ · 0.10–0.25% ⚠️ · > 0.25% 🔴 · > 0.50% 🔴🔴 |
| AUM | > $1B = adequate liquidity ✅ |
| Tracking Error | < 0.20% ✅ · > 0.20% 🔴 |
| Top-15 Concentration | > 40–50% combined weight = Top-Heavy 🔴 |
| Sector Concentration | > 50% of top 15 in same sector = disguised risk 🔴 |
| Moat Overlap | ≥ 10 of 15 top holdings pass Buffett quality filter ✅ |
| Factor Tilt | P/E vs S&P 500 (value) · ROE vs S&P 500 (quality) · Yield (dividend) |

</details>

---

## ⚙️ Installation

### 1. Copy the skill into your Claude Code project

```
your-project/
└── .claude/
    └── skills/
        └── strategic-stock-analysis-pilot/
```

### 2. Install Python dependencies

```bash
pip install yfinance pandas matplotlib requests
```

### 3. Update the Python path in SKILL.md

Open `SKILL.md` and replace:
```
C:/Users/User/AppData/Local/Programs/Python/Python312/python.exe
```
with your own Python executable path (find it by running `where python` or `which python`).

---

## 📋 Data Sources Priority

1. Yahoo Finance (automated via `yfinance`)
2. TipRanks (analyst quality filter)
3. SEC EDGAR (financial statements)
4. Company Investor Relations
