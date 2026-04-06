#!/usr/bin/env python3
"""
analyze_etf.py — Mode 1 ETF Efficiency Audit for Strategic Stock Analysis Pilot
Performs the full ETF audit: expense ratio, concentration, moat overlap, sector aggregation.
Usage: python analyze_etf.py <TICKER>
"""

import sys
import json
import os
import subprocess
from datetime import datetime

# Known moat-quality companies for quick overlap check
# These are companies with known Wide/Narrow moats
KNOWN_MOAT_COMPANIES = {
    # Wide Moat (brand, network, switching costs)
    "AAPL", "MSFT", "GOOGL", "GOOG", "META", "V", "MA", "VISA", "MASTERCARD",
    "KO", "PEP", "MCD", "NKE", "SBUX", "COST", "WMT", "JNJ", "UNH",
    "BRK.B", "BRK-B", "BRKB", "JPM", "BAC", "WFC", "GS",
    "AMZN", "NVDA", "AVGO", "TSM", "ASML",
    "NEE", "DUK", "SO",  # Utilities (efficient scale)
    "UNP", "CSX", "NSC",  # Railroads (efficient scale)
    "WM", "RSG",  # Waste Management (efficient scale)
    "MCO", "SPGI", "ICE", "CME",  # Financial data (regulatory moat)
    "LLY", "ABBV", "PFE", "MRK",  # Pharma (patents)
    "PM", "MO",  # Tobacco (brand)
    "MSCI", "NFLX", "ADBE",
}

# GICS Sector mapping keywords
SECTOR_MAP = {
    "Technology": ["software", "tech", "semiconductor", "hardware", "electronic", "it services"],
    "Healthcare": ["health", "pharma", "biotech", "medical", "drug"],
    "Financials": ["bank", "insurance", "financial", "asset management", "investment"],
    "Consumer Discretionary": ["retail", "auto", "leisure", "hotel", "restaurant"],
    "Consumer Staples": ["food", "beverage", "tobacco", "household", "personal"],
    "Industrials": ["industrial", "aerospace", "defense", "machinery", "transportation"],
    "Energy": ["oil", "gas", "energy", "petroleum"],
    "Utilities": ["utility", "utilities", "electric", "water", "gas distribution"],
    "Real Estate": ["reit", "real estate"],
    "Materials": ["chemical", "mining", "metal", "material"],
    "Communication": ["media", "telecom", "communication", "entertainment"],
}


def run_script(script_name: str, ticker: str, script_dir: str) -> dict:
    result = subprocess.run(
        [sys.executable, os.path.join(script_dir, script_name), ticker],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {"error": f"{script_name} failed: {result.stderr[:200]}"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": f"Failed to parse {script_name} output"}


def score_expense_ratio(expense_ratio_pct: float) -> dict:
    if expense_ratio_pct is None:
        return {
            "value": None,
            "score": 25,  # Assume OK if missing
            "rating": "UNKNOWN",
            "emoji": "❓",
            "note": "Expense ratio not available via yfinance — check ETF.com or fund prospectus"
        }
    if expense_ratio_pct <= 0.05:
        return {"value": expense_ratio_pct, "score": 35, "rating": "EXCELLENT", "emoji": "✅✅",
                "note": f"{expense_ratio_pct}% — ultra-low cost (Vanguard/iShares index tier)"}
    elif expense_ratio_pct <= 0.10:
        return {"value": expense_ratio_pct, "score": 30, "rating": "EXCELLENT", "emoji": "✅",
                "note": f"{expense_ratio_pct}% — low cost, Buffett-approved passive range"}
    elif expense_ratio_pct <= 0.25:
        return {"value": expense_ratio_pct, "score": 20, "rating": "ACCEPTABLE", "emoji": "🟡",
                "note": f"{expense_ratio_pct}% — acceptable but adds meaningful drag over 20 years"}
    elif expense_ratio_pct <= 0.50:
        return {"value": expense_ratio_pct, "score": 10, "rating": "HIGH COST", "emoji": "🔴",
                "note": f"{expense_ratio_pct}% — high cost, erodes returns significantly. 20yr cost: ~{expense_ratio_pct*20:.1f}% of portfolio value"}
    else:
        return {"value": expense_ratio_pct, "score": 0, "rating": "AVOID", "emoji": "🔴🔴",
                "note": f"{expense_ratio_pct}% — very high. Active fund territory. Justify with performance."}


def score_aum(total_assets: float) -> dict:
    if total_assets is None:
        return {"value": None, "rating": "UNKNOWN", "emoji": "❓"}
    billions = total_assets / 1e9
    if billions >= 10:
        return {"value": f"${billions:.1f}B", "rating": "EXCELLENT LIQUIDITY", "emoji": "✅",
                "note": "Large AUM — tight bid/ask spread, easy to trade"}
    elif billions >= 1:
        return {"value": f"${billions:.1f}B", "rating": "ADEQUATE LIQUIDITY", "emoji": "🟡",
                "note": "AUM > $1B — meets Buffett minimum for liquidity"}
    elif billions >= 0.1:
        return {"value": f"${billions*1000:.0f}M", "rating": "LOW LIQUIDITY", "emoji": "🔴",
                "note": "AUM < $1B — potential liquidity risk, wider spreads"}
    else:
        return {"value": f"${billions*1000:.0f}M", "rating": "ILLIQUID", "emoji": "🔴🔴",
                "note": "Very small fund — avoid. Closure risk + wide spreads"}


def analyze_etf_holdings(ticker_obj) -> dict:
    """Fetch and analyze top 15 holdings from Yahoo Finance."""
    try:
        funds_data = ticker_obj.funds_data
        if funds_data is None:
            return {"error": "Holdings data not available via yfinance for this ETF"}

        top_holdings = getattr(funds_data, 'top_holdings', None)
        sector_weightings = getattr(funds_data, 'sector_weightings', None)

        result = {
            "top_holdings": [],
            "sector_breakdown": {},
            "concentration_analysis": {},
            "moat_overlap": {},
        }

        # Process top holdings
        if top_holdings is not None and not top_holdings.empty:
            holdings_list = []
            total_top15_weight = 0

            for i, (symbol, row) in enumerate(top_holdings.iterrows()):
                if i >= 15:
                    break
                weight = float(row.get('Holding Percent', 0)) * 100 if 'Holding Percent' in row else None
                name = row.get('Name', symbol) if hasattr(row, 'get') else symbol
                holdings_list.append({
                    "rank": i + 1,
                    "ticker": str(symbol),
                    "name": str(name),
                    "weight_pct": round(weight, 2) if weight else None,
                    "has_moat": str(symbol).upper() in KNOWN_MOAT_COMPANIES
                })
                if weight:
                    total_top15_weight += weight

            result["top_holdings"] = holdings_list

            # Concentration analysis
            moat_count = sum(1 for h in holdings_list if h.get("has_moat"))
            top2_weight = sum(h.get("weight_pct", 0) or 0 for h in holdings_list[:2])

            result["concentration_analysis"] = {
                "top_15_combined_weight_pct": round(total_top15_weight, 1),
                "top_2_weight_pct": round(top2_weight, 1),
                "is_top_heavy": total_top15_weight > 50,
                "top_heavy_flag": "🔴 TOP-HEAVY: Top 15 holdings > 50% of fund" if total_top15_weight > 50
                                  else ("🟡 MODERATE: Top 15 holdings 40-50% of fund" if total_top15_weight > 40
                                        else "✅ DIVERSIFIED: Top 15 < 40% of fund"),
                "top_pair_risk": f"🔴 Top 2 holdings = {top2_weight:.1f}% combined weight" if top2_weight > 10
                                  else f"✅ Top 2 holdings = {top2_weight:.1f}% (manageable)"
            }

            # Moat overlap analysis
            result["moat_overlap"] = {
                "moat_companies_in_top15": moat_count,
                "total_checked": len(holdings_list),
                "moat_quality_score": f"{moat_count}/{len(holdings_list)} top holdings pass basic MOAT check",
                "quality_rating": (
                    "✅ HIGH QUALITY — Majority of top holdings are moat companies"
                    if moat_count >= 10
                    else "🟡 MODERATE — Some moat companies but also non-moat exposure"
                    if moat_count >= 5
                    else "🔴 LOW QUALITY — Few recognizable moat companies in top 15"
                ),
                "note": "Based on known wide/narrow moat companies list. Manual verification recommended for unlisted companies."
            }

        # Process sector weightings
        if sector_weightings is not None:
            sectors = {}
            if isinstance(sector_weightings, list):
                for item in sector_weightings:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            sectors[k] = round(float(v) * 100, 1)
            elif hasattr(sector_weightings, 'to_dict'):
                raw = sector_weightings.to_dict()
                for k, v in raw.items():
                    sectors[k] = round(float(v) * 100, 1)

            result["sector_breakdown"] = sectors

            # Sector concentration check
            if sectors:
                sorted_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
                top_sector = sorted_sectors[0] if sorted_sectors else None
                num_sectors = len([s for s in sectors.values() if s > 3])  # sectors with >3% weight

                result["sector_concentration"] = {
                    "dominant_sector": top_sector[0] if top_sector else "Unknown",
                    "dominant_sector_pct": top_sector[1] if top_sector else 0,
                    "meaningful_sectors": num_sectors,
                    "diversification_check": (
                        "✅ WELL DIVERSIFIED — 4+ meaningful sectors" if num_sectors >= 4
                        else "🟡 LIMITED DIVERSIFICATION — 3 sectors" if num_sectors >= 3
                        else "🔴 CONCENTRATED — Only 1-2 meaningful sectors (single-sector trap)"
                    ),
                    "single_sector_trap": top_sector[1] > 50 if top_sector else False
                }

        return result

    except Exception as e:
        return {"error": f"Holdings analysis failed: {str(e)}", "note": "Check Yahoo Finance Holdings tab manually"}


def compute_etf_buffett_score(expense_data: dict, aum_data: dict, holdings_data: dict,
                               tracking_error: float = None, beta: float = None) -> dict:
    """Compute ETF Buffett Score (0-100) with three components."""

    # Component 1: Efficiency (35 pts max)
    efficiency_score = 0

    # Expense ratio (20 pts)
    expense_score = expense_data.get("score", 20)
    efficiency_score += min(20, expense_score * 20 // 35)

    # Tracking error (8 pts)
    if tracking_error is not None:
        if tracking_error < 0.10:
            efficiency_score += 8
        elif tracking_error < 0.20:
            efficiency_score += 6
        elif tracking_error < 0.50:
            efficiency_score += 3
    else:
        efficiency_score += 5  # assume OK if not available

    # AUM (7 pts)
    aum_rating = aum_data.get("rating", "")
    if "EXCELLENT" in aum_rating:
        efficiency_score += 7
    elif "ADEQUATE" in aum_rating:
        efficiency_score += 5
    elif "LOW" in aum_rating:
        efficiency_score += 2

    efficiency_score = min(35, efficiency_score)

    # Component 2: Diversification Quality (35 pts max)
    div_score = 0

    conc = holdings_data.get("concentration_analysis", {})
    if not holdings_data.get("error"):
        top15_weight = conc.get("top_15_combined_weight_pct", 50)
        if top15_weight <= 30:
            div_score += 15
        elif top15_weight <= 40:
            div_score += 10
        elif top15_weight <= 50:
            div_score += 5
        else:
            div_score += 0

        # Moat overlap
        moat_overlap = holdings_data.get("moat_overlap", {})
        moat_count = moat_overlap.get("moat_companies_in_top15", 0)
        total = moat_overlap.get("total_checked", 15)
        if total > 0:
            moat_pct = moat_count / total
            div_score += int(moat_pct * 12)

        # Sector diversification
        sector_conc = holdings_data.get("sector_concentration", {})
        meaningful_sectors = sector_conc.get("meaningful_sectors", 3)
        if meaningful_sectors >= 5:
            div_score += 8
        elif meaningful_sectors >= 4:
            div_score += 6
        elif meaningful_sectors >= 3:
            div_score += 4
        else:
            div_score += 0
    else:
        div_score = 18  # default if no data

    div_score = min(35, div_score)

    # Component 3: Factor Value (30 pts max)
    # Can't easily get P/E vs S&P comparison without more data
    # Award based on what we know
    factor_score = 15  # neutral default

    total = efficiency_score + div_score + factor_score

    if total >= 80:
        verdict, bucket = "STRONG CORE HOLD", "Bucket A — Excellent Core ETF"
    elif total >= 65:
        verdict, bucket = "GOOD CORE HOLD", "Bucket A — Good Core ETF"
    elif total >= 50:
        verdict, bucket = "ACCEPTABLE", "Bucket A/B — Acceptable with caveats"
    elif total >= 35:
        verdict, bucket = "CAUTION", "Bucket B Satellite only — high cost or concentration"
    else:
        verdict, bucket = "AVOID", "Not suitable for Core or Satellite"

    return {
        "total_score": total,
        "verdict": verdict,
        "bucket_recommendation": bucket,
        "components": {
            "efficiency": {"score": efficiency_score, "max": 35},
            "diversification_quality": {"score": div_score, "max": 35},
            "factor_value": {"score": factor_score, "max": 30, "note": "Check P/E vs. S&P 500 on Yahoo Finance"}
        }
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: analyze_etf.py <TICKER>"}))
        sys.exit(1)

    ticker_symbol = sys.argv[1].upper().replace("$", "")
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Fetch data
    data = run_script("fetch_data.py", ticker_symbol, script_dir)
    if "error" in data:
        print(json.dumps({"error": data["error"], "ticker": ticker_symbol}))
        sys.exit(1)

    import yfinance as yf
    ticker_obj = yf.Ticker(ticker_symbol)
    info = ticker_obj.info or {}

    # Check if it's actually an ETF
    quote_type = data.get("basic", {}).get("quote_type", "")
    if quote_type == "EQUITY":
        print(json.dumps({
            "redirect": "This appears to be a stock — run analyze_stock.py instead",
            "ticker": ticker_symbol,
            "command": f"python analyze_stock.py {ticker_symbol}"
        }))
        sys.exit(0)

    report = {
        "analysis_type": "MODE_1_ETF",
        "ticker": ticker_symbol,
        "name": data.get("basic", {}).get("name"),
        "category": info.get("category"),
        "fund_family": info.get("fundFamily"),
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "data_source": "Yahoo Finance (yfinance)",
    }

    # Expense ratio
    expense_ratio = data.get("etf", {}).get("expense_ratio_pct")
    # Try alternative field
    if expense_ratio is None:
        expense_ratio = info.get("annualReportExpenseRatio")
        if expense_ratio:
            expense_ratio = round(expense_ratio * 100, 3)

    expense_analysis = score_expense_ratio(expense_ratio)
    report["expense_ratio"] = expense_analysis

    # AUM
    total_assets = data.get("etf", {}).get("total_assets") or info.get("totalAssets")
    report["aum"] = score_aum(total_assets)

    # Tracking error & beta
    beta = data.get("price", {}).get("beta")
    report["beta"] = {
        "value": beta,
        "interpretation": (
            "DEFENSIVE (< 1.0 — less volatile than market)" if beta and beta < 1.0
            else "AGGRESSIVE (> 1.0 — amplifies market moves)" if beta and beta > 1.0
            else "NEUTRAL" if beta and abs(beta - 1.0) < 0.1
            else "Unknown"
        )
    }

    # Note: yfinance doesn't provide tracking error directly — flag for manual check
    report["tracking_error"] = {
        "value": None,
        "note": "Tracking error not available via yfinance — check ETF.com or fund prospectus. Target: < 0.20%"
    }

    # Returns performance
    report["performance"] = {
        "ytd_return_pct": data.get("etf", {}).get("ytd_return_pct"),
        "3yr_avg_return_pct": data.get("etf", {}).get("3yr_return_pct"),
        "5yr_avg_return_pct": data.get("etf", {}).get("5yr_return_pct"),
    }

    # Holdings analysis (Top 15 Test, Moat Overlap, Sector Aggregation)
    holdings_analysis = analyze_etf_holdings(ticker_obj)
    report["holdings_analysis"] = holdings_analysis

    # Factor tilt
    pe = data.get("valuation", {}).get("pe_trailing")
    pb = data.get("valuation", {}).get("price_to_book")
    div_yield = data.get("per_share", {}).get("dividend_yield_pct")
    report["factor_tilt"] = {
        "pe_ratio": pe,
        "price_to_book": pb,
        "dividend_yield_pct": div_yield,
        "note": (
            "Compare these to S&P 500 (P/E ~22x, P/B ~4x, Yield ~1.5%) to identify factor tilt. "
            "Lower P/E = Value tilt. Higher yield = Income tilt."
        ),
        "sp500_benchmarks": {"pe": 22, "pb": 4.0, "yield": 1.5},
        "value_tilt": pe < 20 if pe else None,
        "income_tilt": div_yield > 2.5 if div_yield else None,
    }

    # ETF classification
    etf_buffett_score = compute_etf_buffett_score(
        expense_analysis, report["aum"], holdings_analysis,
        tracking_error=None, beta=beta
    )
    report["etf_buffett_score"] = etf_buffett_score

    # Quick summary
    report["quick_summary"] = {
        "ticker": ticker_symbol,
        "name": data.get("basic", {}).get("name"),
        "buffett_score": etf_buffett_score["total_score"],
        "verdict": etf_buffett_score["verdict"],
        "bucket_recommendation": etf_buffett_score["bucket_recommendation"],
        "expense_ratio_pct": expense_ratio,
        "expense_rating": expense_analysis.get("rating"),
        "aum": report["aum"].get("value"),
        "aum_rating": report["aum"].get("rating"),
        "beta": beta,
        "top15_weight_pct": holdings_analysis.get("concentration_analysis", {}).get("top_15_combined_weight_pct"),
        "moat_in_top15": holdings_analysis.get("moat_overlap", {}).get("moat_companies_in_top15"),
        "dominant_sector": holdings_analysis.get("sector_concentration", {}).get("dominant_sector"),
        "meaningful_sectors": holdings_analysis.get("sector_concentration", {}).get("meaningful_sectors"),
    }

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
