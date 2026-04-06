#!/usr/bin/env python3
"""
analyze_stock.py — Mode 1 Stock Analysis orchestrator for Strategic Stock Analysis Pilot
Runs the full Buffett analysis pipeline and outputs a structured JSON report.
Usage: python analyze_stock.py <TICKER> [--quick]
"""

import sys
import json
import os
import subprocess
from datetime import datetime


def run_script(script_name: str, ticker: str, script_dir: str) -> dict:
    """Run a sibling script and return its JSON output."""
    result = subprocess.run(
        [sys.executable, os.path.join(script_dir, script_name), ticker],
        capture_output=True,
        text=True,
        timeout=60
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {"error": f"{script_name} failed: {result.stderr[:200]}"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": f"Failed to parse {script_name} output"}


def detect_red_flags(data: dict) -> list:
    """Identify Buffett-style red flags from financial data."""
    flags = []

    # Debt check
    de = data.get("balance_sheet", {}).get("debt_to_equity_ratio")
    if de is not None:
        if de > 1.0:
            flags.append({"severity": "CRITICAL", "flag": f"🔴 Debt/Equity {de:.2f} > 1.0 — high leverage risk"})
        elif de > 0.5:
            flags.append({"severity": "CAUTION", "flag": f"🟡 Debt/Equity {de:.2f} > 0.5 — elevated debt"})

    # FCF check
    fcf = data.get("cash_flow", {}).get("free_cash_flow")
    owner_earnings = data.get("cash_flow", {}).get("owner_earnings")
    if owner_earnings is not None and owner_earnings < 0:
        flags.append({"severity": "CRITICAL", "flag": f"🔴 Negative Owner Earnings ${owner_earnings/1e6:.0f}M — not self-funding"})
    elif fcf is not None and fcf < 0:
        flags.append({"severity": "CRITICAL", "flag": f"🔴 Negative FCF ${fcf/1e6:.0f}M — burning cash"})

    # Share dilution
    shares_change = data.get("ownership", {}).get("shares_change_2yr_pct")
    if shares_change is not None and shares_change > 2:
        flags.append({"severity": "CRITICAL", "flag": f"🔴 Share dilution: +{shares_change}%/2yr — shareholders being diluted"})

    # Margin concern
    op_margin = data.get("profitability", {}).get("operating_margin_pct")
    net_margin = data.get("profitability", {}).get("net_margin_pct")
    if op_margin is not None and op_margin < 5:
        flags.append({"severity": "CAUTION", "flag": f"🟡 Thin operating margin {op_margin}% — vulnerable to cost shocks"})

    # ROE below threshold
    roe = data.get("profitability", {}).get("roe_pct")
    if roe is not None and roe < 10:
        flags.append({"severity": "CAUTION", "flag": f"🟡 ROE {roe}% below Buffett threshold (15%) — limited shareholder value creation"})

    # P/E extremes
    pe = data.get("valuation", {}).get("pe_trailing")
    if pe is not None and pe > 50:
        flags.append({"severity": "CAUTION", "flag": f"🟡 P/E {pe:.0f}x — high valuation requires exceptional growth"})

    return flags


def check_buffett_4_filters(data: dict, moat_result: dict, valuation_result: dict) -> dict:
    """Evaluate Buffett's 4 mandatory filters with explicit PASS/FAIL."""
    filters = {}

    # Filter 1: Enduring competitive advantage (MOAT)
    moat_score = moat_result.get("total_score", 0)
    moat_class = moat_result.get("classification", "NO MOAT")
    if moat_score >= 18:
        filters["enduring_competitive_advantage"] = {
            "result": "PASS", "emoji": "✅",
            "detail": f"MOAT Score {moat_score}/25 — {moat_class}"
        }
    elif moat_score >= 10:
        filters["enduring_competitive_advantage"] = {
            "result": "PARTIAL", "emoji": "⚠️",
            "detail": f"MOAT Score {moat_score}/25 — {moat_class} — monitor for erosion"
        }
    else:
        filters["enduring_competitive_advantage"] = {
            "result": "FAIL", "emoji": "❌",
            "detail": f"MOAT Score {moat_score}/25 — {moat_class} — does not meet Buffett standard"
        }

    # Filter 2: Management quality
    roe = data.get("profitability", {}).get("roe_pct")
    shares_change = data.get("ownership", {}).get("shares_change_2yr_pct")
    insider = data.get("ownership", {}).get("insider_ownership_pct")
    mgmt_score = 0
    mgmt_evidence = []
    if roe and roe >= 15:
        mgmt_score += 1
        mgmt_evidence.append(f"ROE {roe}% ≥ 15%")
    if shares_change is not None and shares_change <= 0:
        mgmt_score += 1
        mgmt_evidence.append(f"No dilution (shares {shares_change:+.1f}%)")
    if insider and insider >= 5:
        mgmt_score += 1
        mgmt_evidence.append(f"Insider ownership {insider}%")

    if mgmt_score >= 2:
        filters["management_quality"] = {
            "result": "PASS", "emoji": "✅",
            "detail": " | ".join(mgmt_evidence) if mgmt_evidence else "Adequate management signals"
        }
    elif mgmt_score == 1:
        filters["management_quality"] = {
            "result": "PARTIAL", "emoji": "⚠️",
            "detail": " | ".join(mgmt_evidence) if mgmt_evidence else "Limited data"
        }
    else:
        filters["management_quality"] = {
            "result": "FAIL", "emoji": "❌",
            "detail": "ROE below threshold, dilution, or low insider ownership"
        }

    # Filter 3: Sensible price (Margin of Safety)
    mos_dcf = valuation_result.get("margin_of_safety_dcf", {})
    mos_graham = valuation_result.get("margin_of_safety_graham", {})
    primary_mos = mos_dcf.get("margin_of_safety_pct") or mos_graham.get("margin_of_safety_pct")

    if primary_mos is not None:
        if primary_mos >= 20:
            filters["sensible_price"] = {
                "result": "PASS", "emoji": "✅",
                "detail": f"Margin of Safety: {primary_mos:.1f}% ≥ 20% Buffett threshold"
            }
        elif primary_mos >= 0:
            filters["sensible_price"] = {
                "result": "PARTIAL", "emoji": "⚠️",
                "detail": f"Margin of Safety: {primary_mos:.1f}% — thin cushion, wait for pullback"
            }
        else:
            filters["sensible_price"] = {
                "result": "FAIL", "emoji": "❌",
                "detail": f"Margin of Safety: {primary_mos:.1f}% — trading above intrinsic value"
            }
    else:
        filters["sensible_price"] = {
            "result": "UNKNOWN", "emoji": "❓",
            "detail": "Insufficient data for valuation — check manually"
        }

    # Filter 4: Generates FCF
    fcf = data.get("cash_flow", {}).get("free_cash_flow")
    owner_earnings = data.get("cash_flow", {}).get("owner_earnings")

    if owner_earnings and owner_earnings > 0:
        filters["generates_fcf"] = {
            "result": "PASS", "emoji": "✅",
            "detail": f"Owner Earnings: ${owner_earnings/1e6:.0f}M positive"
        }
    elif fcf and fcf > 0:
        filters["generates_fcf"] = {
            "result": "PASS", "emoji": "✅",
            "detail": f"FCF: ${fcf/1e6:.0f}M positive"
        }
    else:
        filters["generates_fcf"] = {
            "result": "FAIL", "emoji": "❌",
            "detail": "Negative or unavailable FCF/Owner Earnings"
        }

    # Overall 4-filter result
    results = [v["result"] for v in filters.values()]
    pass_count = results.count("PASS")
    partial_count = results.count("PARTIAL")

    if pass_count >= 3:
        overall = "PASSES BUFFETT CRITERIA"
    elif pass_count + partial_count >= 3:
        overall = "BORDERLINE — FURTHER RESEARCH REQUIRED"
    else:
        overall = "FAILS BUFFETT CRITERIA"

    filters["overall"] = {
        "verdict": overall,
        "pass_count": pass_count,
        "partial_count": partial_count,
        "fail_count": results.count("FAIL"),
    }

    return filters


def generate_analyst_commentary(data: dict, buffett_score: int) -> str:
    """Generate herd mentality / undiscovered gem commentary."""
    rec_mean = data.get("analyst", {}).get("recommendation_mean")
    n_analysts = data.get("analyst", {}).get("number_of_analyst_opinions")

    if rec_mean is None:
        return "Analyst data not available — check TipRanks directly."

    analyst_bullish = rec_mean <= 2.0
    n = n_analysts or 0

    if analyst_bullish and buffett_score < 50:
        return (
            f"⚠️ HERD MENTALITY ALERT: {n} analysts are bullish (consensus {rec_mean:.1f}) "
            f"but Buffett Score is only {buffett_score}/100. "
            "The street may be pricing in growth that isn't supported by fundamentals. "
            "Cross-check on TipRanks — are the bullish analysts high-quality (≥3★)?"
        )
    elif not analyst_bullish and buffett_score >= 65:
        return (
            f"💎 UNDISCOVERED GEM SIGNAL: Buffett Score {buffett_score}/100 is strong, "
            f"but only {n} analysts and consensus is neutral ({rec_mean:.1f}). "
            "Strong fundamentals without Wall Street enthusiasm = potential alpha opportunity. "
            "Verify on TipRanks — what are the high-quality analysts saying?"
        )
    elif n < 5:
        return (
            f"🔍 UNDERFOLLOWED: Only {n} analysts cover this stock. "
            "Low coverage means less institutional awareness — could mean hidden value "
            "or simply a smaller company. Buffett's 'Circle of Competence' applies here."
        )
    else:
        return (
            f"Analyst consensus ({rec_mean:.1f} mean from {n} analysts) "
            f"{'aligns with' if buffett_score >= 50 else 'diverges from'} "
            f"the Buffett Score of {buffett_score}/100. "
            "Verify quality-adjusted consensus on TipRanks (filter for ≥3★ analysts)."
        )


def build_entry_conditions(data: dict) -> dict:
    """Assemble the Market Timing & Entry Conditions section."""
    conditions = {}
    green_count = 0

    # RSI
    rsi = data.get("technical", {}).get("rsi_14")
    if rsi is not None:
        if rsi < 30:
            conditions["rsi"] = {"value": rsi, "signal": "OVERSOLD", "emoji": "🟢", "note": "Mr. Market is scared — potential entry"}
            green_count += 1
        elif rsi > 70:
            conditions["rsi"] = {"value": rsi, "signal": "OVERBOUGHT", "emoji": "🔴", "note": "Wait for pullback even if fundamentals strong"}
        else:
            conditions["rsi"] = {"value": rsi, "signal": "NEUTRAL", "emoji": "🟡", "note": "Normal range"}
    else:
        conditions["rsi"] = {"value": None, "signal": "N/A", "emoji": "⬜"}

    # VIX
    vix = data.get("market", {}).get("vix_current")
    vix_signal = data.get("market", {}).get("vix_signal")
    if vix is not None:
        if vix > 30:
            conditions["vix"] = {"value": vix, "signal": "HIGH FEAR", "emoji": "🟢", "note": "Buffett buying environment — 'Be greedy when others are fearful'"}
            green_count += 1
        elif vix > 25:
            conditions["vix"] = {"value": vix, "signal": "ELEVATED ANXIETY", "emoji": "🟡", "note": "Caution but potential opportunity emerging"}
        elif vix < 15:
            conditions["vix"] = {"value": vix, "signal": "COMPLACENCY", "emoji": "🔴", "note": "Market priced for perfection — less margin of safety available"}
        else:
            conditions["vix"] = {"value": vix, "signal": "NORMAL", "emoji": "🟡", "note": "Average market conditions"}
    else:
        conditions["vix"] = {"value": None, "signal": "N/A", "emoji": "⬜"}

    # 52-week position
    pos_52wk = data.get("price", {}).get("week_52_position_pct")
    if pos_52wk is not None:
        if pos_52wk < 30:
            conditions["week_52_position"] = {"value": f"{pos_52wk}%", "signal": "NEAR LOWS", "emoji": "🟢", "note": "Trading near 52-week low — potential value zone"}
            green_count += 1
        elif pos_52wk > 80:
            conditions["week_52_position"] = {"value": f"{pos_52wk}%", "signal": "NEAR HIGHS", "emoji": "🔴", "note": "Near 52-week high — less margin of safety"}
        else:
            conditions["week_52_position"] = {"value": f"{pos_52wk}%", "signal": "MID-RANGE", "emoji": "🟡", "note": "Neutral position"}
    else:
        conditions["week_52_position"] = {"value": None, "signal": "N/A", "emoji": "⬜"}

    # Earnings proximity
    days_to_earnings = data.get("technical", {}).get("days_to_earnings")
    if days_to_earnings is not None:
        if days_to_earnings < 14:
            conditions["earnings_proximity"] = {
                "value": f"{days_to_earnings} days", "signal": "EARNINGS IMMINENT",
                "emoji": "🔴", "note": "Consider waiting or sizing down — event risk"
            }
        elif days_to_earnings < 30:
            conditions["earnings_proximity"] = {
                "value": f"{days_to_earnings} days", "signal": "APPROACHING",
                "emoji": "🟡", "note": "Earnings within 30 days — be aware of event risk"
            }
        else:
            conditions["earnings_proximity"] = {
                "value": f"{days_to_earnings} days", "signal": "SAFE WINDOW",
                "emoji": "🟢", "note": "Adequate runway before earnings event"
            }
            green_count += 1

    # Momentum context
    mom_3m = data.get("technical", {}).get("momentum_3m_pct")
    if mom_3m is not None:
        conditions["momentum_3m"] = {
            "value": f"{mom_3m:+.1f}%",
            "signal": "UP" if mom_3m > 0 else "DOWN",
            "emoji": "📈" if mom_3m > 5 else ("📉" if mom_3m < -15 else "➡️"),
            "note": "Context only — distinguish value dip vs. fundamental deterioration"
        }

    conditions["summary"] = {
        "green_signals": green_count,
        "total_signals": sum(1 for k, v in conditions.items()
                            if k not in ["summary", "momentum_3m"] and v.get("value") is not None),
        "interpretation": (
            "Strong entry window" if green_count >= 3
            else "Neutral conditions" if green_count >= 1
            else "Unfavorable entry timing"
        )
    }

    return conditions


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: analyze_stock.py <TICKER> [--quick]"}))
        sys.exit(1)

    ticker = sys.argv[1].upper().replace("$", "")
    quick_mode = "--quick" in sys.argv

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Step 1: Fetch all data
    data = run_script("fetch_data.py", ticker, script_dir)
    if "error" in data:
        print(json.dumps({"error": data["error"], "ticker": ticker}))
        sys.exit(1)

    # Verify it's a stock
    quote_type = data.get("basic", {}).get("quote_type", "EQUITY")
    if quote_type == "ETF":
        print(json.dumps({
            "redirect": "ETF detected — run analyze_etf.py instead",
            "ticker": ticker,
            "command": f"python analyze_etf.py {ticker}"
        }))
        sys.exit(0)

    report = {
        "analysis_type": "MODE_1_STOCK",
        "ticker": ticker,
        "name": data.get("basic", {}).get("name"),
        "sector": data.get("basic", {}).get("sector"),
        "industry": data.get("basic", {}).get("industry"),
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "data_source_primary": "Yahoo Finance (yfinance)",
        "quick_mode": quick_mode,
    }

    # Step 2: MOAT scoring
    moat_result = run_script("moat_scorer.py", ticker, script_dir)
    report["moat_analysis"] = moat_result

    # Step 3: Valuation
    val_result = run_script("valuation.py", ticker, script_dir)
    report["valuation"] = val_result

    # Step 4: Red flags
    report["red_flags"] = detect_red_flags(data)

    # Step 5: Buffett 4-filter
    report["buffett_4_filters"] = check_buffett_4_filters(data, moat_result, val_result)

    # Step 6: Entry conditions
    report["entry_conditions"] = build_entry_conditions(data)

    # Step 7: Analyst commentary
    buffett_score = val_result.get("buffett_score", {}).get("total_score", 0)
    report["analyst_commentary"] = generate_analyst_commentary(data, buffett_score)

    # Assemble key metrics for quick summary
    current_price = data.get("price", {}).get("current_price")
    report["quick_summary"] = {
        "ticker": ticker,
        "name": data.get("basic", {}).get("name"),
        "current_price": current_price,
        "currency": data.get("basic", {}).get("currency", "USD"),
        "buffett_score": buffett_score,
        "verdict": val_result.get("buffett_score", {}).get("verdict", "UNKNOWN"),
        "moat": moat_result.get("classification", "UNKNOWN"),
        "moat_score": moat_result.get("total_score", 0),
        "margin_of_safety_pct": (
            val_result.get("margin_of_safety_dcf", {}).get("margin_of_safety_pct")
            or val_result.get("margin_of_safety_graham", {}).get("margin_of_safety_pct")
        ),
        "red_flag_count": len([f for f in report["red_flags"] if f.get("severity") == "CRITICAL"]),
        "entry_signal": report["entry_conditions"].get("summary", {}).get("interpretation"),
        "vix": data.get("market", {}).get("vix_current"),
        "rsi": data.get("technical", {}).get("rsi_14"),
        "roe_pct": data.get("profitability", {}).get("roe_pct"),
        "debt_to_equity": data.get("balance_sheet", {}).get("debt_to_equity_ratio"),
        "gross_margin_pct": data.get("profitability", {}).get("gross_margin_pct"),
        "analyst_count": data.get("analyst", {}).get("number_of_analyst_opinions"),
        "analyst_mean": data.get("analyst", {}).get("recommendation_mean"),
        "target_price_avg": data.get("analyst", {}).get("target_mean_price"),
        "upside_to_target_pct": data.get("analyst", {}).get("upside_to_target_pct"),
    }

    # Full data for deep analysis
    if not quick_mode:
        report["full_data"] = data

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
