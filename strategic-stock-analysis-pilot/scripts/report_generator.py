#!/usr/bin/env python3
"""
report_generator.py — Output formatter for Strategic Stock Analysis Pilot
Generates: structured text report + matplotlib charts saved as PNG files.
Usage: python report_generator.py <TICKER> [--output-dir <dir>] [--quick]
"""

import sys
import json
import os
import subprocess
from datetime import datetime

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend (no display needed)
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def get_color(score: float, max_score: float = 100) -> str:
    pct = score / max_score
    if pct >= 0.65:
        return '#27ae60'
    elif pct >= 0.35:
        return '#f39c12'
    else:
        return '#e74c3c'


def chart_buffett_gauge(buffett_score: int, ticker: str, output_dir: str) -> str:
    if not HAS_MATPLOTLIB:
        return None
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.8, 1.8)
    ax.axis('off')

    # Zone bars
    zones = [(34, '#e74c3c', 'AVOID'), (15, '#e67e22', 'MONITOR'),
             (15, '#f1c40f', 'HOLD'), (15, '#2ecc71', 'BUY'), (21, '#27ae60', 'STRONG BUY')]
    left = 0
    for width, color, label in zones:
        ax.barh(0, width, color=color, height=0.6, left=left, alpha=0.5)
        ax.text(left + width / 2, -0.45, label, ha='center', va='top', fontsize=6.5, color='#444')
        left += width

    # Score pointer
    color = get_color(buffett_score)
    ax.barh(0.55, buffett_score, color=color, height=0.25, alpha=0.9)
    ax.text(buffett_score + 1, 0.55, f'{buffett_score}', va='center', fontsize=10,
            fontweight='bold', color=color)

    verdict_map = {(80, 100): 'STRONG BUY', (65, 79): 'BUY', (50, 64): 'HOLD',
                   (35, 49): 'MONITOR', (0, 34): 'AVOID'}
    verdict = next((v for (lo, hi), v in verdict_map.items() if lo <= buffett_score <= hi), 'N/A')

    ax.text(50, 1.3, f'BUFFETT SCORE: {buffett_score}/100 — {verdict}',
            ha='center', va='center', fontsize=13, fontweight='bold', color='#2c3e50')
    plt.title(f'{ticker} Buffett Score', fontsize=11, pad=5)
    plt.tight_layout()
    path = os.path.join(output_dir, f'{ticker}_buffett_score.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    return path


def chart_moat_radar(moat_data: dict, ticker: str, output_dir: str) -> str:
    if not HAS_MATPLOTLIB:
        return None
    scores = moat_data.get('scores_summary', {})
    if not scores:
        return None

    labels = list(scores.keys())
    values = [scores[k] for k in labels]
    n = len(labels)
    angles = [i * 2 * np.pi / n for i in range(n)] + [0]
    values_plot = values + [values[0]]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
    ax.fill(angles, [5] * (n + 1), alpha=0.1, color='#bdc3c7')
    ax.plot(angles, [5] * (n + 1), 'o-', linewidth=1, color='#bdc3c7')

    color = get_color(moat_data.get('total_score', 0), 25)
    ax.fill(angles, values_plot, alpha=0.3, color=color)
    ax.plot(angles, values_plot, 'o-', linewidth=2, color=color)

    ax.set_xticks(angles[:-1])
    short_labels = [l.replace(' ', '\n') for l in labels]
    ax.set_xticklabels(short_labels, fontsize=8)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=7)

    total = moat_data.get('total_score', 0)
    cls = moat_data.get('classification', '')
    ax.set_title(f'{ticker} MOAT: {total}/25 — {cls}', fontsize=11, fontweight='bold', pad=20)
    plt.tight_layout()
    path = os.path.join(output_dir, f'{ticker}_moat_radar.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    return path


def chart_score_breakdown(score_data: dict, ticker: str, output_dir: str) -> str:
    if not HAS_MATPLOTLIB:
        return None
    components = score_data.get('components', {})
    if not components:
        return None

    order = [('moat', 'MOAT Strength', 25), ('fundamentals', 'Fundamentals', 25),
             ('valuation', 'Valuation/MoS', 25), ('management', 'Management', 15),
             ('analyst', 'Analyst Momentum', 10)]

    labels, actuals, maxes = [], [], []
    for key, label, max_pts in order:
        val = components.get(key, {})
        actual = val.get('score', 0) if isinstance(val, dict) else (val or 0)
        labels.append(f'{label} (/{max_pts})')
        actuals.append(actual)
        maxes.append(max_pts)

    fig, ax = plt.subplots(figsize=(9, 5))
    y = range(len(labels))
    ax.barh(y, maxes, color='#ecf0f1', height=0.55)
    colors = [get_color(a, m) for a, m in zip(actuals, maxes)]
    bars = ax.barh(y, actuals, color=colors, height=0.55)

    for bar, a, m in zip(bars, actuals, maxes):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f'{a}/{m}', va='center', fontsize=9, fontweight='bold')

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(0, 30)
    ax.set_xlabel('Points', fontsize=10)
    ax.set_title(f'{ticker} — Buffett Score: {score_data.get("total_score", 0)}/100', fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    path = os.path.join(output_dir, f'{ticker}_score_breakdown.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    return path


def chart_valuation(valuation_data: dict, current_price: float, ticker: str, output_dir: str) -> str:
    if not HAS_MATPLOTLIB or not current_price:
        return None

    labels = ['Current\nPrice']
    values = [current_price]
    colors = ['#3498db']

    dcf = valuation_data.get('dcf', {})
    if dcf and not dcf.get('error'):
        for scenario in ['conservative', 'base', 'optimistic']:
            s = dcf.get(scenario, {})
            if isinstance(s, dict) and not s.get('error'):
                ps = s.get('per_share_value')
                if ps and ps > 0:
                    labels.append(f'DCF\n{scenario.title()}')
                    values.append(ps)
                    colors.append('#27ae60' if ps > current_price else '#e74c3c')

    graham = valuation_data.get('graham_number', {})
    if graham and not graham.get('error'):
        gn = graham.get('graham_number')
        if gn and gn > 0:
            labels.append('Graham\nNumber')
            values.append(gn)
            colors.append('#9b59b6')

    if len(values) <= 1:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values, color=colors, alpha=0.85, edgecolor='white', linewidth=1.5)
    ax.axhline(y=current_price, color='#3498db', linestyle='--', linewidth=1.5,
               label=f'Current: ${current_price:.0f}')

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                f'${val:.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_ylabel('Price (USD)', fontsize=10)
    ax.set_title(f'{ticker} — Price vs. Intrinsic Value', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = os.path.join(output_dir, f'{ticker}_valuation.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    return path


def fmt(val, unit='', decimals=2, default='N/A'):
    if val is None:
        return default
    try:
        if isinstance(val, float):
            return f'{val:.{decimals}f}{unit}'
        return f'{val}{unit}'
    except Exception:
        return str(val)


def generate_text_report(data: dict, charts: list) -> str:
    ticker = data.get('ticker', '?')
    name = data.get('name', '?')
    sector = data.get('sector', '?')
    date = data.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
    is_etf = 'ETF' in data.get('analysis_type', '')

    moat = data.get('moat_analysis', {})
    val = data.get('valuation', {})
    filters = data.get('buffett_4_filters', {})
    # red_flags is a list of {"severity": "CRITICAL"/"CAUTION", "flag": "..."} dicts
    flags_list = data.get('red_flags', [])
    if isinstance(flags_list, list):
        critical = [f.get('flag', '') for f in flags_list if f.get('severity') == 'CRITICAL']
        caution = [f.get('flag', '') for f in flags_list if f.get('severity') == 'CAUTION']
    else:
        critical = flags_list.get('critical', [])
        caution = flags_list.get('caution', [])

    entry = data.get('entry_conditions', {})
    # Buffett score: stocks use valuation.buffett_score, ETFs use etf_buffett_score
    if is_etf:
        bs = data.get('etf_buffett_score', {})
        # ETF analysis fields are at top level (not nested under 'etf_analysis')
        etf = data
    else:
        bs = data.get('valuation', {}).get('buffett_score', {})
        etf = {}
    analyst = data.get('analyst_data', {})
    verdict = bs.get('verdict', data.get('verdict', 'N/A'))
    score = bs.get('total_score', 0)
    moat_score = moat.get('total_score', 0)
    moat_cls = moat.get('classification', 'N/A')
    snap = data.get('data_snapshot', {})
    # Entry conditions green count
    green = entry.get('summary', {}).get('green_signals', entry.get('green_signal_count', 0))
    entry_label = ('🟢 Favorable' if green >= 3 else ('🟡 Neutral' if green >= 2 else '🔴 Unfavorable'))
    # Margin of safety: from valuation.margin_of_safety_dcf
    mos_base = val.get('margin_of_safety_dcf', val.get('margin_of_safety', {}).get('base', {}))
    mos_pct = mos_base.get('margin_of_safety_pct', 'N/A')

    SEP = '━' * 55
    lines = [SEP,
             f'📊 {ticker} | {name}',
             f'🏷  Type: {"ETF" if is_etf else "Stock"} | Sector: {sector}',
             f'📅 Date: {date} | Source: Yahoo Finance (yfinance)',
             SEP,
             f'🏆 BUFFETT SCORE: {score}/100 → {verdict}',
             f'⭐ VERDICT: {verdict}',
             f'🏰 MOAT: {moat_cls} ({moat_score}/25)',
             f'💰 Margin of Safety: {mos_pct}% ({mos_base.get("valuation_label", "")})',
             f'📈 Entry Conditions: {entry_label} ({green} green signals)',
             f'⚠️  Red Flags: {len(critical)} critical, {len(caution)} caution',
             SEP]

    if charts:
        lines += ['', '📊 CHARTS GENERATED:'] + [f'   • {os.path.basename(c)}' for c in charts if c]

    if not is_etf:
        # DATA SNAPSHOT — built from quick_summary
        lines += ['', '=' * 55, 'SECTION 1: KEY METRICS SNAPSHOT', '=' * 55]
        qs_snap = data.get('quick_summary', {})
        val_snap = data.get('valuation', {})
        fd = data.get('full_data', {})
        fd_price = fd.get('price', {}) if fd else {}
        fd_val = fd.get('valuation', {}) if fd else {}
        fd_prof = fd.get('profitability', {}) if fd else {}
        fd_bs = fd.get('balance_sheet', {}) if fd else {}
        fd_cf = fd.get('cash_flow', {}) if fd else {}
        fd_ps = fd.get('per_share', {}) if fd else {}
        snap_metrics = [
            ('Current Price', f'${qs_snap.get("current_price", "N/A")} {qs_snap.get("currency", "USD")} — Source: Yahoo Finance'),
            ('Market Cap', f'${fd_price.get("market_cap", "N/A"):,}' if fd_price.get("market_cap") else 'N/A — Source: Yahoo Finance'),
            ('P/E (TTM)', f'{fd_val.get("pe_trailing", "N/A")}x — Source: Yahoo Finance'),
            ('P/E (Forward)', f'{fd_val.get("pe_forward", "N/A")}x — Source: Yahoo Finance'),
            ('ROE', f'{qs_snap.get("roe_pct", "N/A")}% — Source: Yahoo Finance Statistics'),
            ('Gross Margin', f'{qs_snap.get("gross_margin_pct", "N/A")}% — Source: Yahoo Finance'),
            ('Debt/Equity', f'{qs_snap.get("debt_to_equity", "N/A")}x — Source: Yahoo Finance'),
            ('EPS (TTM)', f'${fd_ps.get("eps_trailing", "N/A")} — Source: Yahoo Finance'),
            ('BVPS', f'${fd_ps.get("book_value_per_share", "N/A")} — Source: Yahoo Finance'),
            ('52-Week Range', f'${fd_price.get("week_52_low", "N/A")} — ${fd_price.get("week_52_high", "N/A")} — Source: Yahoo Finance'),
            ('Beta', f'{fd_price.get("beta", "N/A")} — Source: Yahoo Finance'),
            ('Owner Earnings', f'${fd_cf.get("owner_earnings", "N/A"):,}' if fd_cf.get("owner_earnings") else 'See Section 5'),
        ]
        for label, value in snap_metrics:
            lines.append(f'  {label:<22} {value}')

        # BUFFETT SCORE BREAKDOWN
        lines += ['', '=' * 55, 'SECTION 2: BUFFETT SCORE BREAKDOWN', '=' * 55]
        comps = bs.get('components', {})
        cmap = [
            ('moat_strength', 'MOAT', 25),
            ('fundamentals_quality', 'FUNDAMENTALS', 25),
            ('valuation_margin_of_safety', 'VALUATION', 25),
            ('management_quality', 'MANAGEMENT', 15),
            ('analyst_momentum', 'ANALYST', 10),
        ]
        for key, label, mx in cmap:
            c = comps.get(key, {})
            s = c.get('score', 0) if isinstance(c, dict) else 0
            notes = c.get('detail', c.get('notes', [])) if isinstance(c, dict) else []
            lines.append(f'  {label}: {s}/{mx}')
            for n in notes[:2]:
                lines.append(f'    → {n}')
        lines += [f'  {"─"*40}', f'  TOTAL: {score}/100 → {verdict}']

        # MOAT ANALYSIS
        lines += ['', '=' * 55, 'SECTION 3: MOAT ANALYSIS', '=' * 55,
                  f'  Total: {moat_score}/25 — {moat_cls}',
                  f'  {moat.get("interpretation", "")}', '',
                  f'  {"MOAT Type":<22} {"Score":>6}  Key Evidence',
                  f'  {"─"*22} {"─"*6}  {"─"*25}']
        for dim in moat.get('dimensions', []):
            lbl = dim.get('label', '')
            sc = f'{dim.get("score", 0)}/5'
            ev = (dim.get('evidence') or ['—'])[0][:40]
            lines.append(f'  {lbl:<22} {sc:>6}  {ev}')
        lines += [f'  {"─"*22} {"─"*6}', f'  {"TOTAL":<22} {moat_score:>4}/25  {moat_cls}']

        # 4-FILTER SCORECARD
        lines += ['', '=' * 55, "SECTION 4: BUFFETT'S 4-FILTER SCORECARD", '=' * 55]
        filter_labels = {
            'enduring_competitive_advantage': 'Enduring Competitive Advantage',
            'management_quality': 'Management Quality',
            'sensible_price': 'Sensible Price (Margin of Safety)',
            'generates_fcf': 'Generates Free Cash Flow',
        }
        for key, label in filter_labels.items():
            f = filters.get(key, {})
            if f:
                icon = {'PASS': '✅', 'PARTIAL': '⚠️ ', 'FAIL': '❌', 'UNKNOWN': '❓'}.get(f.get('result', ''), '?')
                lines.append(f'  {icon} {label}: {f.get("result", "N/A")}')
                lines.append(f'     {f.get("detail", "")}')
        overall = filters.get('overall', {})
        lines += [f'', f'  Passed: {overall.get("pass_count", 0)}/4 — {overall.get("verdict", "")}']

        # INTRINSIC VALUE
        lines += ['', '=' * 55, 'SECTION 5: INTRINSIC VALUE & MARGIN OF SAFETY', '=' * 55]
        oe_dcf = val.get('owner_earnings_dcf', {})
        if oe_dcf and not oe_dcf.get('error'):
            oe_total = oe_dcf.get('owner_earnings_total')
            oe_ps = oe_dcf.get('owner_earnings_per_share')
            growth_pct = oe_dcf.get('growth_rate_used_pct', 'N/A')
            growth_src = oe_dcf.get('growth_source', '')
            if oe_total:
                lines.append(f'  Owner Earnings: ${oe_total/1e9:.2f}B (${oe_ps:.2f}/share)' if oe_ps else f'  Owner Earnings: ${oe_total/1e9:.2f}B')
            lines.append(f'  Growth Rate Used: {growth_pct}% ({growth_src})')
            iv_scenarios = oe_dcf.get('intrinsic_value_per_share', {})
            if iv_scenarios and not iv_scenarios.get('error'):
                lines.append('  Owner Earnings DCF (10yr, 10% discount):')
                for sc in ['conservative', 'base', 'optimistic']:
                    s = iv_scenarios.get(sc, {})
                    if isinstance(s, dict):
                        iv = s.get('total_intrinsic_value', 'N/A')
                        g = s.get('growth_rate_used', 'N/A')
                        lines.append(f'    {sc.title()}: ${iv}/share (at {g}% growth)')
        elif oe_dcf and oe_dcf.get('error'):
            lines.append(f'  Owner Earnings DCF: {oe_dcf["error"]}')
            lines.append(f'    Fallback: {oe_dcf.get("fallback", "")}')

        mos_dcf = val.get('margin_of_safety_dcf', {})
        mos_graham_v = val.get('margin_of_safety_graham', {})
        if mos_dcf and not mos_dcf.get('error'):
            lines.append(f'  Margin of Safety (DCF): {mos_dcf.get("margin_of_safety_pct")}% — {mos_dcf.get("signal", "")}')
        if mos_graham_v and not mos_graham_v.get('error'):
            lines.append(f'  Margin of Safety (Graham): {mos_graham_v.get("margin_of_safety_pct")}% — IV: ${mos_graham_v.get("intrinsic_value")}')

        gn = val.get('graham_number', {})
        if gn and not gn.get('error'):
            lines.append(f'  Graham Number: ${gn.get("graham_number", "N/A")} — {gn.get("note", "")}')

        roic = val.get('roic_analysis', {})
        if roic and not roic.get('error'):
            lines.append(f'  ROIC: {roic.get("roic_pct")}% | WACC: {roic.get("wacc_pct")}% | {roic.get("signal")}')

        # ANALYST CONSENSUS
        lines += ['', '=' * 55, 'SECTION 6: ANALYST CONSENSUS', '=' * 55]
        qs = data.get('quick_summary', {})
        n_analysts = qs.get('analyst_count', 'N/A')
        mean_rating = qs.get('analyst_mean', 'N/A')
        target_price = qs.get('target_price_avg', 'N/A')
        upside = qs.get('upside_to_target_pct', 'N/A')
        commentary = data.get('analyst_commentary', '')
        lines += [f'  Yahoo Finance: {n_analysts} analysts covering',
                  f'  Mean Consensus: {mean_rating} (1=Strong Buy, 5=Sell)',
                  f'  Price Target (avg): ${target_price} | Upside to Target: {upside}%',
                  f'  Signal: {commentary}',
                  '',
                  '  ⚡ TipRanks: Check tipranks.com for ≥3★ quality-weighted consensus',
                  '  📊 MarketBeat: 3-month consensus trend direction',
                  '  📈 StockAnalysis.com: EPS revision trend']

        # ENTRY CONDITIONS
        lines += ['', '=' * 55, 'SECTION 9: MARKET TIMING & ENTRY CONDITIONS', '=' * 55,
                  '  (Advisory only — does NOT affect Buffett Score)']
        for key, label in [('rsi', 'RSI (14d)'), ('vix', 'VIX'), ('week_52_position', '52-Week Position'),
                            ('earnings_proximity', 'Earnings')]:
            e = entry.get(key, {})
            if isinstance(e, dict) and e:
                val_str = e.get('value') or e.get('level') or e.get('position_pct') or ''
                sig = e.get('signal', '')
                icon = e.get('icon', '')
                lines.append(f'  {label}: {val_str} — {sig} {icon}')
        mom = entry.get('momentum', {})
        if mom:
            lines.append(f'  3-Month Momentum: {mom.get("momentum_3m_pct", "N/A")}%')
        entry_interp = entry.get('summary', {}).get('interpretation', '') if isinstance(entry.get('summary'), dict) else ''
        lines += [f'  Green Signals: {green}/4 — {entry_interp}']

        # RED FLAGS
        lines += ['', '=' * 55, 'SECTION 10: RED FLAGS', '=' * 55]
        if critical:
            lines.append('  🔴 CRITICAL:')
            for f in critical:
                lines.append(f'     • {f}')
        if caution:
            lines.append('  🟡 CAUTION:')
            for f in caution:
                lines.append(f'     • {f}')
        if not critical and not caution:
            lines.append('  ✅ No significant red flags detected')

    else:
        # ETF AUDIT SECTIONS
        # analyze_etf.py outputs fields at top level (expense_ratio, aum, holdings_analysis, etc.)
        lines += ['', '=' * 55, 'ETF EFFICIENCY AUDIT', '=' * 55]
        er = etf.get('expense_ratio', {})
        aum_d = etf.get('aum', {})
        beta_d = etf.get('beta', {})
        holdings = etf.get('holdings_analysis', {})
        mo = holdings.get('moat_overlap', {}) if holdings else {}
        ft = etf.get('factor_tilt', {})
        qs_etf = etf.get('quick_summary', {})
        etf_bs = etf.get('etf_buffett_score', {})
        top15_wt = qs_etf.get('top15_weight_pct', 'N/A') if qs_etf else 'N/A'
        moat_in = qs_etf.get('moat_in_top15', 'N/A') if qs_etf else 'N/A'
        top_checked = qs_etf.get('total_checked', 15) if qs_etf else 15
        pe = ft.get('pe_ratio') if ft else None
        comps = etf_bs.get('components', {}) if etf_bs else {}
        eff = comps.get('efficiency', {})
        div_q = comps.get('diversification_quality', {})
        fval = comps.get('factor_value', {})
        lines += [
            f'  Category: {etf.get("category", "N/A")}',
            f'  Expense Ratio: {er.get("value", "N/A")} — {er.get("rating", "")}',
            f'    Note: {er.get("note", "Check ETF.com for exact ratio")}',
            f'  AUM: {aum_d.get("value", "N/A")} — {aum_d.get("rating", "")}',
            f'  Beta: {beta_d.get("value", "N/A") if isinstance(beta_d, dict) else beta_d}',
            f'  Top 15 Concentration: {top15_wt}% of fund',
            f'  Moat Overlap: {moat_in}/{top_checked} top holdings pass Buffett quality check',
            f'  Factor P/E: {pe:.1f}x' if isinstance(pe, (int, float)) else '  Factor P/E: N/A',
            f'  Value Tilt: {ft.get("value_tilt","N/A")} | Income Tilt: {ft.get("income_tilt","N/A")}',
            f'  Bucket Recommendation: {etf_bs.get("bucket_recommendation", "N/A")}',
            '',
            '  ETF SCORE BREAKDOWN:',
            f'    Efficiency (expense/AUM/beta):    {eff.get("score","N/A")}/{eff.get("max",35)} pts',
            f'    Diversification (concentration):  {div_q.get("score","N/A")}/{div_q.get("max",35)} pts',
            f'    Factor Value (P/E vs S&P):        {fval.get("score","N/A")}/{fval.get("max",30)} pts',
            f'    TOTAL: {etf_bs.get("total_score","N/A")}/100 — {etf_bs.get("verdict","N/A")}',
        ]

    # FINAL SUMMARY
    lines += [f'', SEP, 'FINAL SUMMARY FOR SKILL INTEGRATION', SEP,
              f'Main Output Category:      {"Mode 1 ETF Audit" if is_etf else "Mode 1 Deep-Dive Stock"}',
              f'Buffett Score:             {score}/100 → {verdict}',
              f'MOAT:                      {moat_cls} ({moat_score}/25)' if not is_etf else f'ETF Score:                 {score}/100',
              f'Margin of Safety:          {mos_pct}%' if not is_etf else '',
              f'Analyst Consensus:         {data.get("quick_summary", {}).get("analyst_count", "N/A")} analysts — Source: Yahoo Finance',
              f'Strategy:                  {"Bucket A (ETF Core)" if is_etf else "Bucket B (MOAT Satellite)"}',
              f'Data Verification Path:    Yahoo Finance > Statistics tab',
              f'Analysis Depth:            Full Investment Memo',
              SEP]

    return '\n'.join(l for l in lines if l is not None)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: report_generator.py <TICKER> [--quick] [--output-dir <dir>]"}))
        sys.exit(1)

    ticker = sys.argv[1].upper().replace('$', '')
    quick_mode = '--quick' in sys.argv
    output_dir = '.'
    for i, arg in enumerate(sys.argv):
        if arg == '--output-dir' and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            break

    os.makedirs(output_dir, exist_ok=True)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Detect ETF
    is_etf = False
    try:
        r = subprocess.run([sys.executable, os.path.join(script_dir, 'fetch_data.py'), ticker],
                           capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            fd = json.loads(r.stdout)
            is_etf = fd.get('basic', {}).get('quote_type', '') == 'ETF'
    except Exception:
        pass

    # Run analysis
    script = 'analyze_etf.py' if is_etf else 'analyze_stock.py'
    args = [sys.executable, os.path.join(script_dir, script), ticker]
    if quick_mode:
        args.append('--quick')

    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(json.dumps({"error": f"Analysis failed: {result.stderr[:500]}"}))
            sys.exit(1)
        analysis_data = json.loads(result.stdout)
    except Exception as e:
        print(json.dumps({"error": f"Failed: {e}"}))
        sys.exit(1)

    # Generate charts
    charts = []
    if not quick_mode and HAS_MATPLOTLIB:
        # Get buffett score — for stocks it's nested under valuation, for ETFs it's etf_buffett_score
        if is_etf:
            bs = analysis_data.get('etf_buffett_score', {})
        else:
            bs = analysis_data.get('valuation', {}).get('buffett_score', {})
        score = bs.get('total_score', 0)
        charts.append(chart_buffett_gauge(score, ticker, output_dir))
        charts.append(chart_score_breakdown(bs, ticker, output_dir))
        if not is_etf:
            moat = analysis_data.get('moat_analysis', {})
            if moat:
                charts.append(chart_moat_radar(moat, ticker, output_dir))
            # Get current price from quick_summary
            current_price = analysis_data.get('quick_summary', {}).get('current_price')
            if current_price:
                charts.append(chart_valuation(analysis_data.get('valuation', {}),
                                              float(current_price),
                                              ticker, output_dir))
    charts = [c for c in charts if c]

    # Generate text report
    text = generate_text_report(analysis_data, charts)
    report_path = os.path.join(output_dir, f'{ticker}_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(text)

    # Extract summary fields from correct paths
    if is_etf:
        final_score = analysis_data.get('etf_buffett_score', {}).get('total_score')
        final_verdict = analysis_data.get('etf_buffett_score', {}).get('verdict')
    else:
        final_score = analysis_data.get('valuation', {}).get('buffett_score', {}).get('total_score')
        final_verdict = analysis_data.get('valuation', {}).get('buffett_score', {}).get('verdict') \
                        or analysis_data.get('quick_summary', {}).get('verdict')

    print(json.dumps({
        "ticker": ticker,
        "report_path": report_path,
        "charts": charts,
        "summary": {
            "buffett_score": final_score,
            "verdict": final_verdict,
            "moat": analysis_data.get('moat_analysis', {}).get('classification'),
        },
        "text_report": text,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
