# Strategic Stock Analysis Skill — Usage Guide

## How to Use This Skill

### Triggering an Analysis

Just type naturally. The skill activates whenever you mention a ticker, ask about a stock, or ask a market question.

**Stock analysis:**
```
AAPL
Analyze $NVDA
Should I buy Microsoft?
Is KO a good long-term hold?
Run a Buffett analysis on $MCO
```

**ETF audit:**
```
VOO
Should I add QQQ to my core portfolio?
Run an ETF audit on ARKK
```

**Market scan:**
```
What sectors look cheap right now?
Where is the margin of safety in 2026?
What sectors have AI tailwinds?
```

**Explicit mode prefixes (optional):**
```
QUICK: AAPL          → Summary Card only (fast sniff test)
DEEP: AAPL           → Full memo with all sections
MODE1: AAPL          → Force stock analysis
MODE1-ETF: VOO       → Force ETF audit
MODE2: semiconductors → Force sector scan
```

---

## The Analysis Pipeline

When you submit a ticker, the skill runs this pipeline automatically:

```
1. fetch_data.py        → Pulls all data from Yahoo Finance
2. moat_scorer.py       → Scores the 5 MOAT dimensions (stocks only)
3. valuation.py         → Runs DCF, Graham Number, ROIC, Buffett Score
4. analyze_stock.py     → Orchestrates everything + red flags + 4-filter check
   OR analyze_etf.py    → ETF-specific audit
5. report_generator.py  → Formats the full report + charts
```

All data comes from **Yahoo Finance (yfinance)** automatically. No manual input needed.

---

## How Each Section Is Calculated

---

### BUFFETT SCORE (0–100)

The single most important number. It combines five weighted components:

| Component | Max | What it measures |
|-----------|-----|-----------------|
| MOAT Strength | 25 | Durability of competitive advantage |
| Fundamentals Quality | 25 | ROE, FCF, margins, debt |
| Valuation / MoS | 25 | How cheap the stock is vs. intrinsic value |
| Management Quality | 15 | Buybacks, insider ownership, no dilution |
| Analyst Momentum | 10 | Yahoo Finance consensus + coverage depth |
| **TOTAL** | **100** | |

**Score → Verdict:**
- 80–100 → **STRONG BUY** (Wide Moat + Deep Value)
- 65–79 → **BUY** (Quality business at fair price)
- 50–64 → **HOLD** (Decent business, watch price)
- 35–49 → **MONITOR** (Weak moat or overvalued)
- 0–34 → **AVOID** (No moat, dangerous balance sheet, or extreme overvaluation)

---

### SECTION 1: KEY METRICS SNAPSHOT

All data pulled directly from Yahoo Finance. Every metric shows its source.

| Metric | Where it comes from | What to look for |
|--------|-------------------|-----------------|
| Current Price | Yahoo Finance real-time | Reference point for all valuation |
| Market Cap | Price × Shares Outstanding | Scale of the business |
| P/E (TTM) | Trailing 12-month price/earnings | < 20 = potentially cheap |
| P/E (Forward) | Analyst estimated earnings | Lower than TTM = earnings growing |
| ROE | Net Income / Shareholder Equity | Buffett wants ≥ 15–20% consistently |
| Gross Margin | Gross Profit / Revenue | > 40% = pricing power signal |
| Debt/Equity | Total Debt / Shareholder Equity | > 1.0 = red flag |
| EPS (TTM) | Earnings Per Share, trailing | Used in Graham Number |
| BVPS | Book Value Per Share | Used in Graham Number |
| 52-Week Range | High and low over past year | Where does price sit in the range? |
| Beta | Volatility vs. S&P 500 | > 1.0 = more volatile than market |
| Owner Earnings | Net Income + D&A − CapEx | The real cash available to owners |

---

### SECTION 2: BUFFETT SCORE BREAKDOWN

Shows the sub-score for each of the five components with the evidence behind each point.

**MOAT (0–25):** Direct passthrough from Section 3 total.

**Fundamentals (0–25):**
- ROE ≥ 20% → +5 pts; ≥ 15% → +4 pts; ≥ 10% → +2 pts
- D/E ≤ 0.25 → +5 pts; ≤ 0.5 → +4 pts; ≤ 1.0 → +2 pts; > 1.0 → +0
- Owner Earnings positive → +5 pts; FCF positive → +4 pts
- Gross Margin ≥ 60% → +5 pts; ≥ 40% → +3 pts; ≥ 25% → +1 pt
- Revenue growth ≥ 15% → +5 pts; ≥ 8% → +3 pts; ≥ 3% → +1 pt

**Valuation (0–25):**
- Margin of Safety ≥ 40% → 25 pts
- MoS 30–40% → 20 pts
- MoS 20–30% → 15 pts
- MoS 10–20% → 8 pts
- MoS 0–10% → 3 pts
- MoS negative → 0 pts

**Management (0–15):**
- Insider ownership ≥ 10% → +5 pts; ≥ 5% → +4 pts; ≥ 1% → +2 pts
- Share count shrinking (buybacks) → +5 pts; flat → +4 pts; growing → +0
- Sustainable dividend (payout < 60%) → +5 pts; no dividend but growing revenue → +4 pts

**Analyst Momentum (0–10):**
- Consensus mean ≤ 1.5 (Strong Buy range) → +5 pts; ≤ 2.0 → +4 pts
- ≥ 20 analysts covering → +3 pts; ≥ 10 → +2 pts; < 5 → +2 (underfollowed potential)
- Upside to analyst target > 30% → +2 pts; > 15% → +1 pt

---

### SECTION 3: MOAT ANALYSIS

Scores the five types of competitive moat that Buffett looks for, each on a 0–5 scale.

#### How Each MOAT Dimension Is Scored

**Switching Costs (0–5)**
Measures how painful it is for customers to leave.
- +2 if the industry is software, SaaS, banking, consumer electronics, or similar high-lock-in sector
- +2 if gross margin > 70% (customers paying a premium = locked in)
- +1 if gross margin > 50%
- +1 if revenue growing > 5% (stable/growing customer base)

**Network Effect (0–5)**
Measures whether the product gets more valuable as more people use it.
- +2 if it's a platform, marketplace, payment, social, or exchange business
- +2 if gross margin > 60% AND revenue growing > 15% (network flywheel signal)
- +1 if gross margin > 50%
- +1 if operating margin > 20% (scale leverage)

**Cost Advantage (0–5)**
Measures whether the company can produce cheaper than competitors.
- Compares gross margin to sector benchmark (Technology: 55%, Healthcare: 50%, etc.)
- +3 if gross margin is 20+ pp above sector avg
- +2 if 10+ pp above sector avg
- +1 if above sector avg
- +1 if operating margin > 20%
- +1 if FCF/Net Income > 1.1x (excellent cash conversion)

**Intangible Assets (0–5)**
Measures brands, patents, regulatory licenses.
- +2 if brand-driven industry (consumer goods, beverages, electronics, entertainment)
- +2 if patent-driven industry (pharma, biotech, semiconductor, defense)
- +3 if license-driven industry (credit ratings, financial data, utilities, telecom)
- +2 if gross margin > 65% (pricing power = strong intangible)
- +1 if gross margin > 50%

**Efficient Scale (0–5)**
Measures whether the market can only support 1–3 profitable players.
- +3 if natural oligopoly industry (railroad, pipeline, utility, landfill, port, exchange)
- +2 if market cap > $500B (scale dominance)
- +1 if market cap > $100B
- +1 if high capex (>15% of revenue) with strong margins (capital moat)

**MOAT Classification:**
- 18–25 → Wide Moat ✅
- 10–17 → Narrow Moat ⚠️
- 0–9 → No Moat ❌

> **Important:** The automatic score is a starting floor. Always check the "Manual check" notes for each dimension. The script uses industry proxies — you may need to adjust up or down based on what you know about the specific business.

---

### SECTION 4: BUFFETT'S 4-FILTER SCORECARD

Buffett's four non-negotiable criteria. A stock that fails 2+ filters should be HOLD or AVOID regardless of analyst consensus.

**Filter 1 — Enduring Competitive Advantage:**
- PASS: MOAT Score ≥ 18 (Wide Moat)
- PARTIAL: MOAT Score 10–17 (Narrow Moat)
- FAIL: MOAT Score < 10 (No Moat)

**Filter 2 — Management Quality:**
- PASS: At least 2 of: ROE ≥ 15%, no dilution, insider ownership ≥ 5%
- PARTIAL: 1 of the above
- FAIL: 0 of the above

**Filter 3 — Sensible Price (Margin of Safety):**
- PASS: Margin of Safety ≥ 20%
- PARTIAL: MoS ≥ 0% (fairly valued, thin cushion)
- FAIL: MoS negative (trading above intrinsic value)

**Filter 4 — Generates Free Cash Flow:**
- PASS: Owner Earnings > 0 (or FCF > 0)
- FAIL: Negative Owner Earnings or FCF

---

### SECTION 5: INTRINSIC VALUE & MARGIN OF SAFETY

Two independent valuation methods. Both are shown so you can compare.

#### Owner Earnings DCF

1. **Owner Earnings** = Net Income + Depreciation/Amortization − CapEx
   - This is the cash available to owners after maintaining the business
   - Per share = Owner Earnings / Shares Outstanding

2. **Growth Rate Selection** (priority order):
   - Analyst 5-year consensus estimate (from Yahoo Finance)
   - Trailing 12-month earnings growth (capped at 20%)
   - Trailing 12-month revenue growth (capped at 15%)
   - Default: 5% conservative fallback

3. **Three scenarios:**
   - Conservative = 60% of growth rate (business disappoints)
   - Base = 100% of growth rate (base case)
   - Optimistic = 140% of growth rate (business over-delivers, max 25%)

4. **Projection:** 10 years of compounding Owner Earnings per share

5. **Terminal Value** = Year 10 Owner Earnings × 1.03 / (0.10 − 0.03)
   - Assumes 3% perpetual growth (nominal GDP level)
   - Discounted at 10% (Buffett's hurdle rate)

6. **Intrinsic Value** = Sum of discounted annual earnings + discounted terminal value

7. **Margin of Safety** = (Intrinsic Value − Current Price) / Intrinsic Value × 100

#### Graham Number

```
Graham Number = √(22.5 × EPS × BVPS)
```

- 22.5 = 15 (max P/E) × 1.5 (max P/B) — Benjamin Graham's conservative ceiling
- Represents the absolute maximum price a defensive investor should pay
- **Not applicable** when BVPS is negative (common for buyback-heavy companies like AAPL)
- Works best for stable, asset-heavy businesses

#### ROIC vs. WACC

- **ROIC** (Return on Invested Capital) = Operating Income × (1 − 21% tax) / Invested Capital
- **WACC** = Risk-Free Rate (4.5%) + Beta × 5.5% Equity Risk Premium
- **ROIC > WACC** = Value being created ✅
- **ROIC < WACC** = Value being destroyed ❌ (even if profitable on paper)

---

### SECTION 6: ANALYST CONSENSUS

Layered from multiple sources for signal quality:

**Yahoo Finance (automated):**
- Total number of analysts covering the stock
- Mean consensus rating (1.0 = Strong Buy → 5.0 = Strong Sell)
- Average price target (low / avg / high)
- Upside/downside to target from current price

**Flags generated automatically:**
- **HERD MENTALITY ALERT:** Analysts bullish (consensus ≤ 2.0) but Buffett Score < 50 → Wall Street enthusiasm may not be backed by fundamentals
- **UNDISCOVERED GEM:** Buffett Score ≥ 65 but analyst consensus neutral → strong fundamentals without Wall Street attention = potential alpha
- **UNDERFOLLOWED:** < 5 analysts covering → may be under-researched

**Manual checks to do yourself:**
- TipRanks: Filter for analysts with ≥ 3★ rating accuracy — this removes low-quality analysts from the consensus
- MarketBeat: Check the 3-month consensus direction (improving or deteriorating?)
- StockAnalysis.com: Are EPS estimates being revised up or down?

---

### SECTION 9: MARKET TIMING & ENTRY CONDITIONS

**This section does NOT affect the Buffett Score.** It answers "is now a good time to pull the trigger on a stock I already believe in?"

| Signal | Green 🟢 | Neutral 🟡 | Red 🔴 |
|--------|---------|-----------|------|
| RSI (14-day) | < 30 (oversold) | 30–70 | > 70 (overbought) |
| VIX | > 30 (high fear) | 15–30 | < 15 (complacency) |
| 52-Week Position | < 30% of range (near lows) | 30–80% | > 80% (near highs) |
| Earnings Proximity | > 30 days away | 14–30 days | < 14 days (event risk) |

**Count green signals:**
- 3+ greens on a high Buffett Score → Strong entry window
- 1–2 greens → Neutral conditions
- 0 greens → Wait for better setup

> Buffett's principle: "Be fearful when others are greedy, and greedy when others are fearful." High VIX (>30) = fear = Buffett's buying environment.

---

### SECTION 10: RED FLAGS

Automatically detected from the financial data:

| Flag | Severity | Threshold |
|------|----------|-----------|
| High debt | 🔴 Critical | Debt/Equity > 1.0 |
| Negative cash flow | 🔴 Critical | Owner Earnings or FCF < 0 |
| Share dilution | 🔴 Critical | Shares outstanding growing > 2%/yr |
| Thin operating margin | 🟡 Caution | Operating margin < 5% |
| Low ROE | 🟡 Caution | ROE < 10% |
| Excessive valuation | 🟡 Caution | P/E > 50x |

Any critical flag automatically suppresses the Buffett Score. Two or more critical flags should result in an AVOID regardless of other metrics.

---

## ETF Track: How the ETF Buffett Score Is Calculated

For ETFs, the analysis is an **Efficiency Audit** — not a MOAT analysis. The question is: "Is this ETF an efficient vehicle for market exposure?"

### ETF Buffett Score (0–100)

| Component | Max | What it measures |
|-----------|-----|-----------------|
| Efficiency | 35 | Expense ratio + tracking error + AUM/liquidity |
| Diversification Quality | 35 | Top 15 concentration + moat quality of holdings + sector spread |
| Factor Value | 30 | P/E and P/B vs. S&P 500 baseline |

**Expense Ratio scoring:**
- ≤ 0.05% → 35 pts (Vanguard index tier)
- ≤ 0.10% → 30 pts (Buffett-approved passive)
- ≤ 0.25% → 20 pts (acceptable)
- ≤ 0.50% → 10 pts (high cost, erodes returns)
- > 0.50% → 0 pts (avoid)

**Top 15 Concentration (The 40% Rule):**
- Combined weight of top 15 holdings > 50% → 🔴 Top-Heavy
- 40–50% → 🟡 Moderate
- < 40% → ✅ Diversified

**Moat Overlap:**
- ≥ 10 of top 15 holdings are known moat companies → ✅ High Quality
- 5–9 of 15 → 🟡 Moderate
- < 5 of 15 → 🔴 Low Quality

**ETF Verdict → Bucket:**
- 80–100 → STRONG CORE HOLD → Bucket A (passive core)
- 65–79 → GOOD CORE HOLD → Bucket A
- 50–64 → ACCEPTABLE → Bucket A/B (with caveats)
- 35–49 → CAUTION → Bucket B (satellite only)
- 0–34 → AVOID

---

## The Core + Satellite Framework

Every analysis ends with a bucket recommendation:

**Bucket A — Passive Core (typically 60–80% of portfolio)**
- Broad index ETFs (VOO, VTI, VXUS)
- Low-cost (< 0.10%), diversified, passive
- Goal: capture market returns efficiently

**Bucket B — Active MOAT Satellites (typically 20–40% of portfolio)**
- Individual wide-moat stocks or thematic ETFs
- Each position should have Buffett Score ≥ 65 AND Margin of Safety ≥ 20%
- Goal: outperform the index through quality + value selection

> Buffett's advice to retail investors: put the majority in Bucket A (S&P 500 index). Only use Bucket B if you have time and competence to research individual businesses within your Circle of Competence.

---

## Data Sources & Verification

| Data Point | Primary Source (Automated) | Fallback (Manual) |
|------------|---------------------------|-------------------|
| Price, P/E, P/B, Beta | Yahoo Finance (yfinance) | Google Finance |
| ROE, Margins, D/E | Yahoo Finance Statistics | Macrotrends.net |
| EPS, BVPS | Yahoo Finance | SEC EDGAR 10-K |
| Analyst Ratings | Yahoo Finance | TipRanks (quality-weighted) |
| ETF Expense Ratio | Yahoo Finance (often missing) | ETF.com or fund prospectus |
| Earnings Date | Yahoo Finance Calendar | Earnings Whispers |
| CapEx, D&A | Yahoo Finance Cash Flow | SEC EDGAR |
| Insider Ownership | Yahoo Finance | SEC Form 4 |

**When a field shows N/A:** The data wasn't available from Yahoo Finance for this ticker. Check the fallback source listed in `references/data_sources.md`.

---

## Limitations to Be Aware Of

1. **MOAT scoring is semi-automated.** The script uses industry classification proxies. Verify the "Manual check" notes for each dimension — especially for companies that don't fit neatly into standard sector buckets.

2. **DCF is highly sensitive to growth rate.** A wide gap between the conservative and optimistic scenario means high uncertainty. When the range is wide, weight the conservative scenario more heavily.

3. **Graham Number doesn't work for negative book value.** Companies like Apple with aggressive buyback programs often have negative book equity. In these cases, rely on the DCF only.

4. **Analyst consensus is from Yahoo Finance, not quality-weighted.** Always verify on TipRanks filtering for ≥ 3★ analysts. A consensus built on 30 low-quality analysts is less meaningful than 5 top-tier analysts.

5. **Entry Conditions are advisory only.** A great business at a fair price is worth buying regardless of RSI or VIX signals. The entry section helps you time your entry — it doesn't change the fundamental thesis.

6. **The skill uses TTM (trailing twelve months) data.** For cyclical businesses at a cycle peak or trough, TTM metrics can be misleading. Use your judgment about where in the cycle the business is.
