# Data Sources Reference

## Primary: Yahoo Finance via yfinance

All data pulled automatically by `fetch_data.py`. Paths below are for manual verification.

### Yahoo Finance Navigation Paths

| Metric | Yahoo Finance Path | yfinance Field |
|--------|-------------------|---------------|
| Current Price | Summary tab | `info.currentPrice` |
| Market Cap | Summary tab | `info.marketCap` |
| P/E (TTM) | Summary tab | `info.trailingPE` |
| P/E (Forward) | Summary tab | `info.forwardPE` |
| EPS (TTM) | Statistics tab → Per Share Data | `info.trailingEps` |
| Book Value/Share | Statistics tab → Per Share Data | `info.bookValue` |
| Beta | Summary tab | `info.beta` |
| 52-Week Range | Summary tab | `info.fiftyTwoWeekLow/High` |
| ROE (5yr avg) | Statistics tab → Management Effectiveness | `info.returnOnEquity` |
| ROA | Statistics tab → Management Effectiveness | `info.returnOnAssets` |
| Gross Margin | Statistics tab → Profitability | `info.grossMargins` |
| Operating Margin | Statistics tab → Profitability | `info.operatingMargins` |
| Net Margin | Statistics tab → Profitability | `info.profitMargins` |
| Revenue | Financials tab → Income Statement | `info.totalRevenue` |
| Net Income | Financials tab → Income Statement | `info.netIncomeToCommon` |
| Total Debt | Statistics tab → Balance Sheet | `info.totalDebt` |
| Debt/Equity | Statistics tab → Balance Sheet | `info.debtToEquity` (×100) |
| Total Cash | Statistics tab → Balance Sheet | `info.totalCash` |
| Free Cash Flow | Statistics tab → Cash Flow | `info.freeCashflow` |
| Operating Cash Flow | Statistics tab → Cash Flow | `info.operatingCashflow` |
| Insider Ownership | Statistics tab → Share Statistics | `info.heldPercentInsiders` |
| Shares Outstanding | Statistics tab → Share Statistics | `info.sharesOutstanding` |
| Analyst Count | Analysis tab → Analyst Price Targets | `info.numberOfAnalystOpinions` |
| Analyst Mean Rating | Analysis tab | `info.recommendationMean` (1=Strong Buy, 5=Sell) |
| Price Target (avg) | Analysis tab → Analyst Price Targets | `info.targetMeanPrice` |
| 5yr Growth Estimate | Analysis tab → Growth Estimates | `growth_estimates.loc["+5y"]` |
| ETF Expense Ratio | ETF Summary tab | `info.annualReportExpenseRatio` |
| ETF Top Holdings | ETF Holdings tab | `ticker.funds_data.top_holdings` |
| ETF Sector Weights | ETF Holdings tab | `ticker.funds_data.sector_weightings` |

---

## Fallback Sources by Data Type

### Financial Statements (when Yahoo Finance is missing)
**SEC EDGAR** (free, authoritative)
- URL: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<TICKER>&type=10-K`
- Use for: exact CapEx, D&A, complete cash flow statements
- Path: 10-K → Consolidated Statements of Cash Flows

**Company Investor Relations**
- URL: `https://ir.<company>.com` or Google "<company> investor relations"
- Use for: latest earnings release, supplemental financials, guidance

---

### Analyst Consensus (layered approach)

**1. Yahoo Finance** (baseline, automated)
- Gives: raw count + mean rating + price target range
- Limitation: aggregated, no quality weighting, can lag

**2. TipRanks** (primary quality filter — USER'S PREFERRED SOURCE)
- URL: `https://www.tipranks.com/stocks/<TICKER>/forecast`
- Use for: analyst quality rating (1-5 stars based on accuracy), Smart Score (1-10), quality-adjusted consensus
- Key feature: filter to show only ≥3★ analysts for signal vs. noise separation
- Note: free tier has limited data; premium unlocks full analyst profiles

**3. MarketBeat** (consensus trend)
- URL: `https://www.marketbeat.com/stocks/NASDAQ/<TICKER>/`
- Use for: 3-month consensus trend direction, recent upgrade/downgrade list
- Free: yes

**4. StockAnalysis.com** (EPS revisions)
- URL: `https://stockanalysis.com/stocks/<TICKER>/forecast/`
- Use for: EPS estimate revisions, revenue estimates, analyst count over time
- Free: yes

**5. Benzinga** (news-based analyst actions)
- URL: `https://www.benzinga.com/stock/<TICKER>/analyst-ratings`
- Use for: latest upgrade/downgrade with analyst rationale
- Free: yes

---

### ETF-Specific Sources

**ETF.com** (most comprehensive free ETF data)
- URL: `https://www.etf.com/<TICKER>`
- Use for: expense ratio, tracking difference, AUM, inception date, bid/ask spread
- Tracking difference vs. tracking error: prefer "tracking difference" (actual net cost)

**ETF Database (etfdb.com)**
- URL: `https://etfdb.com/etf/<TICKER>/`
- Use for: category comparison, fund flows, alternatives in same category

**Fund Issuer Sites** (most authoritative)
- Vanguard: `https://investor.vanguard.com/investment-products/etfs/profile/<TICKER>`
- iShares: `https://www.ishares.com/us/products/<TICKER>`
- SPDR: `https://www.ssga.com/us/en/intermediary/etfs/funds/<TICKER>`

---

### Sector & Market Data

**Finviz** (free screener, sector P/E)
- URL: `https://finviz.com/groups.ashx?g=sector&v=120&o=-perf1w`
- Use for: sector P/E comparison, sector performance, quick stock screening
- Screen for: Analyst Reco = Buy + P/E < 20 + ROE > 15%

**Macrotrends** (historical data)
- URL: `https://www.macrotrends.net/stocks/charts/<TICKER>/<COMPANY>/<METRIC>`
- Use for: 10-year historical margins, ROIC trends, ROE history
- Free, excellent for longitudinal analysis

**FRED (Federal Reserve)** (macro data)
- URL: `https://fred.stlouisfed.org`
- Use for: 10-year Treasury rate (for WACC), CPI, GDP growth

---

## Data Priority Order
1. **yfinance** (automated, always try first)
2. **Yahoo Finance website** (manual verification of automated data)
3. **TipRanks** (analyst quality — user's primary source)
4. **ETF.com** (ETF expense ratio, tracking)
5. **SEC EDGAR** (definitive financial statements)
6. **Company IR** (guidance, supplemental data)
7. **Macrotrends** (historical trend data)
8. **Finviz** (screening and sector data)

---

## Labeling Convention
Every metric in the output MUST be labeled with its source:
- `"ROE: 28.4% — Source: Yahoo Finance Statistics tab"`
- `"Expense Ratio: 0.03% — Source: ETF.com (not available via yfinance)"`
- `"Analyst Count: 42 — Source: Yahoo Finance; Quality-adjusted (≥3★): 18 — Source: TipRanks"`
