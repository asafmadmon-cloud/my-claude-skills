# Valuation Formulas Reference

## 1. Owner Earnings (Buffett's Definition)

**Formula:**
```
Owner Earnings = Net Income + Depreciation/Amortization − Capital Expenditures
```

**Why this matters:** Net Income can be manipulated via accounting choices. Owner Earnings represents the cash actually available to the business owner after maintaining competitive position. It's Buffett's preferred measure of true profitability.

**Owner Earnings Yield:**
```
Owner Earnings Yield = Owner Earnings / Market Cap × 100
```
- > 6% = Value zone (at 10% discount rate)
- 3–6% = Fair value
- < 3% = Overvalued or growth premium priced in

**CapEx / D&A Ratio:**
```
CapEx / D&A < 1.5 = asset-light (Buffett prefers these)
CapEx / D&A > 2.0 = capital-intensive (flag for review)
```

---

## 2. Owner Earnings DCF (10-Year Projection)

Buffett discounts all future Owner Earnings back to present value at his hurdle rate of 10%.

**Step-by-step:**

1. **Get Base Owner Earnings** = Net Income + D&A − CapEx (from last full year)

2. **Get Growth Rate** — priority order:
   - Analyst 5-year consensus estimate (from yfinance growth_estimates)
   - TTM earnings growth (if no analyst estimate)
   - TTM revenue growth (fallback)
   - 5% default (conservative fallback)

3. **Run 3 scenarios:**
   - Conservative: 60% of growth rate
   - Base: 100% of growth rate (capped at 25% to avoid fantasy)
   - Optimistic: 140% of growth rate

4. **Project 10 years:** For each year, Owner Earnings × (1 + growth_rate)^year

5. **Calculate Terminal Value:**
   ```
   Terminal Value = Year 10 Owner Earnings × (1 + 3%) / (10% − 3%)
   Terminal Value = Year 10 OE × 1.03 / 0.07
   ```
   Note: 3% is the assumed long-run nominal GDP growth (terminal growth rate)

6. **Discount all values to present at 10%:**
   ```
   PV = Cash Flow / (1 + 0.10)^year
   ```

7. **Intrinsic Value = Sum of all discounted Owner Earnings + PV of Terminal Value**

8. **Margin of Safety:**
   ```
   MoS% = (Intrinsic Value − Current Price) / Intrinsic Value × 100
   ```
   - > 40% = Deep Value (Buffett's sweet spot)
   - 20–40% = Margin of Safety present
   - 0–20% = Fairly valued
   - Negative = Overvalued — wait

**Important limitations:**
- DCF is highly sensitive to growth rate assumptions
- A wide range between conservative and optimistic = high uncertainty
- For businesses with unpredictable cash flows, use Graham Number as primary check

---

## 3. Graham Number

The Graham Number is the **maximum price** a defensive investor should pay for a stock, using Benjamin Graham's formula from "The Intelligent Investor."

**Formula:**
```
Graham Number = √(22.5 × EPS × BVPS)
```

Where:
- EPS = Earnings Per Share (TTM, trailing twelve months)
- BVPS = Book Value Per Share
- 22.5 = 15 (max P/E) × 1.5 (max P/B) — Graham's ceiling

**How to use it:**
- If Current Price < Graham Number → trading below Graham's conservative ceiling
- If Current Price > Graham Number → requires premium justification (MOAT, growth)
- Graham Number works best for stable, asset-heavy businesses (banks, industrials)
- Less useful for asset-light technology companies (high ROE = high BVPS distortion)

**Adjustment for negative book value:**
- If BVPS is negative (common in buyback-heavy companies like AAPL), Graham Number is not calculable
- Flag this: "Graham Number N/A — negative book value due to aggressive buyback program"
- Use DCF as primary valuation in this case

---

## 4. ROIC vs. WACC

ROIC > WACC = the business is creating value for shareholders.
ROIC < WACC = the business is destroying value (even if profitable on paper).

**ROIC Formula:**
```
NOPAT = Net Income + Interest Expense × (1 − Tax Rate)
Invested Capital = Total Debt + Market Cap (simplified)
ROIC = NOPAT / Invested Capital × 100
```

**WACC Formula (simplified):**
```
Risk-Free Rate = Current 10-Year US Treasury yield (approximately 4.2% in 2026)
Equity Risk Premium = 5.5% (historical average)
Cost of Equity = Risk-Free Rate + Beta × Equity Risk Premium
WACC ≈ Cost of Equity (for low-debt companies)
```

**Interpretation:**
- ROIC 20%+ with WACC ~8–10% = substantial value creation (Wide Moat evidence)
- ROIC 10–15% = narrow spread, monitor
- ROIC < WACC = value destruction — requires explanation

**Buffett's shortcut:** He looks for businesses earning 15%+ ROE consistently, which is his proxy for ROIC > WACC without requiring a complex WACC calculation.

---

## 5. Buffett Score Component Formulas

### MOAT Strength (0–25 points)
```
MOAT Score = raw score from moat_scorer.py (0–25)
Points = MOAT Score (direct mapping)
```

### Fundamentals Quality (0–25 points)
```
ROE ≥ 20%:      8 pts | 15–20%: 5 pts | 10–15%: 2 pts | <10%: 0 pts
ROIC > WACC:    6 pts | ROIC > 15% but below WACC: 3 pts | ROIC < 15%: 0 pts
FCF Positive:   5 pts | Intermittent: 2 pts | Negative: 0 pts
Margin Stable+: 4 pts | Margin Declining: 0 pts
Owner Earn Yld: ≥6% = 2pts | 3-6% = 1pt | <3% = 0pts
Total max: 25
```

### Valuation / Margin of Safety (0–25 points)
```
MoS > 40%:         25 pts (Deep Value — Buffett's sweet spot)
MoS 20–40%:        15 pts (Margin of Safety present)
MoS 0–20%:          5 pts (Fairly valued)
MoS negative:       0 pts (Overvalued)
```
Note: Uses the BASE CASE DCF estimate. If Graham Number is available, average the two MoS figures.

### Management Quality (0–15 points)
```
No share dilution (<2%/yr):          5 pts | Mild dilution: 2 pts | Heavy dilution: 0 pts
Insider ownership ≥5%:               4 pts | 1–5%: 2 pts | <1%: 0 pts
Buyback track record (shrinking SO): 4 pts | Flat: 2 pts | Growing SO: 0 pts
Capital allocation quality:          2 pts (qualitative — rational dividends/buybacks)
Total max: 15
```

### Analyst Quality Momentum (0–10 points)
```
TipRanks Smart Score ≥ 8:            4 pts | Score 6–7: 2 pts | Score <6: 0 pts
Quality-adj consensus majority Buy:  3 pts | Mixed: 1 pt | Majority Sell: 0 pts
3-month trend improving:             2 pts | Stable: 1 pt | Deteriorating: 0 pts
EPS revisions upward:                1 pt  | Downward: 0 pts
Total max: 10
```

---

## 6. ETF Buffett Score Component Formulas

### Efficiency (0–35 points)
```
Expense Ratio ≤0.05%:   20 pts | ≤0.10%: 15 pts | ≤0.25%: 8 pts | ≤0.50%: 3 pts | >0.50%: 0 pts
AUM > $10B:             10 pts | >$1B: 7 pts | >$100M: 3 pts | <$100M: 0 pts
Beta ≤ 0.8:              5 pts | 0.8–1.0: 3 pts | 1.0–1.3: 1 pt | >1.3: 0 pts
Total max: 35
```

### Diversification Quality (0–35 points)
```
Top 15 concentration ≤30%:    15 pts | ≤40%: 10 pts | ≤50%: 5 pts | >50%: 0 pts
Moat overlap ≥10 of 15:       12 pts | ≥7 of 15: 8 pts | <7 of 15: 2 pts
Sector spread ≥5 sectors:      8 pts | ≥3 sectors: 5 pts | <3 sectors: 0 pts
Total max: 35
```

### Factor Value (0–30 points)
```
ETF P/E vs S&P 500 (P/E ~22):
  ETF P/E < 15:              25 pts | 15–20: 15 pts | 20–25: 8 pts | >25: 0 pts
P/B below market average:     5 pts | At market: 3 pts | Above market: 0 pts
Total max: 30
```

---

## Quick Reference: Key Thresholds

| Metric | Excellent | Acceptable | Flag | Avoid |
|--------|-----------|-----------|------|-------|
| ROE | ≥ 20% | 15–20% | 10–15% | < 10% |
| Debt/Equity | < 0.3 | 0.3–0.5 | 0.5–1.0 | > 1.0 |
| Owner Earnings Yield | > 6% | 4–6% | 2–4% | < 2% |
| Gross Margin (non-commodity) | > 40% | 25–40% | 15–25% | < 15% |
| ROIC | > 20% | 15–20% | 10–15% | < WACC |
| Margin of Safety | > 40% | 20–40% | 0–20% | Negative |
| ETF Expense Ratio | < 0.10% | 0.10–0.25% | 0.25–0.50% | > 0.50% |
| ETF AUM | > $10B | > $1B | > $100M | < $100M |
