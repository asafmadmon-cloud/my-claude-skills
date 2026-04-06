#!/usr/bin/env python3
"""
valuation.py — Intrinsic value calculator for Strategic Stock Analysis Pilot
Implements: Owner Earnings DCF, Graham Number, Margin of Safety, Buffett Score.
Usage: python valuation.py <TICKER>
"""

import sys
import json
import math
import os
import subprocess


DISCOUNT_RATE = 0.10       # 10% discount rate (Buffett's hurdle rate)
TERMINAL_GROWTH = 0.03     # 3% terminal growth rate (GDP-level perpetuity)
DCF_YEARS = 10             # 10-year projection horizon


def owner_earnings_dcf(owner_earnings: float, growth_rate: float,
                        discount_rate: float = DISCOUNT_RATE,
                        terminal_growth: float = TERMINAL_GROWTH,
                        years: int = DCF_YEARS) -> dict:
    """
    Buffett's Owner Earnings DCF.
    Projects owner earnings for N years, discounts back, adds terminal value.
    """
    if owner_earnings <= 0:
        return {"error": "Owner earnings must be positive for DCF"}

    # Clamp growth rates to realistic bounds
    g = max(min(growth_rate, 0.25), -0.05)  # Cap at 25%, floor at -5%

    # Conservative, base, and optimistic scenarios
    scenarios = {
        "conservative": max(g * 0.6, 0.01),
        "base": g,
        "optimistic": min(g * 1.4, 0.25),
    }

    results = {}
    for scenario_name, growth in scenarios.items():
        pv_sum = 0
        projected_oe = owner_earnings

        for year in range(1, years + 1):
            projected_oe *= (1 + growth)
            pv = projected_oe / ((1 + discount_rate) ** year)
            pv_sum += pv

        # Terminal value (Gordon Growth Model)
        terminal_oe = projected_oe * (1 + terminal_growth)
        terminal_value = terminal_oe / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / ((1 + discount_rate) ** years)

        total_intrinsic_value = pv_sum + pv_terminal

        results[scenario_name] = {
            "growth_rate_used": round(growth * 100, 1),
            "pv_of_earnings": round(pv_sum),
            "pv_of_terminal_value": round(pv_terminal),
            "total_intrinsic_value": round(total_intrinsic_value),
        }

    return results


def graham_number(eps: float, bvps: float) -> dict:
    """
    Graham Number: √(22.5 × EPS × BVPS)
    Represents the upper limit of price a defensive investor should pay.
    Only valid when both EPS and BVPS are positive.
    """
    if eps is None or bvps is None:
        return {"error": "EPS and BVPS required for Graham Number"}
    if eps <= 0:
        return {"error": f"Graham Number requires positive EPS (got {eps})"}
    if bvps <= 0:
        return {"error": f"Graham Number requires positive BVPS (got {bvps})"}

    graham = math.sqrt(22.5 * eps * bvps)
    return {
        "graham_number": round(graham, 2),
        "formula": f"√(22.5 × {eps} EPS × {bvps} BVPS)",
        "note": "Graham Number is a conservative ceiling. Prefer buying at 20-30% below.",
    }


def margin_of_safety(intrinsic_value: float, current_price: float) -> dict:
    """
    Margin of Safety = (Intrinsic Value - Current Price) / Intrinsic Value
    Buffett requires minimum 20-25% margin of safety.
    """
    if intrinsic_value <= 0:
        return {"error": "Intrinsic value must be positive"}
    if current_price is None or current_price <= 0:
        return {"error": "Valid current price required"}

    mos = (intrinsic_value - current_price) / intrinsic_value
    mos_pct = round(mos * 100, 1)

    if mos_pct >= 40:
        signal = "DEEP VALUE — Strong margin of safety (Buffett zone)"
        valuation_label = "Significantly Undervalued"
    elif mos_pct >= 20:
        signal = "UNDERVALUED — Adequate margin of safety"
        valuation_label = "Undervalued"
    elif mos_pct >= 0:
        signal = "FAIRLY VALUED — Thin margin of safety, wait for pullback"
        valuation_label = "Fair Value"
    elif mos_pct >= -20:
        signal = "SLIGHTLY OVERVALUED — Premium to intrinsic value"
        valuation_label = "Slightly Overvalued"
    else:
        signal = "OVERVALUED — Significant premium, avoid unless exceptional growth"
        valuation_label = "Overvalued"

    return {
        "margin_of_safety_pct": mos_pct,
        "intrinsic_value": round(intrinsic_value, 2),
        "current_price": round(current_price, 2),
        "signal": signal,
        "valuation_label": valuation_label,
        "upside_downside_pct": round((intrinsic_value - current_price) / current_price * 100, 1),
    }


def estimate_roic(data: dict) -> dict:
    """
    ROIC = NOPAT / (Total Debt + Total Equity)
    NOPAT = Operating Income × (1 - Tax Rate)
    """
    ebitda = data.get("profitability", {}).get("ebitda")
    op_margin = data.get("profitability", {}).get("operating_margin_pct")
    revenue = data.get("cash_flow", {}).get("revenue")
    total_debt = data.get("balance_sheet", {}).get("total_debt")
    market_cap = data.get("price", {}).get("market_cap")
    net_income = data.get("cash_flow", {}).get("net_income")

    if not all([op_margin, revenue, market_cap]):
        return {"error": "Insufficient data for ROIC calculation"}

    # Approximate NOPAT: Operating Income × (1 - 0.21 federal tax rate approximation)
    operating_income = revenue * op_margin / 100
    nopat = operating_income * (1 - 0.21)

    # Invested capital = Total Debt + Book Equity (NOT market cap — that distorts ROIC)
    # Use stockholders equity (book value). If negative due to buybacks, use total assets.
    book_equity = data.get("balance_sheet", {}).get("total_stockholder_equity")
    total_assets = data.get("balance_sheet", {}).get("total_assets")

    if book_equity is not None and book_equity > 0:
        total_invested = (total_debt or 0) + book_equity
        denominator_note = f"book equity ${book_equity/1e9:.1f}B + debt ${(total_debt or 0)/1e9:.1f}B"
    elif total_assets and total_assets > 0:
        # Fallback: use total assets (common for buyback-heavy companies with negative book equity)
        current_liabilities = data.get("balance_sheet", {}).get("current_liabilities", 0) or 0
        total_invested = total_assets - current_liabilities
        denominator_note = f"total assets - current liabilities (book equity negative due to buybacks)"
    else:
        # Last resort: use revenue as a rough scale proxy
        total_invested = revenue
        denominator_note = "revenue (balance sheet data unavailable)"

    if total_invested <= 0:
        return {"error": "Cannot calculate ROIC: invested capital is zero or negative"}

    roic = nopat / total_invested * 100

    # WACC estimation (simplified: Risk-Free Rate + Beta × Equity Risk Premium)
    beta = data.get("price", {}).get("beta") or 1.0
    risk_free_rate = 4.5  # Approximate 10-yr US Treasury yield as of 2026
    equity_risk_premium = 5.5  # Historical ERP
    cost_of_equity = risk_free_rate + beta * equity_risk_premium

    # Simple WACC (assume 30% debt at 5% cost if debt exists)
    if total_debt and total_debt > 0:
        debt_pct = total_debt / total_invested
        eq_pct = 1 - debt_pct
        wacc = eq_pct * cost_of_equity + debt_pct * 5.0 * (1 - 0.21)
    else:
        wacc = cost_of_equity

    roic_vs_wacc_spread = round(roic - wacc, 1)

    return {
        "roic_pct": round(roic, 1),
        "wacc_pct": round(wacc, 1),
        "spread_pct": roic_vs_wacc_spread,
        "signal": "VALUE CREATING" if roic_vs_wacc_spread > 0 else "VALUE DESTROYING",
        "note": f"ROIC ({roic:.1f}%) {'>' if roic > wacc else '<'} WACC ({wacc:.1f}%) — {'positive' if roic > wacc else 'negative'} economic profit",
    }


def score_fundamentals(data: dict) -> dict:
    """Score fundamentals component for Buffett Score (0-25)."""
    score = 0
    components = []

    # ROE (5 pts max)
    roe = data.get("profitability", {}).get("roe_pct")
    if roe is not None:
        if roe >= 20:
            score += 5; components.append(f"ROE {roe}% ≥ 20% (+5)")
        elif roe >= 15:
            score += 4; components.append(f"ROE {roe}% ≥ 15% (+4)")
        elif roe >= 10:
            score += 2; components.append(f"ROE {roe}% ≥ 10% (+2)")
        else:
            components.append(f"ROE {roe}% < 10% (+0)")

    # Debt/Equity (5 pts max)
    de = data.get("balance_sheet", {}).get("debt_to_equity_ratio")
    if de is not None:
        if de <= 0.25:
            score += 5; components.append(f"D/E {de:.2f} ≤ 0.25 (+5)")
        elif de <= 0.5:
            score += 4; components.append(f"D/E {de:.2f} ≤ 0.5 (+4)")
        elif de <= 1.0:
            score += 2; components.append(f"D/E {de:.2f} ≤ 1.0 (+2)")
        else:
            components.append(f"D/E {de:.2f} > 1.0 (+0, red flag)")

    # FCF positive (5 pts max)
    fcf = data.get("cash_flow", {}).get("free_cash_flow")
    owner_earnings = data.get("cash_flow", {}).get("owner_earnings")
    if owner_earnings is not None and owner_earnings > 0:
        score += 5; components.append(f"Owner Earnings ${owner_earnings/1e6:.0f}M positive (+5)")
    elif fcf is not None and fcf > 0:
        score += 4; components.append(f"FCF ${fcf/1e6:.0f}M positive (+4)")
    elif fcf is not None:
        components.append(f"FCF ${fcf/1e6:.0f}M negative (+0)")

    # Gross margin stability (5 pts max)
    gm = data.get("profitability", {}).get("gross_margin_pct")
    if gm is not None:
        if gm >= 60:
            score += 5; components.append(f"Gross margin {gm}% ≥ 60% (+5)")
        elif gm >= 40:
            score += 3; components.append(f"Gross margin {gm}% ≥ 40% (+3)")
        elif gm >= 25:
            score += 1; components.append(f"Gross margin {gm}% (+1)")
        else:
            components.append(f"Gross margin {gm}% < 25% (+0)")

    # Revenue growth (5 pts max)
    rev_growth = data.get("growth", {}).get("revenue_growth_ttm_pct")
    if rev_growth is not None:
        if rev_growth >= 15:
            score += 5; components.append(f"Revenue growth {rev_growth}% ≥ 15% (+5)")
        elif rev_growth >= 8:
            score += 3; components.append(f"Revenue growth {rev_growth}% (+3)")
        elif rev_growth >= 3:
            score += 1; components.append(f"Revenue growth {rev_growth}% (+1)")
        else:
            components.append(f"Revenue growth {rev_growth}% < 3% (+0)")

    return {"score": min(25, score), "max": 25, "components": components}


def score_management(data: dict) -> dict:
    """Score management quality component for Buffett Score (0-15)."""
    score = 0
    components = []

    # Insider ownership (5 pts max)
    insider = data.get("ownership", {}).get("insider_ownership_pct")
    if insider is not None:
        if insider >= 10:
            score += 5; components.append(f"Insider ownership {insider}% ≥ 10% (+5)")
        elif insider >= 5:
            score += 4; components.append(f"Insider ownership {insider}% ≥ 5% (+4)")
        elif insider >= 1:
            score += 2; components.append(f"Insider ownership {insider}% (+2)")
        else:
            components.append(f"Low insider ownership {insider}% (+0)")

    # Share dilution check (5 pts max)
    shares_change = data.get("ownership", {}).get("shares_change_2yr_pct")
    if shares_change is not None:
        if shares_change <= -2:
            score += 5; components.append(f"Buybacks: shares down {shares_change}% (+5)")
        elif shares_change <= 0:
            score += 4; components.append(f"Share count stable/flat {shares_change}% (+4)")
        elif shares_change <= 2:
            score += 2; components.append(f"Mild dilution {shares_change}% (+2)")
        else:
            components.append(f"Dilution: shares up {shares_change}% (+0, red flag)")

    # Dividend consistency (5 pts max)
    div_yield = data.get("per_share", {}).get("dividend_yield_pct")
    payout_ratio = data.get("per_share", {}).get("payout_ratio_pct")
    if div_yield and div_yield > 0:
        if payout_ratio and payout_ratio < 60:
            score += 5; components.append(f"Dividend {div_yield}%, payout {payout_ratio}% (sustainable) (+5)")
        elif payout_ratio and payout_ratio < 80:
            score += 3; components.append(f"Dividend {div_yield}%, payout {payout_ratio}% (+3)")
        else:
            score += 1; components.append(f"Dividend {div_yield}% but high payout ratio (+1)")
    else:
        # No dividend — check if FCF is being invested productively (growth reinvestment)
        rev_growth = data.get("growth", {}).get("revenue_growth_ttm_pct")
        if rev_growth and rev_growth > 10:
            score += 4; components.append(f"No dividend, but reinvesting at {rev_growth}% growth rate (+4)")
        else:
            score += 2; components.append("No dividend, moderate reinvestment (+2)")

    return {"score": min(15, score), "max": 15, "components": components}


def score_analyst_momentum(data: dict) -> dict:
    """Score analyst quality momentum for Buffett Score (0-10)."""
    score = 0
    components = []

    rec_mean = data.get("analyst", {}).get("recommendation_mean")
    n_analysts = data.get("analyst", {}).get("number_of_analyst_opinions")
    rec_key = data.get("analyst", {}).get("recommendation_key")

    # Yahoo consensus score: 1=Strong Buy, 5=Sell
    if rec_mean is not None:
        if rec_mean <= 1.5:
            score += 5; components.append(f"Consensus {rec_mean:.1f} (Strong Buy range) (+5)")
        elif rec_mean <= 2.0:
            score += 4; components.append(f"Consensus {rec_mean:.1f} (Buy range) (+4)")
        elif rec_mean <= 2.5:
            score += 3; components.append(f"Consensus {rec_mean:.1f} (Moderate Buy) (+3)")
        elif rec_mean <= 3.0:
            score += 2; components.append(f"Consensus {rec_mean:.1f} (Hold range) (+2)")
        else:
            score += 0; components.append(f"Consensus {rec_mean:.1f} (Sell/Underperform) (+0)")

    # Analyst coverage (< 5 = underfollowed gem potential)
    if n_analysts is not None:
        if n_analysts >= 20:
            score += 3; components.append(f"{n_analysts} analysts covering (+3, well-covered)")
        elif n_analysts >= 10:
            score += 2; components.append(f"{n_analysts} analysts (+2)")
        elif n_analysts >= 5:
            score += 1; components.append(f"{n_analysts} analysts (+1)")
        else:
            score += 2; components.append(f"Only {n_analysts} analysts — underfollowed (+2, potential gem)")

    # Upside to analyst target
    upside = data.get("analyst", {}).get("upside_to_target_pct")
    if upside is not None:
        if upside > 30:
            score += 2; components.append(f"{upside}% upside to target (+2)")
        elif upside > 15:
            score += 1; components.append(f"{upside}% upside to target (+1)")

    return {"score": min(10, score), "max": 10, "components": components}


def compute_buffett_score(data: dict, moat_score: int, mos_pct: float) -> dict:
    """
    Compute the overall Buffett Score (0-100).
    Components: MOAT (25), Fundamentals (25), Valuation/MoS (25), Management (15), Analyst (10)
    """
    # Component 1: MOAT (0-25, already scored by moat_scorer.py)
    moat_pts = min(25, moat_score)

    # Component 2: Fundamentals (0-25)
    fundamentals = score_fundamentals(data)

    # Component 3: Valuation / Margin of Safety (0-25)
    if mos_pct >= 40:
        valuation_pts = 25
    elif mos_pct >= 30:
        valuation_pts = 20
    elif mos_pct >= 20:
        valuation_pts = 15
    elif mos_pct >= 10:
        valuation_pts = 8
    elif mos_pct >= 0:
        valuation_pts = 3
    else:
        valuation_pts = 0

    # Component 4: Management (0-15)
    management = score_management(data)

    # Component 5: Analyst Momentum (0-10)
    analyst = score_analyst_momentum(data)

    total = moat_pts + fundamentals["score"] + valuation_pts + management["score"] + analyst["score"]
    total = min(100, total)

    # Determine verdict
    if total >= 80:
        verdict = "STRONG BUY"
        verdict_color = "🟢🟢"
    elif total >= 65:
        verdict = "BUY"
        verdict_color = "🟢"
    elif total >= 50:
        verdict = "HOLD"
        verdict_color = "🟡"
    elif total >= 35:
        verdict = "MONITOR"
        verdict_color = "🟠"
    else:
        verdict = "AVOID"
        verdict_color = "🔴"

    return {
        "total_score": total,
        "verdict": verdict,
        "verdict_emoji": verdict_color,
        "components": {
            "moat_strength": {"score": moat_pts, "max": 25},
            "fundamentals_quality": {"score": fundamentals["score"], "max": 25, "detail": fundamentals["components"]},
            "valuation_margin_of_safety": {"score": valuation_pts, "max": 25, "mos_pct_used": mos_pct},
            "management_quality": {"score": management["score"], "max": 15, "detail": management["components"]},
            "analyst_momentum": {"score": analyst["score"], "max": 10, "detail": analyst["components"]},
        },
    }


def full_valuation(data: dict, moat_result: dict = None) -> dict:
    """Run complete valuation analysis and return all results."""
    output = {}
    ticker = data.get("basic", {}).get("ticker", "N/A")
    current_price = data.get("price", {}).get("current_price")

    # 1. ROIC vs WACC
    output["roic_analysis"] = estimate_roic(data)

    # 2. Owner Earnings DCF
    owner_earnings = data.get("cash_flow", {}).get("owner_earnings")
    shares_outstanding = data.get("per_share", {}).get("shares_outstanding")
    growth_rate_estimate = None

    # Get growth rate for DCF
    analyst_growth = data.get("growth", {}).get("analyst_5yr_growth_pct")
    rev_growth = data.get("growth", {}).get("revenue_growth_ttm_pct")
    earnings_growth = data.get("growth", {}).get("earnings_growth_ttm_pct")

    if analyst_growth:
        growth_rate_estimate = analyst_growth / 100
        growth_source = f"Analyst 5yr estimate: {analyst_growth}%"
    elif earnings_growth and earnings_growth > 0:
        growth_rate_estimate = min(earnings_growth / 100, 0.20)
        growth_source = f"TTM earnings growth: {earnings_growth}%"
    elif rev_growth and rev_growth > 0:
        growth_rate_estimate = min(rev_growth / 100, 0.15)
        growth_source = f"TTM revenue growth: {rev_growth}%"
    else:
        growth_rate_estimate = 0.05
        growth_source = "Default conservative 5% (no growth data available)"

    if owner_earnings and owner_earnings > 0 and shares_outstanding and shares_outstanding > 0:
        oe_per_share = owner_earnings / shares_outstanding
        dcf_results = owner_earnings_dcf(oe_per_share, growth_rate_estimate)
        output["owner_earnings_dcf"] = {
            "owner_earnings_total": owner_earnings,
            "owner_earnings_per_share": round(oe_per_share, 2),
            "growth_rate_used_pct": round(growth_rate_estimate * 100, 1),
            "growth_source": growth_source,
            "intrinsic_value_per_share": dcf_results,
        }
        base_intrinsic = dcf_results.get("base", {}).get("total_intrinsic_value")
    else:
        output["owner_earnings_dcf"] = {
            "error": "Owner earnings not available or negative — DCF requires positive FCF",
            "fallback": "Use Graham Number or P/E-based valuation instead",
        }
        base_intrinsic = None

    # 3. Graham Number
    eps = data.get("per_share", {}).get("eps_trailing")
    bvps = data.get("per_share", {}).get("book_value_per_share")
    output["graham_number"] = graham_number(eps, bvps)

    # 4. Margin of Safety (using best available intrinsic value)
    graham_val = output["graham_number"].get("graham_number")

    if base_intrinsic and current_price:
        output["margin_of_safety_dcf"] = margin_of_safety(base_intrinsic, current_price)
        primary_mos = output["margin_of_safety_dcf"]["margin_of_safety_pct"]
    elif graham_val and current_price:
        output["margin_of_safety_graham"] = margin_of_safety(graham_val, current_price)
        primary_mos = output["margin_of_safety_graham"]["margin_of_safety_pct"]
    else:
        primary_mos = 0

    if graham_val and current_price:
        output["margin_of_safety_graham"] = margin_of_safety(graham_val, current_price)

    # 5. Buffett Score
    moat_score = moat_result.get("total_score", 0) if moat_result else 0
    output["buffett_score"] = compute_buffett_score(data, moat_score, primary_mos)
    output["buffett_score"]["primary_mos_used"] = primary_mos

    return output


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: valuation.py <TICKER>"}))
        sys.exit(1)

    ticker = sys.argv[1]
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Fetch data
    result = subprocess.run(
        [sys.executable, os.path.join(script_dir, "fetch_data.py"), ticker],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(json.dumps({"error": f"fetch_data failed: {result.stderr}"}))
        sys.exit(1)
    data = json.loads(result.stdout)

    # Get MOAT score
    moat_result_raw = subprocess.run(
        [sys.executable, os.path.join(script_dir, "moat_scorer.py"), ticker],
        capture_output=True, text=True
    )
    moat_result = None
    if moat_result_raw.returncode == 0:
        try:
            moat_result = json.loads(moat_result_raw.stdout)
        except Exception:
            pass

    result_data = full_valuation(data, moat_result)
    print(json.dumps(result_data, indent=2, default=str))


if __name__ == "__main__":
    main()
