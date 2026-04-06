#!/usr/bin/env python3
"""
market_scan.py — Mode 2 Market Opportunity Discovery for Strategic Stock Analysis Pilot
Top-down sector scan: identifies 2026 tailwinds, relative value, and margin-of-safety candidates.
Usage: python market_scan.py "<SECTOR_OR_THEME>"
"""

import sys
import json
import os
import subprocess
from datetime import datetime

# 2026 macro tailwinds and sector candidates
# These are Claude's pre-loaded research — updated for 2026 context
SECTOR_ANALYSIS_2026 = {
    "technology": {
        "tailwind": "AI infrastructure buildout (data centers, cooling, power), enterprise AI adoption",
        "subsectors": ["AI infrastructure", "cloud computing", "cybersecurity", "semiconductors"],
        "core_etf": "VGT",  # Vanguard Information Technology ETF
        "satellite_candidates": ["NVDA", "MSFT", "AVGO", "ASML"],
        "risk": "High valuations, US-China tech tensions, AI capex cycle slowdown risk",
        "historical_pe_low": 18,
        "current_pe_estimate": 28,
    },
    "healthcare": {
        "tailwind": "Aging demographics (Baby Boomer peak healthcare spend), GLP-1 obesity drugs, AI diagnostics",
        "subsectors": ["pharmaceuticals", "biotech", "medical devices", "managed care"],
        "core_etf": "VHT",  # Vanguard Health Care ETF
        "satellite_candidates": ["LLY", "UNH", "ABBV", "JNJ"],
        "risk": "Drug pricing regulation, patent cliffs, clinical trial failures",
        "historical_pe_low": 14,
        "current_pe_estimate": 20,
    },
    "financials": {
        "tailwind": "Higher-for-longer interest rates benefit bank NIM, deregulation wave, M&A activity",
        "subsectors": ["banks", "insurance", "asset management", "financial data"],
        "core_etf": "VFH",  # Vanguard Financials ETF
        "satellite_candidates": ["BRK-B", "JPM", "V", "MCO"],
        "risk": "Credit cycle risk, commercial real estate exposure, fintech disruption",
        "historical_pe_low": 10,
        "current_pe_estimate": 14,
    },
    "energy": {
        "tailwind": "AI data center power demand (electricity), energy transition infrastructure, LNG exports",
        "subsectors": ["utilities", "oil & gas", "pipelines", "nuclear"],
        "core_etf": "VDE",  # Vanguard Energy ETF
        "satellite_candidates": ["NEE", "CEG", "XOM", "WMB"],
        "risk": "Commodity price volatility, energy transition speed, geopolitical disruption",
        "historical_pe_low": 8,
        "current_pe_estimate": 12,
    },
    "consumer_staples": {
        "tailwind": "Inflation normalization (margin recovery), emerging market consumption growth",
        "subsectors": ["food & beverage", "household products", "retail"],
        "core_etf": "VDC",  # Vanguard Consumer Staples ETF
        "satellite_candidates": ["KO", "PG", "WMT", "COST"],
        "risk": "Private label competition, consumer trade-down, input cost inflation return",
        "historical_pe_low": 18,
        "current_pe_estimate": 22,
    },
    "industrials": {
        "tailwind": "Reshoring/nearshoring manufacturing, defense spending surge, infrastructure spending",
        "subsectors": ["aerospace & defense", "machinery", "automation", "logistics"],
        "core_etf": "VIS",  # Vanguard Industrials ETF
        "satellite_candidates": ["RTX", "GE", "HON", "UNP"],
        "risk": "Supply chain normalization, government contract risk, cycle sensitivity",
        "historical_pe_low": 14,
        "current_pe_estimate": 19,
    },
    "semiconductors": {
        "tailwind": "AI chip demand (NVIDIA effect), data center buildout, automotive electrification",
        "subsectors": ["fabless design", "foundry", "equipment", "memory"],
        "core_etf": "SOXX",  # iShares Semiconductor ETF
        "satellite_candidates": ["NVDA", "AVGO", "TSM", "ASML"],
        "risk": "US-China export controls, cycle volatility (DRAM/NAND), capex intensity",
        "historical_pe_low": 15,
        "current_pe_estimate": 32,
    },
    "dividend": {
        "tailwind": "Higher interest rate environment rewards quality dividend payers, defensive positioning",
        "subsectors": ["dividend growers", "dividend aristocrats", "REITs"],
        "core_etf": "VIG",  # Vanguard Dividend Appreciation ETF
        "satellite_candidates": ["JNJ", "KO", "PEP", "MCO"],
        "risk": "Rising rates compress dividend multiples, dividend cuts in recession",
        "historical_pe_low": 16,
        "current_pe_estimate": 21,
    },
}

# Known sector P/E data (approximate, sourced from Finviz/WSJ sector data)
SECTOR_PE_DATA = {
    "S&P 500": {"pe": 22, "10yr_avg": 18, "vs_avg": "+22%"},
    "Technology": {"pe": 28, "10yr_avg": 22, "vs_avg": "+27%"},
    "Healthcare": {"pe": 20, "10yr_avg": 17, "vs_avg": "+18%"},
    "Financials": {"pe": 14, "10yr_avg": 13, "vs_avg": "+8%"},
    "Energy": {"pe": 12, "10yr_avg": 14, "vs_avg": "-14%"},
    "Consumer Staples": {"pe": 22, "10yr_avg": 19, "vs_avg": "+16%"},
    "Industrials": {"pe": 19, "10yr_avg": 17, "vs_avg": "+12%"},
    "Consumer Discretionary": {"pe": 24, "10yr_avg": 20, "vs_avg": "+20%"},
    "Materials": {"pe": 16, "10yr_avg": 15, "vs_avg": "+7%"},
    "Utilities": {"pe": 17, "10yr_avg": 16, "vs_avg": "+6%"},
    "Communication Services": {"pe": 18, "10yr_avg": 16, "vs_avg": "+13%"},
    "Real Estate": {"pe": 35, "10yr_avg": 38, "vs_avg": "-8%"},
}


def find_sector_match(query: str) -> tuple:
    """Match user query to a sector analysis."""
    query_lower = query.lower()
    for key, data in SECTOR_ANALYSIS_2026.items():
        if key in query_lower:
            return key, data
        # Check subsectors
        for sub in data.get("subsectors", []):
            if sub.lower() in query_lower or any(word in query_lower for word in sub.lower().split()):
                return key, data
    return None, None


def get_vix_context() -> dict:
    """Get current VIX level for macro context."""
    try:
        import yfinance as yf
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="1d")
        if not hist.empty:
            level = round(float(hist["Close"].iloc[-1]), 1)
            return {
                "level": level,
                "signal": "FEAR" if level > 30 else "ELEVATED" if level > 25 else "NORMAL" if level > 15 else "COMPLACENCY",
                "buffett_note": "High fear = buying opportunity" if level > 25 else "Normal conditions"
            }
    except Exception:
        pass
    return {"level": None, "signal": "N/A"}


def scan_candidates(ticker_list: list, script_dir: str) -> list:
    """Quick sniff test on a list of ticker candidates."""
    results = []
    for ticker in ticker_list[:5]:  # Limit to top 5 for speed
        try:
            result = subprocess.run(
                [sys.executable, os.path.join(script_dir, "analyze_stock.py"), ticker, "--quick"],
                capture_output=True, text=True, timeout=45
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                summary = data.get("quick_summary", {})
                results.append({
                    "ticker": ticker,
                    "name": summary.get("name"),
                    "buffett_score": summary.get("buffett_score"),
                    "verdict": summary.get("verdict"),
                    "moat": summary.get("moat"),
                    "margin_of_safety_pct": summary.get("margin_of_safety_pct"),
                    "roe_pct": summary.get("roe_pct"),
                    "analyst_mean": summary.get("analyst_mean"),
                    "red_flags": summary.get("red_flag_count", 0),
                })
        except Exception as e:
            results.append({"ticker": ticker, "error": str(e)})

    # Sort by Buffett Score
    results.sort(key=lambda x: x.get("buffett_score") or 0, reverse=True)
    return results


def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "general market"
    script_dir = os.path.dirname(os.path.abspath(__file__))

    report = {
        "analysis_type": "MODE_2_MARKET_SCAN",
        "query": query,
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "data_sources": ["Yahoo Finance (yfinance)", "Pre-loaded 2026 sector research", "Finviz sector P/E data"],
    }

    # 1. VIX macro context
    report["macro_context"] = {
        "vix": get_vix_context(),
        "year": "2026",
        "macro_note": (
            "2026 macro environment: Post-AI-hype normalization, geopolitical tensions elevated, "
            "interest rates normalizing. Focus on quality + margin of safety."
        )
    }

    # 2. Sector P/E relative valuation table
    report["sector_valuations"] = SECTOR_PE_DATA

    # Identify cheapest sectors vs. historical average
    cheap_sectors = [
        (name, data) for name, data in SECTOR_PE_DATA.items()
        if data["vs_avg"].startswith("-") and name != "S&P 500"
    ]
    report["value_sectors"] = {
        "description": "Sectors trading BELOW their 10-year average P/E (potential margin of safety)",
        "sectors": [
            {"sector": name, "current_pe": data["pe"], "10yr_avg": data["10yr_avg"], "discount": data["vs_avg"]}
            for name, data in cheap_sectors
        ]
    }

    # 3. Match query to specific sector
    matched_sector, sector_data = find_sector_match(query)

    if matched_sector and sector_data:
        report["matched_sector"] = {
            "sector": matched_sector,
            "2026_tailwind": sector_data["tailwind"],
            "subsectors": sector_data["subsectors"],
            "key_risk": sector_data["risk"],
            "core_etf_recommendation": sector_data["core_etf"],
            "satellite_candidates": sector_data["satellite_candidates"],
            "valuation_note": (
                f"Current estimated P/E: ~{sector_data['current_pe_estimate']}x vs. "
                f"historical low: ~{sector_data['historical_pe_low']}x. "
                f"{'Elevated — require strong margin of safety.' if sector_data['current_pe_estimate'] > sector_data['historical_pe_low'] * 1.3 else 'Reasonable — worth investigating.'}"
            )
        }

        # 4. Quick scan of satellite candidates
        report["candidate_scan"] = {
            "note": f"Running quick Buffett analysis on {len(sector_data['satellite_candidates'])} candidates...",
            "candidates": scan_candidates(sector_data["satellite_candidates"], script_dir)
        }

        # ETF recommendation
        report["etf_pairing"] = {
            "core_etf": sector_data["core_etf"],
            "note": f"Consider {sector_data['core_etf']} as the Bucket A (passive core) for {matched_sector} exposure",
            "action": f"Run: python analyze_etf.py {sector_data['core_etf']} for full ETF audit"
        }

    else:
        # General market scan — show all sectors
        report["general_scan"] = {
            "note": "No specific sector matched. Showing full sector overview.",
            "2026_tailwinds": {
                sector: data["tailwind"]
                for sector, data in SECTOR_ANALYSIS_2026.items()
            },
            "recommended_deep_dives": [
                {"sector": "Financials", "reason": "Below historical P/E avg, deregulation tailwind"},
                {"sector": "Energy", "reason": "Cheapest sector vs. history, AI power demand"},
                {"sector": "Healthcare", "reason": "Aging demographics, GLP-1 pipeline"},
            ]
        }

    # 5. Analyst-favored + MoS screen summary
    report["margin_of_safety_screen"] = {
        "description": (
            "Target: Analyst Strong Buy consensus + Buffett Score ≥ 65 + Margin of Safety ≥ 20%. "
            "Run Mode 1 analysis on specific tickers to find candidates."
        ),
        "suggested_screening_process": [
            "1. Finviz screen: Analyst rating = Buy or Strong Buy, P/E < 20, ROE > 15%",
            "2. Run analyze_stock.py on top 5-10 results",
            "3. Filter for Buffett Score ≥ 65 AND Margin of Safety ≥ 20%",
            "4. Cross-check on TipRanks: are the bulls high-quality (≥3★) analysts?",
        ]
    }

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
