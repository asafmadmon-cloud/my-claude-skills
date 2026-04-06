#!/usr/bin/env python3
"""
moat_scorer.py — 5-type MOAT scoring engine for Strategic Stock Analysis Pilot
Scores each MOAT dimension 0-5 using quantitative proxies from financial data.
Usage: python moat_scorer.py <TICKER>  OR  import and call score_moat(data_dict)
"""

import sys
import json


def score_switching_costs(data: dict) -> dict:
    """
    Switching Costs (0-5): How painful/expensive is it for customers to leave?
    Proxy: Revenue stability, gross margin consistency, SaaS/recurring revenue signals.
    """
    score = 0
    evidence = []
    sector = (data.get("basic", {}).get("sector") or "").lower()
    industry = (data.get("basic", {}).get("industry") or "").lower()

    # High-switching-cost industries get a baseline
    # Consumer electronics/tech ecosystems (Apple, Google) have deep lock-in via app stores,
    # device ecosystems, cloud accounts, and cross-device continuity
    high_switching_industries = [
        "software", "saas", "enterprise", "database", "erp", "cloud",
        "insurance", "banking", "financial services", "healthcare technology",
        "payment processing", "semiconductor equipment",
        "consumer electronics", "technology hardware", "electronic equipment",
        "information technology services", "internet content", "interactive media",
        "application software", "systems software"
    ]
    for keyword in high_switching_industries:
        if keyword in industry or keyword in sector:
            score += 2
            evidence.append(f"Industry '{industry}' typically has high switching costs")
            break

    # Gross margin > 60% often indicates pricing power from lock-in
    gm = data.get("profitability", {}).get("gross_margin_pct")
    if gm is not None:
        if gm > 70:
            score += 2
            evidence.append(f"Gross margin {gm}% (>70%) suggests strong pricing power / lock-in")
        elif gm > 50:
            score += 1
            evidence.append(f"Gross margin {gm}% (>50%) suggests moderate switching cost advantage")
        else:
            evidence.append(f"Gross margin {gm}% — limited pricing power signal")

    # Revenue stability proxy: low revenue growth volatility = sticky customers
    rev_growth = data.get("growth", {}).get("revenue_growth_ttm_pct")
    if rev_growth is not None and rev_growth > 5:
        score += 1
        evidence.append(f"Revenue growing {rev_growth}% — stable customer base signal")

    score = min(5, score)
    return {
        "score": score,
        "max": 5,
        "label": "Switching Costs",
        "evidence": evidence,
        "note": "Manual check: look for multi-year contracts, API integrations, data lock-in"
    }


def score_network_effect(data: dict) -> dict:
    """
    Network Effect (0-5): Does the product become more valuable with more users?
    Proxy: Platform/marketplace industries, user growth signals.
    """
    score = 0
    evidence = []
    sector = (data.get("basic", {}).get("sector") or "").lower()
    industry = (data.get("basic", {}).get("industry") or "").lower()
    name = (data.get("basic", {}).get("name") or "").lower()

    # Network effect industries — includes app stores and device ecosystems
    # Apple's App Store, Google Play, Meta social graph are all classic two-sided networks
    network_industries = [
        "payment", "social", "marketplace", "platform", "exchange",
        "financial exchange", "data", "advertising", "media", "communications",
        "consumer electronics", "internet content", "interactive media",
        "internet retail", "technology hardware"
    ]
    for keyword in network_industries:
        if keyword in industry or keyword in sector or keyword in name:
            score += 2
            evidence.append(f"'{industry}' is a network-effect business model")
            break

    # High revenue growth + high margins often indicates network flywheel
    gm = data.get("profitability", {}).get("gross_margin_pct")
    rev_growth = data.get("growth", {}).get("revenue_growth_ttm_pct")

    if gm and rev_growth and gm > 60 and rev_growth > 15:
        score += 2
        evidence.append(
            f"High margin ({gm}%) + strong growth ({rev_growth}%) consistent with network flywheel"
        )
    elif gm and gm > 50:
        score += 1
        evidence.append(f"Gross margin {gm}% may reflect network leverage")

    # Operating leverage (margin expansion) signals network effect
    op_margin = data.get("profitability", {}).get("operating_margin_pct")
    if op_margin and op_margin > 20:
        score += 1
        evidence.append(f"Operating margin {op_margin}% — potential operating leverage from scale")

    score = min(5, score)
    return {
        "score": score,
        "max": 5,
        "label": "Network Effect",
        "evidence": evidence,
        "note": "Manual check: platform with two-sided market? Data flywheel? Growing user base?"
    }


def score_cost_advantage(data: dict) -> dict:
    """
    Cost Advantage (0-5): Can the company produce at lower cost than competitors?
    Proxy: Gross margin vs. sector, operating leverage, capex efficiency.
    """
    score = 0
    evidence = []
    sector = (data.get("basic", {}).get("sector") or "").lower()
    industry = (data.get("basic", {}).get("industry") or "").lower()

    gm = data.get("profitability", {}).get("gross_margin_pct")
    op_margin = data.get("profitability", {}).get("operating_margin_pct")
    net_margin = data.get("profitability", {}).get("net_margin_pct")

    # Sector-specific gross margin benchmarks
    # These are approximate industry averages
    sector_benchmarks = {
        "technology": 55,
        "healthcare": 50,
        "financial services": 40,
        "consumer defensive": 35,
        "communication services": 50,
        "consumer cyclical": 30,
        "industrials": 30,
        "energy": 25,
        "basic materials": 25,
        "utilities": 30,
        "real estate": 40,
    }

    benchmark = None
    for sec_key, bench in sector_benchmarks.items():
        if sec_key in sector or sec_key in industry:
            benchmark = bench
            break

    if gm is not None:
        if benchmark and gm > benchmark + 20:
            score += 3
            evidence.append(
                f"Gross margin {gm}% is {gm - benchmark:.0f}pp above sector avg ({benchmark}%) — significant cost/pricing advantage"
            )
        elif benchmark and gm > benchmark + 10:
            score += 2
            evidence.append(
                f"Gross margin {gm}% is {gm - benchmark:.0f}pp above sector avg — moderate cost advantage"
            )
        elif benchmark and gm > benchmark:
            score += 1
            evidence.append(f"Gross margin {gm}% slightly above sector avg ({benchmark}%)")
        elif gm > 50:
            score += 2
            evidence.append(f"High absolute gross margin {gm}% suggests cost discipline")
        elif gm > 35:
            score += 1
            evidence.append(f"Gross margin {gm}% — moderate cost structure")
        else:
            evidence.append(f"Gross margin {gm}% — limited cost advantage")

    # Operating margin as efficiency indicator
    if op_margin is not None and op_margin > 20:
        score += 1
        evidence.append(f"Operating margin {op_margin}% shows operational efficiency")

    # FCF conversion rate (FCF/Net Income > 1 = good cash conversion)
    fcf = data.get("cash_flow", {}).get("free_cash_flow")
    net_inc = data.get("cash_flow", {}).get("net_income")
    if fcf and net_inc and net_inc > 0:
        fcf_conversion = fcf / net_inc
        if fcf_conversion > 1.1:
            score += 1
            evidence.append(
                f"FCF/Net Income = {fcf_conversion:.1f}x — excellent cash conversion (cost-efficient ops)"
            )

    score = min(5, score)
    return {
        "score": score,
        "max": 5,
        "label": "Cost Advantage",
        "evidence": evidence,
        "note": "Manual check: proprietary process? Sole-source supplier? Scale economics vs. peers?"
    }


def score_intangible_assets(data: dict) -> dict:
    """
    Intangible Assets (0-5): Brands, patents, licenses, regulatory approvals.
    Proxy: Gross margin stability, R&D intensity, sector indicators.
    """
    score = 0
    evidence = []
    sector = (data.get("basic", {}).get("sector") or "").lower()
    industry = (data.get("basic", {}).get("industry") or "").lower()
    name = (data.get("basic", {}).get("name") or "").lower()

    # Industries with strong intangible moats
    # Consumer electronics includes Apple (world's most valuable brand + iOS ecosystem IP)
    brand_industries = [
        "beverage", "consumer goods", "apparel", "luxury", "spirits",
        "tobacco", "food", "cosmetics", "personal care",
        "consumer electronics", "technology hardware", "internet content",
        "interactive media", "communication services", "entertainment"
    ]
    patent_industries = [
        "pharmaceutical", "biotechnology", "drug", "medical device",
        "semiconductor", "aerospace", "defense",
        "application software", "systems software", "it services"
    ]
    license_industries = [
        "credit rating", "financial data", "exchange", "insurance",
        "utilities", "broadcast", "telecom", "financial services",
        "payment", "capital markets"
    ]

    for keyword in brand_industries:
        if keyword in industry or keyword in name:
            score += 2
            evidence.append(f"'{industry}' — brand-driven business with likely pricing power")
            break

    for keyword in patent_industries:
        if keyword in industry or keyword in sector:
            score += 2
            evidence.append(f"'{industry}' — patent/IP-driven business model")
            break

    for keyword in license_industries:
        if keyword in industry:
            score += 3
            evidence.append(f"'{industry}' — regulatory license/franchise creates high barrier")
            break

    # Sustained high gross margins = pricing power = brand/intangible signal
    gm = data.get("profitability", {}).get("gross_margin_pct")
    if gm is not None:
        if gm > 65:
            score += 2
            evidence.append(
                f"Sustained gross margin {gm}% (>65%) is strong evidence of pricing power / intangible asset"
            )
        elif gm > 50:
            score += 1
            evidence.append(f"Gross margin {gm}% suggests some pricing power")

    # R&D as % of revenue (high R&D investment = patent creation)
    # Can't get this directly from yfinance easily, so note it
    evidence.append("Manual check: R&D / Revenue ratio vs. peers; brand valuation; patent count")

    score = min(5, score)
    return {
        "score": score,
        "max": 5,
        "label": "Intangible Assets",
        "evidence": evidence,
        "note": "Manual: brand premium vs. generic, patent expiry schedule, regulatory license"
    }


def score_efficient_scale(data: dict) -> dict:
    """
    Efficient Scale (0-5): Market where only 1-3 players can profitably operate.
    Proxy: Market cap size relative to industry, stable market share signals.
    """
    score = 0
    evidence = []
    sector = (data.get("basic", {}).get("sector") or "").lower()
    industry = (data.get("basic", {}).get("industry") or "").lower()

    # Industries with natural monopoly/oligopoly characteristics
    efficient_scale_industries = [
        "railroad", "pipeline", "utility", "water", "waste management",
        "airport", "port", "toll", "landfill", "satellite",
        "credit card network", "payment network", "exchange"
    ]

    for keyword in efficient_scale_industries:
        if keyword in industry:
            score += 3
            evidence.append(
                f"'{industry}' is a natural oligopoly — capital intensity prevents new entrants"
            )
            break

    # Large market cap + stable margins = possible dominant position
    mktcap = data.get("price", {}).get("market_cap")
    if mktcap:
        if mktcap > 500_000_000_000:  # > $500B
            score += 2
            evidence.append(
                f"Market cap ${mktcap/1e9:.0f}B — scale dominance in its category likely"
            )
        elif mktcap > 100_000_000_000:  # > $100B
            score += 1
            evidence.append(
                f"Market cap ${mktcap/1e9:.0f}B — significant scale, likely top-3 in industry"
            )

    # High operating margins in capital-heavy industries = efficient scale
    op_margin = data.get("profitability", {}).get("operating_margin_pct")
    capex = data.get("cash_flow", {}).get("capital_expenditures")
    revenue = data.get("cash_flow", {}).get("revenue")
    if op_margin and capex and revenue and revenue > 0:
        capex_pct = abs(capex) / revenue * 100
        if capex_pct > 15 and op_margin > 20:
            score += 1
            evidence.append(
                f"High capex ({capex_pct:.0f}% of revenue) + strong margins ({op_margin}%) = capital moat"
            )

    score = min(5, score)
    return {
        "score": score,
        "max": 5,
        "label": "Efficient Scale",
        "evidence": evidence,
        "note": "Manual check: How many players in this market? What capex to compete? Regulatory barriers?"
    }


def classify_moat(total_score: int) -> str:
    if total_score >= 18:
        return "WIDE MOAT"
    elif total_score >= 10:
        return "NARROW MOAT"
    else:
        return "NO MOAT"


def score_moat(data: dict) -> dict:
    """Main entry point: score all 5 MOAT types and return summary."""
    switching = score_switching_costs(data)
    network = score_network_effect(data)
    cost = score_cost_advantage(data)
    intangible = score_intangible_assets(data)
    scale = score_efficient_scale(data)

    total = switching["score"] + network["score"] + cost["score"] + intangible["score"] + scale["score"]
    classification = classify_moat(total)

    # Identify the dominant moat type
    scores = {
        "Switching Costs": switching["score"],
        "Network Effect": network["score"],
        "Cost Advantage": cost["score"],
        "Intangible Assets": intangible["score"],
        "Efficient Scale": scale["score"],
    }
    dominant = max(scores, key=scores.get)

    return {
        "total_score": total,
        "max_score": 25,
        "classification": classification,
        "dominant_moat_type": dominant if scores[dominant] >= 3 else "Mixed / Unclear",
        "dimensions": [switching, network, cost, intangible, scale],
        "scores_summary": scores,
        "interpretation": {
            "18-25": "Wide Moat — Buffett-quality, long-term hold candidate",
            "10-17": "Narrow Moat — monitor, moat may be eroding",
            "0-9": "No Moat — avoid for long-term investment",
        }[
            "18-25" if total >= 18 else ("10-17" if total >= 10 else "0-9")
        ],
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: moat_scorer.py <TICKER>"}))
        sys.exit(1)

    ticker = sys.argv[1]

    # Import fetch_data from same directory
    import subprocess
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(
        [sys.executable, os.path.join(script_dir, "fetch_data.py"), ticker],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(json.dumps({"error": f"fetch_data.py failed: {result.stderr}"}))
        sys.exit(1)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Failed to parse fetch_data.py output"}))
        sys.exit(1)

    moat_result = score_moat(data)
    print(json.dumps(moat_result, indent=2))


if __name__ == "__main__":
    main()
