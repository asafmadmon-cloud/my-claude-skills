#!/usr/bin/env python3
"""
fetch_data.py — Yahoo Finance data fetcher for Strategic Stock Analysis Pilot
Fetches all available metrics for a given ticker and outputs structured JSON.
Usage: python fetch_data.py <TICKER>
"""

import sys
import json
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    print(json.dumps({"error": "yfinance not installed. Run: pip install yfinance"}))
    sys.exit(1)


def safe_get(d, *keys):
    """Safely navigate nested dict/object, return None if missing."""
    val = d
    for k in keys:
        if val is None:
            return None
        if isinstance(val, dict):
            val = val.get(k)
        else:
            val = getattr(val, k, None)
    return val


def pct(val):
    """Convert decimal to percentage string, or return None."""
    if val is None:
        return None
    return round(val * 100, 2)


def fetch_stock_data(ticker_symbol: str) -> dict:
    """Fetch comprehensive data for a stock or ETF ticker."""
    ticker = yf.Ticker(ticker_symbol.upper().replace("$", ""))
    info = ticker.info or {}

    quote_type = info.get("quoteType", "EQUITY")

    # --- Basic Info ---
    basic = {
        "ticker": ticker_symbol.upper().replace("$", ""),
        "name": info.get("longName") or info.get("shortName"),
        "quote_type": quote_type,  # EQUITY or ETF
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "currency": info.get("currency", "USD"),
        "exchange": info.get("exchange"),
        "website": info.get("website"),
        "description": (info.get("longBusinessSummary") or "")[:500],
        "fetch_date": datetime.now().strftime("%Y-%m-%d"),
    }

    # --- Price & Market Data ---
    price = {
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "previous_close": info.get("previousClose"),
        "open": info.get("open"),
        "day_low": info.get("dayLow"),
        "day_high": info.get("dayHigh"),
        "week_52_low": info.get("fiftyTwoWeekLow"),
        "week_52_high": info.get("fiftyTwoWeekHigh"),
        "market_cap": info.get("marketCap"),
        "enterprise_value": info.get("enterpriseValue"),
        "beta": info.get("beta"),
        "volume": info.get("volume"),
        "avg_volume": info.get("averageVolume"),
    }

    # Calculate 52-week position (0-100%)
    w52_low = price["week_52_low"]
    w52_high = price["week_52_high"]
    curr = price["current_price"]
    if w52_low and w52_high and curr and (w52_high - w52_low) > 0:
        price["week_52_position_pct"] = round(
            (curr - w52_low) / (w52_high - w52_low) * 100, 1
        )
    else:
        price["week_52_position_pct"] = None

    # --- Valuation Multiples ---
    valuation = {
        "pe_trailing": info.get("trailingPE"),
        "pe_forward": info.get("forwardPE"),
        "peg_ratio": info.get("pegRatio"),
        "price_to_book": info.get("priceToBook"),
        "price_to_sales": info.get("priceToSalesTrailing12Months"),
        "ev_to_ebitda": info.get("enterpriseToEbitda"),
        "ev_to_revenue": info.get("enterpriseToRevenue"),
    }

    # --- Profitability & Margins ---
    profitability = {
        "gross_margin_pct": pct(info.get("grossMargins")),
        "operating_margin_pct": pct(info.get("operatingMargins")),
        "net_margin_pct": pct(info.get("profitMargins")),
        "roe_pct": pct(info.get("returnOnEquity")),
        "roa_pct": pct(info.get("returnOnAssets")),
        "ebitda": info.get("ebitda"),
        "ebitda_margin_pct": pct(info.get("ebitdaMargins")),
    }

    # --- Balance Sheet & Debt ---
    balance_sheet = {
        "total_cash": info.get("totalCash"),
        "total_debt": info.get("totalDebt"),
        "debt_to_equity": info.get("debtToEquity"),  # Yahoo gives as % (e.g., 50 = 0.5x)
        "current_ratio": info.get("currentRatio"),
        "quick_ratio": info.get("quickRatio"),
        "book_value_per_share": info.get("bookValue"),
        "total_assets": info.get("totalAssets") if "totalAssets" in info else None,
    }

    # Normalize debt_to_equity (Yahoo gives as %, convert to ratio)
    if balance_sheet["debt_to_equity"] is not None:
        balance_sheet["debt_to_equity_ratio"] = round(
            balance_sheet["debt_to_equity"] / 100, 3
        )
    else:
        balance_sheet["debt_to_equity_ratio"] = None

    # --- Cash Flow & Owner Earnings ---
    cash_flow = {
        "operating_cash_flow": info.get("operatingCashflow"),
        "free_cash_flow": info.get("freeCashflow"),
        "capital_expenditures": None,  # Will compute below
        "net_income": info.get("netIncomeToCommon"),
        "revenue": info.get("totalRevenue"),
        "revenue_growth_pct": pct(info.get("revenueGrowth")),
        "earnings_growth_pct": pct(info.get("earningsGrowth")),
    }

    # Try to get CapEx from cashflow statement
    try:
        cf_stmt = ticker.cashflow
        if cf_stmt is not None and not cf_stmt.empty:
            capex_row = None
            for idx in cf_stmt.index:
                if "capital" in str(idx).lower() and "expenditure" in str(idx).lower():
                    capex_row = idx
                    break
            if capex_row:
                cash_flow["capital_expenditures"] = int(cf_stmt.loc[capex_row].iloc[0])
    except Exception:
        pass

    # Try to get D&A
    cash_flow["depreciation_amortization"] = None
    try:
        cf_stmt = ticker.cashflow
        if cf_stmt is not None and not cf_stmt.empty:
            for idx in cf_stmt.index:
                if "depreciation" in str(idx).lower():
                    cash_flow["depreciation_amortization"] = int(cf_stmt.loc[idx].iloc[0])
                    break
    except Exception:
        pass

    # Calculate Owner Earnings if we have the components
    net_inc = cash_flow["net_income"]
    da = cash_flow["depreciation_amortization"]
    capex = cash_flow["capital_expenditures"]

    if net_inc is not None and da is not None and capex is not None:
        # CapEx from Yahoo is usually negative, so we add it
        cash_flow["owner_earnings"] = net_inc + da + capex  # capex is negative in statements
        mktcap = price["market_cap"]
        if mktcap and mktcap > 0:
            cash_flow["owner_earnings_yield_pct"] = round(
                cash_flow["owner_earnings"] / mktcap * 100, 2
            )
        else:
            cash_flow["owner_earnings_yield_pct"] = None
    else:
        cash_flow["owner_earnings"] = None
        cash_flow["owner_earnings_yield_pct"] = None

    # --- Per Share Data ---
    per_share = {
        "eps_trailing": info.get("trailingEps"),
        "eps_forward": info.get("forwardEps"),
        "dividend_per_share": info.get("dividendRate"),
        "dividend_yield_pct": pct(info.get("dividendYield")),
        "payout_ratio_pct": pct(info.get("payoutRatio")),
        "shares_outstanding": info.get("sharesOutstanding"),
        "shares_float": info.get("floatShares"),
        "shares_short_pct": pct(info.get("shortPercentOfFloat")),
    }

    # --- Analyst Data ---
    analyst = {
        "recommendation_mean": info.get("recommendationMean"),  # 1=Strong Buy, 5=Sell
        "recommendation_key": info.get("recommendationKey"),
        "number_of_analyst_opinions": info.get("numberOfAnalystOpinions"),
        "target_mean_price": info.get("targetMeanPrice"),
        "target_high_price": info.get("targetHighPrice"),
        "target_low_price": info.get("targetLowPrice"),
        "target_median_price": info.get("targetMedianPrice"),
    }

    # Calculate upside/downside to target
    if analyst["target_mean_price"] and price["current_price"]:
        analyst["upside_to_target_pct"] = round(
            (analyst["target_mean_price"] - price["current_price"])
            / price["current_price"]
            * 100,
            1,
        )

    # Try to get analyst upgrade/downgrade history
    try:
        upgrades = ticker.upgrades_downgrades
        if upgrades is not None and not upgrades.empty:
            recent = upgrades.head(5).to_dict("records")
            analyst["recent_analyst_actions"] = recent
    except Exception:
        analyst["recent_analyst_actions"] = []

    # --- Growth Estimates ---
    growth = {
        "revenue_growth_ttm_pct": pct(info.get("revenueGrowth")),
        "earnings_growth_ttm_pct": pct(info.get("earningsGrowth")),
        "earnings_quarterly_growth_pct": pct(info.get("earningsQuarterlyGrowth")),
    }

    # Try to get analyst growth estimates
    try:
        estimates = ticker.growth_estimates
        if estimates is not None and not estimates.empty:
            # Get next 5 years estimate if available
            if "+5y" in estimates.index:
                growth["analyst_5yr_growth_pct"] = round(
                    float(estimates.loc["+5y"].iloc[0]) * 100, 1
                )
            if "+1y" in estimates.index:
                growth["analyst_1yr_growth_pct"] = round(
                    float(estimates.loc["+1y"].iloc[0]) * 100, 1
                )
    except Exception:
        pass

    # --- Insider & Institutional ---
    ownership = {
        "insider_ownership_pct": pct(info.get("heldPercentInsiders")),
        "institutional_ownership_pct": pct(info.get("heldPercentInstitutions")),
    }

    # Try to get shares buyback trend (compare recent quarters)
    try:
        bs = ticker.quarterly_balance_sheet
        if bs is not None and not bs.empty:
            shares_rows = [i for i in bs.index if "share" in str(i).lower() and "outstanding" in str(i).lower()]
            if shares_rows and len(bs.columns) >= 2:
                row = shares_rows[0]
                recent_shares = bs.loc[row].iloc[0]
                older_shares = bs.loc[row].iloc[-1]
                if recent_shares and older_shares and older_shares > 0:
                    ownership["shares_change_2yr_pct"] = round(
                        (recent_shares - older_shares) / older_shares * 100, 1
                    )
    except Exception:
        pass

    # --- Technical Indicators ---
    technical = {
        "ma_50": info.get("fiftyDayAverage"),
        "ma_200": info.get("twoHundredDayAverage"),
    }

    # Calculate RSI from price history
    try:
        hist = ticker.history(period="3mo")
        if hist is not None and len(hist) >= 15:
            delta = hist["Close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(14).mean().iloc[-1]
            avg_loss = loss.rolling(14).mean().iloc[-1]
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                technical["rsi_14"] = round(100 - (100 / (1 + rs)), 1)
            else:
                technical["rsi_14"] = 100.0

            # Price momentum
            if len(hist) >= 63:  # ~3 months
                technical["momentum_3m_pct"] = round(
                    (hist["Close"].iloc[-1] - hist["Close"].iloc[-63])
                    / hist["Close"].iloc[-63]
                    * 100,
                    1,
                )
            if len(hist) >= 126:  # ~6 months
                technical["momentum_6m_pct"] = round(
                    (hist["Close"].iloc[-1] - hist["Close"].iloc[-126])
                    / hist["Close"].iloc[-126]
                    * 100,
                    1,
                )
    except Exception:
        pass

    # Get next earnings date
    try:
        cal = ticker.calendar
        if cal is not None and not cal.empty:
            from datetime import date
            next_earnings = cal.get("Earnings Date", [None])[0] if isinstance(cal, dict) else None
            if next_earnings:
                technical["next_earnings_date"] = str(next_earnings)[:10]
                from datetime import datetime as dt
                days_to_earnings = (dt.strptime(str(next_earnings)[:10], "%Y-%m-%d") - dt.now()).days
                technical["days_to_earnings"] = max(0, days_to_earnings)
    except Exception:
        pass

    # --- ETF-Specific Data ---
    etf_data = {}
    if quote_type == "ETF":
        etf_data = {
            "expense_ratio_pct": None,  # Not always in yfinance info
            "nav": info.get("navPrice"),
            "total_assets": info.get("totalAssets"),
            "category": info.get("category"),
            "fund_family": info.get("fundFamily"),
            "ytd_return_pct": pct(info.get("ytdReturn")),
            "3yr_return_pct": pct(info.get("threeYearAverageReturn")),
            "5yr_return_pct": pct(info.get("fiveYearAverageReturn")),
        }

        # Try to get holdings
        try:
            holdings = ticker.funds_data
            if holdings:
                etf_data["top_holdings_available"] = True
        except Exception:
            etf_data["top_holdings_available"] = False

        # Try expense ratio from info
        if "annualReportExpenseRatio" in info:
            etf_data["expense_ratio_pct"] = pct(info["annualReportExpenseRatio"])

    # --- VIX (Market Fear) ---
    vix_data = {}
    try:
        vix = yf.Ticker("^VIX")
        vix_info = vix.history(period="1d")
        if not vix_info.empty:
            vix_data["vix_current"] = round(float(vix_info["Close"].iloc[-1]), 2)
            if vix_data["vix_current"] > 30:
                vix_data["vix_signal"] = "HIGH_FEAR"
            elif vix_data["vix_current"] > 25:
                vix_data["vix_signal"] = "ELEVATED"
            elif vix_data["vix_current"] > 15:
                vix_data["vix_signal"] = "NORMAL"
            else:
                vix_data["vix_signal"] = "COMPLACENCY"
    except Exception:
        pass

    # Assemble full output
    output = {
        "basic": basic,
        "price": price,
        "valuation": valuation,
        "profitability": profitability,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
        "per_share": per_share,
        "analyst": analyst,
        "growth": growth,
        "ownership": ownership,
        "technical": technical,
        "market": vix_data,
    }

    if quote_type == "ETF":
        output["etf"] = etf_data

    # Add data quality flags
    missing_fields = []
    critical_fields = [
        ("cash_flow", "net_income"),
        ("cash_flow", "free_cash_flow"),
        ("profitability", "roe_pct"),
        ("balance_sheet", "debt_to_equity_ratio"),
        ("per_share", "eps_trailing"),
        ("per_share", "book_value_per_share"),
    ]
    for section, field in critical_fields:
        if output[section].get(field) is None:
            missing_fields.append(f"{section}.{field}")

    output["data_quality"] = {
        "missing_critical_fields": missing_fields,
        "fallback_required": len(missing_fields) > 0,
        "fallback_sources": "See references/data_sources.md for fallback lookup paths",
    }

    return output


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: fetch_data.py <TICKER>"}))
        sys.exit(1)

    ticker = sys.argv[1]
    try:
        data = fetch_stock_data(ticker)
        print(json.dumps(data, indent=2, default=str))
    except Exception as e:
        print(json.dumps({"error": str(e), "ticker": ticker}))
        sys.exit(1)


if __name__ == "__main__":
    main()
