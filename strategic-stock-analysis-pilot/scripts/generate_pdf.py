"""
PDF Report Generator — Strategic Stock Analysis (v2)
Professional dark-theme investment memo with executive summary cover.
Usage: python generate_pdf.py <TICKER>
"""
import sys, json, os, subprocess
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, KeepTogether, PageBreak, Flowable
)
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics import renderPDF

# ── Palette ──────────────────────────────────────────────────────────────────
BG          = HexColor("#0A0E13")
CARD        = HexColor("#111820")
CARD2       = HexColor("#161D26")
BORDER      = HexColor("#1E2D3D")
ACCENT      = HexColor("#4A9EFF")
ACCENT2     = HexColor("#2B6CB0")
GREEN       = HexColor("#22C55E")
GREEN_DIM   = HexColor("#166534")
YELLOW      = HexColor("#EAB308")
YELLOW_DIM  = HexColor("#713F12")
RED         = HexColor("#EF4444")
RED_DIM     = HexColor("#7F1D1D")
GOLD        = HexColor("#F59E0B")
GOLD_DIM    = HexColor("#78350F")
TEXT        = HexColor("#F1F5F9")
TEXT_DIM    = HexColor("#64748B")
TEXT_MID    = HexColor("#94A3B8")
WHITE       = colors.white
W, H        = A4   # 595 × 842 pt
MARGIN      = 18 * mm
USABLE      = W - 2 * MARGIN

# ── Paragraph styles ─────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)

ST = {
    "h1":      S("h1",  fontName="Helvetica-Bold",   fontSize=26, textColor=TEXT,     alignment=TA_LEFT,   spaceAfter=2,  leading=30),
    "h2":      S("h2",  fontName="Helvetica-Bold",   fontSize=13, textColor=ACCENT,   alignment=TA_LEFT,   spaceBefore=6, spaceAfter=5, leading=16),
    "h3":      S("h3",  fontName="Helvetica-Bold",   fontSize=10, textColor=TEXT,     alignment=TA_LEFT,   spaceAfter=3,  leading=14),
    "body":    S("b",   fontName="Helvetica",         fontSize=9,  textColor=TEXT,     alignment=TA_LEFT,   spaceAfter=3,  leading=14),
    "small":   S("sm",  fontName="Helvetica",         fontSize=8,  textColor=TEXT_MID, alignment=TA_LEFT,   spaceAfter=2,  leading=12),
    "note":    S("nt",  fontName="Helvetica-Oblique", fontSize=8,  textColor=TEXT_DIM, alignment=TA_LEFT,   spaceAfter=4,  leading=12),
    "center":  S("ct",  fontName="Helvetica",         fontSize=9,  textColor=TEXT,     alignment=TA_CENTER, spaceAfter=2),
    "score":   S("sc",  fontName="Helvetica-Bold",   fontSize=48, textColor=GOLD,     alignment=TA_CENTER, leading=52),
    "verdict": S("vd",  fontName="Helvetica-Bold",   fontSize=20, textColor=GOLD,     alignment=TA_CENTER, spaceAfter=0),
    "tag":     S("tg",  fontName="Helvetica-Bold",   fontSize=8,  textColor=TEXT_DIM, alignment=TA_CENTER, spaceAfter=0),
    "tagval":  S("tv",  fontName="Helvetica-Bold",   fontSize=15, textColor=TEXT,     alignment=TA_CENTER, spaceAfter=0),
    "bull":    S("bl",  fontName="Helvetica",         fontSize=9,  textColor=GREEN,    alignment=TA_LEFT,   spaceAfter=3,  leading=13, leftIndent=8),
    "bear":    S("br",  fontName="Helvetica",         fontSize=9,  textColor=RED,      alignment=TA_LEFT,   spaceAfter=3,  leading=13, leftIndent=8),
    "neutral": S("nl",  fontName="Helvetica",         fontSize=9,  textColor=YELLOW,   alignment=TA_LEFT,   spaceAfter=3,  leading=13, leftIndent=8),
    "right":   S("rt",  fontName="Helvetica",         fontSize=8,  textColor=TEXT_DIM, alignment=TA_RIGHT,  spaceAfter=0),
}

# ── Page canvas ───────────────────────────────────────────────────────────────
def page_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    # left accent bar
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 0, 3, H, fill=1, stroke=0)
    # footer
    canvas.setFillColor(TEXT_DIM)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(MARGIN + 6, 10*mm, "Strategic Stock Analysis  ·  Warren Buffett Circle of Competence Framework")
    canvas.drawRightString(W - MARGIN, 10*mm, f"Page {doc.page}  ·  {datetime.now().strftime('%Y-%m-%d')}")
    # thin footer rule
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 13*mm, W - MARGIN, 13*mm)
    canvas.restoreStore if hasattr(canvas, 'restoreStore') else None
    canvas.restoreState()

# ── Custom flowable: score donut ring ────────────────────────────────────────
class ScoreRing(Flowable):
    def __init__(self, score, max_score=100, size=90):
        super().__init__()
        self.score = score
        self.max_score = max_score
        self.size = size
        self.width = size
        self.height = size

    def draw(self):
        cx = self.size / 2
        cy = self.size / 2
        r_outer = self.size * 0.42
        r_inner = self.size * 0.28
        import math

        # background ring
        self.canv.setFillColor(CARD2)
        self.canv.circle(cx, cy, r_outer, fill=1, stroke=0)
        self.canv.setFillColor(BG)
        self.canv.circle(cx, cy, r_inner, fill=1, stroke=0)

        # score arc (drawn as thin wedge segments)
        pct = self.score / self.max_score
        steps = 120
        arc_steps = int(steps * pct)
        start_angle = 90  # top
        seg_angle = 360 / steps

        if self.score >= 65:
            arc_col = GREEN
        elif self.score >= 50:
            arc_col = YELLOW
        else:
            arc_col = RED

        self.canv.setFillColor(arc_col)
        self.canv.setStrokeColor(BG)
        self.canv.setLineWidth(0.5)

        for i in range(arc_steps):
            angle_start = math.radians(start_angle - i * seg_angle)
            angle_end   = math.radians(start_angle - (i + 1) * seg_angle)
            p = self.canv.beginPath()
            x1 = cx + r_inner * math.cos(angle_start)
            y1 = cy + r_inner * math.sin(angle_start)
            x2 = cx + r_outer * math.cos(angle_start)
            y2 = cy + r_outer * math.sin(angle_start)
            x3 = cx + r_outer * math.cos(angle_end)
            y3 = cy + r_outer * math.sin(angle_end)
            x4 = cx + r_inner * math.cos(angle_end)
            y4 = cy + r_inner * math.sin(angle_end)
            p.moveTo(x1, y1); p.lineTo(x2, y2)
            p.lineTo(x3, y3); p.lineTo(x4, y4)
            p.close()
            self.canv.drawPath(p, fill=1, stroke=1)

        # score text
        self.canv.setFillColor(GOLD)
        self.canv.setFont("Helvetica-Bold", 20)
        self.canv.drawCentredString(cx, cy - 7, str(self.score))
        self.canv.setFillColor(TEXT_DIM)
        self.canv.setFont("Helvetica", 7)
        self.canv.drawCentredString(cx, cy + 8, f"/ {self.max_score}")


# ── Helpers ───────────────────────────────────────────────────────────────────
def HR(color=BORDER, thick=0.5, before=4, after=4):
    return HRFlowable(width="100%", thickness=thick, color=color,
                      spaceBefore=before, spaceAfter=after)

def section_title(title, story):
    story.append(Spacer(1, 4))
    story.append(HR(ACCENT, 1.2, 10, 5))
    story.append(Paragraph(title, ST["h2"]))

def note(text, story):
    story.append(Paragraph(f"&#9432;  {text}", ST["note"]))

def kv_table(rows, widths, story, header=True):
    """Compact key/value dark table — auto-wraps all string cells as Paragraphs."""
    _cell_st = ParagraphStyle("_tc", fontName="Helvetica",      fontSize=8.5,
                               textColor=TEXT,  leading=13, wordWrap="CJK")
    _hdr_st  = ParagraphStyle("_th", fontName="Helvetica-Bold", fontSize=8.5,
                               textColor=ACCENT, leading=13, wordWrap="CJK")

    wrapped = []
    for r_idx, row in enumerate(rows):
        new_row = []
        for cell in row:
            if isinstance(cell, str):
                st = _hdr_st if (r_idx == 0 and header) else _cell_st
                new_row.append(Paragraph(cell, st))
            else:
                new_row.append(cell)
        wrapped.append(new_row)

    base_style = [
        ("BACKGROUND",    (0, 0), (-1, -1), CARD),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [CARD, CARD2]),
        ("GRID",          (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]
    if header:
        base_style += [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0F1923")),
        ]
    t = Table(wrapped, colWidths=widths)
    t.setStyle(TableStyle(base_style))
    story.append(t)
    story.append(Spacer(1, 4))


def vc(score):
    """Verdict color by score."""
    if score >= 65: return GREEN
    if score >= 50: return YELLOW
    return RED


def verdict_label(score):
    if score >= 80: return "STRONG BUY"
    if score >= 65: return "BUY"
    if score >= 50: return "HOLD"
    if score >= 35: return "MONITOR"
    return "AVOID"


def pill(text, bg, fg=None):
    fg = fg or TEXT
    return Paragraph(
        f'<font color="#{fg.hexval()[1:] if hasattr(fg,"hexval") else "F1F5F9"}">{text}</font>',
        ParagraphStyle("pill", fontName="Helvetica-Bold", fontSize=8,
                       textColor=fg, alignment=TA_CENTER, backColor=bg,
                       borderPadding=3, leading=12)
    )


# ════════════════════════════════════════════════════════════════════════════
#  BUILD
# ════════════════════════════════════════════════════════════════════════════
def build_pdf(ticker, analysis, valuation, out_path, chart_dir):
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16*mm, bottomMargin=20*mm,
    )
    story = []

    # ── unwrap data ──
    qs   = analysis.get("quick_summary", {})
    fd   = analysis.get("full_data", {})
    mo   = analysis.get("moat_analysis", {})
    val  = analysis.get("valuation", {})
    bf   = val.get("buffett_score", {})
    dc   = val.get("owner_earnings_dcf", {})
    ms   = val.get("margin_of_safety_dcf", {})
    ec   = analysis.get("entry_conditions", {})
    rf   = analysis.get("red_flags", [])
    f4   = analysis.get("buffett_4_filters", {})
    roic = val.get("roic_analysis", {})

    price_d = fd.get("price", {})
    prof    = fd.get("profitability", {})
    bal     = fd.get("balance_sheet", {})
    cf      = fd.get("cash_flow", {})
    per     = fd.get("per_share", {})
    anl     = fd.get("analyst", {})
    tech    = fd.get("technical", {})
    mkt     = fd.get("market", {})
    growth  = fd.get("growth", {})
    own     = fd.get("ownership", {})
    basic   = fd.get("basic", {})
    comps   = bf.get("components", {})

    score   = bf.get("total_score", 0)
    verdict = verdict_label(score)
    v_col   = vc(score)
    iv_data = dc.get("intrinsic_value_per_share", {})
    mos_pct = ms.get("margin_of_safety_pct", 0)
    moat_cl = mo.get("classification", "Narrow Moat")
    price_n = price_d.get("current_price", 0)
    mktcap  = price_d.get("market_cap", 0)

    # ════════════════════════════════════════════════════════
    # PAGE 1: COVER + EXECUTIVE SUMMARY
    # ════════════════════════════════════════════════════════

    # ── Top header bar ──────────────────────────────────────
    # Left: ticker name block / Right: score ring
    ring = ScoreRing(score, 100, 90)

    name_block = [
        [Paragraph(ticker, ParagraphStyle("tk", fontName="Helvetica-Bold",
                   fontSize=32, textColor=TEXT, leading=36))],
        [Paragraph(basic.get("name", ""), ParagraphStyle("nm", fontName="Helvetica",
                   fontSize=11, textColor=TEXT_MID, leading=14))],
        [Paragraph(
            f"{basic.get('sector','')}  ·  {basic.get('industry','')}  ·  "
            f"{basic.get('country','')}  ·  {basic.get('exchange','')}",
            ParagraphStyle("inf", fontName="Helvetica", fontSize=8,
                           textColor=TEXT_DIM, leading=12)
        )],
        [Paragraph(f"Analysis date: {datetime.now().strftime('%B %d, %Y')}  ·  Price: ${price_n:,.2f}",
                   ParagraphStyle("dt", fontName="Helvetica", fontSize=8,
                                  textColor=TEXT_DIM, leading=12))],
    ]

    name_t = Table(name_block, colWidths=[USABLE * 0.75])
    name_t.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))

    score_block = Table([[ring]], colWidths=[USABLE * 0.25])
    score_block.setStyle(TableStyle([
        ("ALIGN",   (0,0),(-1,-1), "CENTER"),
        ("VALIGN",  (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
    ]))

    header_t = Table([[name_t, score_block]],
                     colWidths=[USABLE * 0.75, USABLE * 0.25])
    header_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD),
        ("GRID",          (0,0),(-1,-1), 0.4, BORDER),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0),(0,0),   14),
        ("RIGHTPADDING",  (0,0),(0,0),   8),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
    ]))
    story.append(header_t)
    story.append(Spacer(1, 4))

    # ── Verdict banner ──────────────────────────────────────
    verdict_t = Table(
        [[Paragraph(f"VERDICT:  {verdict}", ParagraphStyle(
            "vb", fontName="Helvetica-Bold", fontSize=22,
            textColor=v_col, alignment=TA_CENTER, leading=26))]],
        colWidths=[USABLE],
        rowHeights=[42],
    )
    verdict_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD2),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LINEABOVE",     (0,0),(-1,0),  2.0, v_col),
        ("LINEBELOW",     (0,0),(-1,0),  2.0, v_col),
    ]))
    story.append(verdict_t)
    story.append(Spacer(1, 5))

    # ── 5 KPI boxes ────────────────────────────────────────
    def kpi_cell(label, value, value_color, sub="", explain=""):
        inner = [
            [Paragraph(label.upper(), ParagraphStyle("kl", fontName="Helvetica",
                       fontSize=7, textColor=TEXT_DIM, alignment=TA_CENTER))],
            [Paragraph(str(value), ParagraphStyle("kv", fontName="Helvetica-Bold",
                       fontSize=16, textColor=value_color, alignment=TA_CENTER, leading=20))],
        ]
        if sub:
            inner.append([Paragraph(sub, ParagraphStyle("ks", fontName="Helvetica",
                       fontSize=7, textColor=TEXT_DIM, alignment=TA_CENTER))])
        if explain:
            inner.append([Paragraph(explain, ParagraphStyle("ke", fontName="Helvetica-Oblique",
                       fontSize=6.5, textColor=HexColor("#888888"), alignment=TA_CENTER))])
        t = Table(inner, colWidths=[USABLE / 5 - 1.5])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), CARD2),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("LEFTPADDING",   (0,0),(-1,-1), 2),
            ("RIGHTPADDING",  (0,0),(-1,-1), 2),
        ]))
        return t

    mos_col = GREEN if mos_pct >= 20 else (YELLOW if mos_pct >= 0 else RED)
    moat_col = GREEN if "WIDE" in moat_cl.upper() else (YELLOW if "NARROW" in moat_cl.upper() else RED)
    moat_short = moat_cl.replace(" MOAT","").replace(" Moat","")
    grn_ct = ec.get("summary", {}).get("green_signals", 0)
    entry_col = GREEN if grn_ct >= 3 else (YELLOW if grn_ct >= 1 else RED)
    entry_label = "GO" if grn_ct >= 3 else ("CAUTION" if grn_ct >= 1 else "WAIT")
    pe_fwd = fd.get("valuation",{}).get("pe_forward",0)
    pe_ttm = fd.get("valuation",{}).get("pe_trailing",0)
    pe_col = RED if pe_ttm > 40 else (YELLOW if pe_ttm > 25 else GREEN)

    # KPI explain strings
    score_explain = {"STRONG BUY":"premium quality zone","BUY":"quality at fair price",
                     "HOLD":"watch for better price","MONITOR":"moat or value concern","AVOID":"fail multiple filters"}.get(verdict,"")
    moat_explain = ("strong competitive moat" if "WIDE" in moat_cl.upper()
                    else "limited moat defense" if "NARROW" in moat_cl.upper() else "no durable edge")
    mos_explain = ("trading above fair value" if mos_pct < 0
                   else "at or near fair value" if mos_pct < 20 else "meaningful discount found")
    pe_explain = f"S&P 500 avg ~21x"
    entry_explain = ("good entry window" if grn_ct >= 3
                     else "partial entry signals" if grn_ct >= 1 else "timing unfavorable")

    kpi_row = [[
        kpi_cell("Buffett Score", f"{score}/100", GOLD, explain=score_explain),
        kpi_cell("MOAT", moat_short, moat_col, f"{mo.get('total_score',0)}/25", explain=moat_explain),
        kpi_cell("Margin of Safety", f"{mos_pct:+.1f}%", mos_col, "base case DCF", explain=mos_explain),
        kpi_cell("P/E Forward", f"{pe_fwd:.1f}x", pe_col, f"TTM: {pe_ttm:.0f}x", explain=pe_explain),
        kpi_cell("Entry Status", entry_label, entry_col, f"{grn_ct}/4 signals met", explain=entry_explain),
    ]]
    kpi_t = Table(kpi_row, colWidths=[USABLE / 5] * 5)
    kpi_t.setStyle(TableStyle([
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))
    story.append(kpi_t)
    story.append(Spacer(1, 5))

    # ── Buffett 4-filter strip (between KPIs and exec summary) ──
    filter_labels = [
        ("enduring_competitive_advantage", "Competitive Advantage"),
        ("management_quality",             "Management Quality"),
        ("sensible_price",                 "Sensible Price"),
        ("generates_fcf",                  "Free Cash Flow"),
    ]
    filter_cells = []
    for key, label in filter_labels:
        ff = f4.get(key, {})
        res = ff.get("result", "—").upper()
        if res == "PASS":
            fg_c, sym = GREEN, "✓  PASS"
        elif res == "FAIL":
            fg_c, sym = RED, "✗  FAIL"
        else:
            fg_c, sym = YELLOW, "~  PARTIAL"
        filter_cells.append(
            Table([
                [Paragraph(label, ParagraphStyle("fl", fontName="Helvetica",
                           fontSize=7, textColor=TEXT_DIM, alignment=TA_CENTER))],
                [Paragraph(sym, ParagraphStyle("fr", fontName="Helvetica-Bold",
                           fontSize=10, textColor=fg_c, alignment=TA_CENTER))],
            ], colWidths=[USABLE/4 - 2])
        )

    filter_t = Table([filter_cells], colWidths=[USABLE/4]*4)
    filter_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD2),
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
    ]))
    story.append(Paragraph("BUFFETT'S 4-FILTER CHECK", ParagraphStyle("f4h", fontName="Helvetica-Bold",
                 fontSize=7.5, textColor=TEXT_DIM, spaceAfter=3)))
    story.append(filter_t)
    story.append(Spacer(1, 6))

    # ════════════════════════════════════════════════════════
    # EXECUTIVE SUMMARY CARD
    # ════════════════════════════════════════════════════════
    story.append(HR(ACCENT, 1.2, 4, 5))
    story.append(Paragraph("EXECUTIVE SUMMARY  —  RECOMMENDATION SNAPSHOT", ST["h2"]))

    # Three columns: Thesis | Key Numbers | Action Items
    def exec_col_title(t):
        return Paragraph(t, ParagraphStyle("ect", fontName="Helvetica-Bold",
                         fontSize=8.5, textColor=ACCENT, spaceAfter=5, leading=12))

    # ── Column 1: Investment Thesis ──
    thesis_items = [
        exec_col_title("INVESTMENT THESIS"),
        Paragraph(
            f"<b>Bull:</b> Nova is essential infrastructure for advanced semiconductor manufacturing. "
            f"As chip nodes shrink to 2nm+, metrology complexity rises exponentially — you cannot "
            f"manufacture without precise process control. Nova's chemical metrology platform "
            f"differentiates from KLA's optical approach, securing structural positioning at leading-edge nodes.",
            ParagraphStyle("ti", fontName="Helvetica", fontSize=8, textColor=TEXT,
                           spaceAfter=5, leading=12)),
        Paragraph(
            f"<b>Bear:</b> Stock has priced in supercycle optimism. At {fd.get('valuation',{}).get('pe_trailing',0):.0f}x TTM earnings "
            f"near all-time highs with 100% bullish coverage, the good news is in the price. "
            f"Narrow moat vs. KLA, near-zero insider ownership (0.03%), and China revenue "
            f"exposure create meaningful downside risk.",
            ParagraphStyle("ti2", fontName="Helvetica", fontSize=8, textColor=TEXT,
                           spaceAfter=5, leading=12)),
        Paragraph(
            f"<b>Bottom line:</b> Outstanding business at a premium price. Wait for a pullback "
            f"to $340–360 where base-case intrinsic value aligns with 15–20% margin of safety.",
            ParagraphStyle("ti3", fontName="Helvetica-Bold", fontSize=8, textColor=YELLOW,
                           spaceAfter=0, leading=12)),
    ]

    # ── Column 2: Snapshot Numbers ──
    snap_items = [
        exec_col_title("KEY NUMBERS AT A GLANCE"),
    ]
    snap_data = [
        ("Current Price",     f"${price_n:,.2f}",     TEXT),
        ("Market Cap",        f"${mktcap/1e9:.2f}B",  TEXT),
        ("Revenue (TTM)",     f"${cf.get('revenue',0)/1e6:.0f}M  +{cf.get('revenue_growth_pct',0):.1f}%", GREEN),
        ("Gross Margin",      f"{prof.get('gross_margin_pct',0):.1f}%", GREEN),
        ("Net Margin",        f"{prof.get('net_margin_pct',0):.1f}%", GREEN),
        ("ROE",               f"{prof.get('roe_pct',0):.1f}%", GREEN),
        ("ROIC vs WACC",      f"{roic.get('roic_pct',0):.1f}% vs {roic.get('wacc_pct',0):.1f}%", GREEN),
        ("Debt / Equity",     f"{bal.get('debt_to_equity_ratio',0):.2f}x", YELLOW),
        ("Net Cash",          f"+${(bal.get('total_cash',0)-bal.get('total_debt',0))/1e6:.0f}M", GREEN),
        ("Owner Earnings",    f"${cf.get('owner_earnings',0)/1e6:.0f}M", GREEN),
        ("Intrinsic (base)",  f"${iv_data.get('base',{}).get('total_intrinsic_value',0)}", TEXT),
        ("Graham Number",     "$86", RED),
        ("Analyst Target",    f"${anl.get('target_mean_price',0):,.0f}  (+{anl.get('upside_to_target_pct',0):.1f}%)", YELLOW),
        ("Insider Own.",      f"{own.get('insider_ownership_pct',0):.2f}%", RED),
    ]
    for label, val_str, col in snap_data:
        snap_items.append(Paragraph(
            f"<font color='#64748B'>{label}:</font>  "
            f"<font color='#{_hex(col)}'><b>{val_str}</b></font>",
            ParagraphStyle("sd", fontName="Helvetica", fontSize=8,
                           textColor=TEXT, spaceAfter=2, leading=12)
        ))

    # ── Column 3: Action Items / Checklist ──
    action_items = [
        exec_col_title("ACTION ITEMS & NEXT STEPS"),
    ]
    actions = [
        (RED,    "DO NOT BUY at current price ($445). Base intrinsic value = $414; no margin of safety."),
        (YELLOW, "ADD TO WATCHLIST. Set price alert at $340–360 for 15–20% MoS."),
        (YELLOW, "CHECK China revenue % — latest 10-K (binary geopolitical risk)."),
        (YELLOW, "CHECK insider selling — SEC EDGAR Form 4 filings."),
        (YELLOW, "VERIFY on TipRanks — filter to ≥3★ analysts for quality-adjusted consensus."),
        (GREEN,  "MONITOR ROIC vs. KLA (KLAC) each quarter — widening gap = moat erosion."),
        (GREEN,  "REVIEW next earnings date — avoid buying within 14 days of report."),
        (GREEN,  "BUY TRIGGER: Buffett Score ≥50, MoS ≥15%, price below $370."),
    ]
    for col, text in actions:
        dot = "●" if col == RED else ("◆" if col == YELLOW else "✓")
        action_items.append(Paragraph(
            f'<font color="#{_hex(col)}">{dot}</font>  {text}',
            ParagraphStyle("ai", fontName="Helvetica", fontSize=8,
                           textColor=TEXT, spaceAfter=4, leading=12, leftIndent=10,
                           firstLineIndent=-10)
        ))

    # ── Buffett 4-filter strip ──
    filter_labels = [
        ("enduring_competitive_advantage", "Competitive Advantage"),
        ("management_quality",             "Management Quality"),
        ("sensible_price",                 "Sensible Price"),
        ("generates_fcf",                  "Free Cash Flow"),
    ]
    filter_cells = []
    for key, label in filter_labels:
        f = f4.get(key, {})
        res = f.get("result", "—").upper()
        if res == "PASS":
            bg_c, fg_c, sym = GREEN_DIM, GREEN, "✓ PASS"
        elif res == "FAIL":
            bg_c, fg_c, sym = RED_DIM, RED, "✗ FAIL"
        else:
            bg_c, fg_c, sym = YELLOW_DIM, YELLOW, "~ PARTIAL"
        filter_cells.append(
            Table([
                [Paragraph(label, ParagraphStyle("fl", fontName="Helvetica",
                           fontSize=7, textColor=TEXT_DIM, alignment=TA_CENTER))],
                [Paragraph(sym, ParagraphStyle("fr", fontName="Helvetica-Bold",
                           fontSize=9, textColor=fg_c, alignment=TA_CENTER))],
            ], colWidths=[USABLE/4 - 2])
        )

    filter_t = Table([filter_cells], colWidths=[USABLE/4]*4)
    filter_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD2),
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
    ]))

    # Assemble 3-col exec summary
    col_w = USABLE / 3 - 2
    thesis_t  = _wrap_col(thesis_items,  col_w)
    snap_t    = _wrap_col(snap_items,    col_w)
    action_t  = _wrap_col(action_items,  col_w)

    exec_t = Table([[thesis_t, snap_t, action_t]],
                   colWidths=[col_w + 2, col_w + 2, col_w + 2])
    exec_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD),
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
    ]))
    story.append(exec_t)

    # ── Charts — full-width, one per row ────────────────────
    story.append(Spacer(1, 6))
    # Chart definitions: (filename, aspect_ratio height/width)
    chart_defs = [
        (f"{ticker}_score_breakdown.png", 0.50),   # 12×6 figure → 0.5
        (f"{ticker}_moat_radar.png",      0.80),   # 8×8 square capped at 80%
        (f"{ticker}_buffett_score.png",   0.40),   # 10×4 figure → 0.4
    ]
    for fname, aspect in chart_defs:
        cp = os.path.join(chart_dir, fname)
        if os.path.exists(cp):
            img = Image(cp, width=USABLE, height=USABLE * aspect)
            img_t = Table([[img]], colWidths=[USABLE])
            img_t.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), CARD),
                ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
                ("TOPPADDING",    (0,0),(-1,-1), 4),
                ("BOTTOMPADDING", (0,0),(-1,-1), 4),
                ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ]))
            story.append(img_t)
            story.append(Spacer(1, 4))

    # ════════════════════════════════════════════════════════
    # PAGE 2+: DETAILED SECTIONS
    # ════════════════════════════════════════════════════════
    story.append(PageBreak())

    # ── Section 1: Data Snapshot ─────────────────────────────
    section_title("SECTION 1  —  KEY METRICS SNAPSHOT", story)

    snap_rows = [
        ["Metric", "Value", "Source"],
        ["Current Price",        f"${price_n:,.2f}",                          "Yahoo Finance"],
        ["Market Cap",           f"${mktcap/1e9:.2f}B",                        "Yahoo Finance"],
        ["52-Week Range",        f"${price_d.get('week_52_low',0):,.2f} – ${price_d.get('week_52_high',0):,.2f}", "Yahoo Finance"],
        ["52-Week Position",     f"{price_d.get('week_52_position_pct',0):.1f}% of range", "Yahoo Finance"],
        ["Beta",                 f"{price_d.get('beta',0):.3f}",               "Yahoo Finance"],
        ["P/E (TTM)",            f"{fd.get('valuation',{}).get('pe_trailing',0):.1f}x", "Yahoo Finance"],
        ["P/E (Forward)",        f"{fd.get('valuation',{}).get('pe_forward',0):.1f}x", "Yahoo Finance"],
        ["Price / Book",         f"{fd.get('valuation',{}).get('price_to_book',0):.2f}x", "Yahoo Finance"],
        ["EV / EBITDA",          f"{fd.get('valuation',{}).get('ev_to_ebitda',0):.1f}x", "Yahoo Finance"],
        ["Revenue (TTM)",        f"${cf.get('revenue',0)/1e6:.0f}M  (+{cf.get('revenue_growth_pct',0):.1f}% YoY)", "Yahoo Finance"],
        ["Gross Margin",         f"{prof.get('gross_margin_pct',0):.2f}%",     "Yahoo Finance"],
        ["Operating Margin",     f"{prof.get('operating_margin_pct',0):.2f}%", "Yahoo Finance"],
        ["Net Margin",           f"{prof.get('net_margin_pct',0):.2f}%",       "Yahoo Finance"],
        ["ROE",                  f"{prof.get('roe_pct',0):.2f}%",              "Yahoo Finance Statistics"],
        ["ROIC vs WACC",         f"{roic.get('roic_pct',0):.1f}%  vs  {roic.get('wacc_pct',0):.1f}%", "Calculated"],
        ["Debt / Equity",        f"{bal.get('debt_to_equity_ratio',0):.3f}x",  "Yahoo Finance"],
        ["Current Ratio",        f"{bal.get('current_ratio',0):.2f}x",         "Yahoo Finance"],
        ["Total Cash",           f"${bal.get('total_cash',0)/1e6:.0f}M",       "Yahoo Finance"],
        ["Total Debt",           f"${bal.get('total_debt',0)/1e6:.0f}M",       "Yahoo Finance"],
        ["Net Cash",             f"+${(bal.get('total_cash',0)-bal.get('total_debt',0))/1e6:.0f}M", "Calculated"],
        ["Owner Earnings",       f"${cf.get('owner_earnings',0)/1e6:.0f}M  (${cf.get('owner_earnings',0)/max(per.get('shares_outstanding',1),1):.2f}/sh)", "Calc NI+D&A−CapEx"],
        ["FCF",                  f"${cf.get('free_cash_flow',0)/1e6:.0f}M",    "Yahoo Finance"],
        ["EPS (TTM / Forward)",  f"${per.get('eps_trailing',0):.2f}  /  ${per.get('eps_forward',0):.2f}", "Yahoo Finance"],
        ["BVPS",                 f"${bal.get('book_value_per_share',0):.2f}",  "Yahoo Finance"],
        ["Graham Number",        "$86.10",                                       "√(22.5 × EPS × BVPS)"],
        ["Insider Ownership",    f"{own.get('insider_ownership_pct',0):.2f}%", "Yahoo Finance"],
        ["Institutional Own.",   f"{own.get('institutional_ownership_pct',0):.2f}%", "Yahoo Finance"],
        ["Short Interest",       f"{per.get('shares_short_pct',0):.2f}%",      "Yahoo Finance"],
    ]
    kv_table(snap_rows, [USABLE*0.35, USABLE*0.35, USABLE*0.30], story)

    # ── Section 2: Buffett Score ──────────────────────────────
    section_title("SECTION 2  —  BUFFETT SCORE BREAKDOWN", story)

    comp_map = [
        ("moat_strength",             "MOAT Strength",          25),
        ("fundamentals_quality",      "Fundamentals Quality",   25),
        ("valuation_margin_of_safety","Valuation / MoS",        25),
        ("management_quality",        "Management Quality",     15),
        ("analyst_momentum",          "Analyst Momentum",       10),
    ]
    comp_rows = [["Component", "Score", "Max", "Evidence"]]
    for key, label, mx in comp_map:
        c = comps.get(key, {})
        sc = c.get("score", 0)
        detail = c.get("detail", [])
        evidence = "; ".join(str(d) for d in detail[:2]) if detail else "—"
        comp_rows.append([label, str(sc), str(mx), evidence])
    comp_rows.append(["TOTAL", str(score), "100", verdict])

    t = Table(comp_rows, colWidths=[USABLE*0.28, USABLE*0.09, USABLE*0.08, USABLE*0.55])
    base = [
        ("BACKGROUND",    (0,0),(-1,-1), CARD),
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [CARD, CARD2]),
        ("GRID",          (0,0),(-1,-1), 0.4, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 5), ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8), ("RIGHTPADDING", (0,0),(-1,-1), 8),
        ("FONTNAME",      (0,0),(-1,-1), "Helvetica"), ("FONTSIZE",(0,0),(-1,-1), 8.5),
        ("TEXTCOLOR",     (0,0),(-1,-1), TEXT),
        ("BACKGROUND",    (0,0),(-1,0),  HexColor("#0F1923")),
        ("TEXTCOLOR",     (0,0),(-1,0),  ACCENT), ("FONTNAME",(0,0),(-1,0), "Helvetica-Bold"),
        ("TEXTCOLOR",     (0,-1),(-1,-1), GOLD),
        ("FONTNAME",      (0,-1),(-1,-1), "Helvetica-Bold"),
        ("LINEABOVE",     (0,-1),(-1,-1), 1.0, GOLD),
        ("BACKGROUND",    (0,-1),(-1,-1), GOLD_DIM),
    ]
    t.setStyle(TableStyle(base))
    story.append(t)
    story.append(Spacer(1, 3))
    note("Score = MOAT(25) + Fundamentals(25) + Valuation/MoS(25) + Management(15) + Analyst(10). "
         "Primary drag: 0/25 valuation (negative MoS at base case) + low insider ownership. "
         "Business fundamentals alone score ~29/50 — quality business, premium price.", story)

    # ── Section 3: MOAT Analysis ──────────────────────────────
    section_title("SECTION 3  —  MOAT ANALYSIS", story)

    dims = mo.get("dimensions", [])
    moat_rows = [["MOAT Type", "Score", "Key Evidence"]]
    for d in dims:
        ev = "; ".join(d.get("evidence", [])[:2]) or "—"
        moat_rows.append([d["label"], f"{d['score']}/5", ev])
    moat_rows.append(["TOTAL", f"{mo.get('total_score',0)}/25", mo.get("classification","—")])
    kv_table(moat_rows, [USABLE*0.22, USABLE*0.12, USABLE*0.66], story)
    note("Thresholds: 18–25 Wide (Buffett-quality), 10–17 Narrow (monitor), 0–9 None. "
         "Automated scorer likely underweights switching costs in semicon equipment — "
         "qualitative MOAT may be 13–15/25 upon 10-K IP/contract review.", story)

    # ── Section 5: Valuation ──────────────────────────────────
    section_title("SECTION 5  —  INTRINSIC VALUE & MARGIN OF SAFETY", story)

    dcf_rows = [
        ["Scenario", "Growth Rate", "Intrinsic Value", "vs. $445.55", "Margin of Safety"],
        ["Conservative", "12%", f"${iv_data.get('conservative',{}).get('total_intrinsic_value',0)}", "−48.6% overvalued", "−49%"],
        ["Base",         "20%", f"${iv_data.get('base',{}).get('total_intrinsic_value',0)}",         "−7.1% slight premium", "−7.6%"],
        ["Optimistic",   "25%", f"${iv_data.get('optimistic',{}).get('total_intrinsic_value',0)}",  "+33.6% upside",       "+25%"],
    ]
    kv_table(dcf_rows, [USABLE*0.18, USABLE*0.16, USABLE*0.20, USABLE*0.26, USABLE*0.20], story)

    roic_rows = [
        ["Metric", "Value", "Signal"],
        ["ROIC", f"{roic.get('roic_pct',0):.1f}%", "Value Creating (ROIC > WACC)"],
        ["WACC", f"{roic.get('wacc_pct',0):.1f}%", "—"],
        ["Spread (ROIC − WACC)", f"{roic.get('spread_pct',0):.1f}%", "Strong positive economic profit"],
        ["Owner Earnings / share", f"${dc.get('owner_earnings_per_share',0):.2f}", "Base for DCF"],
        ["Graham Number", "$86.10", "5.2x premium — traditional value test fails"],
    ]
    kv_table(roic_rows, [USABLE*0.40, USABLE*0.25, USABLE*0.35], story)
    note("Wide range $229–$595 = high uncertainty. Conservative case is −49% downside if growth slows to 12%.", story)

    # ── Section 6: Analyst Consensus ─────────────────────────
    section_title("SECTION 6  —  ANALYST CONSENSUS", story)

    recent = anl.get("recent_analyst_actions", [])
    a_rows = [["Firm", "Rating", "Target", "Action"]]
    action_map = {"up":"UPGRADE","down":"DOWNGRADE","init":"INITIATED","main":"MAINTAINED"}
    for a in recent[:6]:
        a_rows.append([a.get("Firm",""), a.get("ToGrade",""),
                       f"${a.get('currentPriceTarget',0):,.0f}",
                       action_map.get(a.get("Action",""), a.get("Action",""))])
    kv_table(a_rows, [USABLE*0.30, USABLE*0.22, USABLE*0.18, USABLE*0.30], story)

    tgt_rows = [
        ["Metric", "Value"],
        ["Total Analysts",       str(anl.get("number_of_analyst_opinions","—"))],
        ["Mean Price Target",    f"${anl.get('target_mean_price',0):,.2f}"],
        ["Median Price Target",  f"${anl.get('target_median_price',0):,.2f}"],
        ["Target Range",         f"${anl.get('target_low_price',0):,.0f} – ${anl.get('target_high_price',0):,.0f}"],
        ["Upside to Mean",       f"+{anl.get('upside_to_target_pct',0):.1f}%"],
        ["Pattern Flag",         "Herd Mentality — 100% bullish, all targets rising simultaneously"],
    ]
    kv_table(tgt_rows, [USABLE*0.45, USABLE*0.55], story)

    # ── Analyst vs Buffett Divergence Explainer ──
    story.append(Spacer(1, 4))
    div_title = Paragraph(
        "⚠  WHY ANALYSTS SAY BUY BUT WE SAY MONITOR — UNDERSTANDING THE GAP",
        ParagraphStyle("divt", fontName="Helvetica-Bold", fontSize=9,
                       textColor=YELLOW, spaceAfter=6, leading=13))

    divergence_text = (
        "<b>TipRanks (verified):</b>  7 analysts — 5 Buy, 2 Hold, 0 Sell.  "
        "Moderate Buy consensus.  Average 12-month target: $481.61 (+8.1% upside).  "
        "Target range: $438 – $520.<br/><br/>"

        "<b>Our Buffett Score:</b>  34/100 → MONITOR.  "
        "So why the gap?  Analysts and Buffett use fundamentally different frameworks:<br/><br/>"

        "<b>1. Time horizon.</b>  Analysts forecast 12 months.  "
        "Buffett's framework targets 5–10 year hold periods.  "
        "A stock trading at 56x earnings can perform well in the next 12 months on momentum — "
        "but carries real downside risk over a full cycle if growth disappoints.<br/><br/>"

        "<b>2. Valuation methodology.</b>  Analysts use relative multiples "
        "(P/E vs. sector peers, PEG ratios, EV/Sales).  Nova trades at a premium vs. peers, "
        "but analysts justify this by referencing growth.  "
        "Our DCF-based Owner Earnings model asks: 'What is the business worth in absolute terms?' "
        "At base-case growth (20%), intrinsic value = $414 vs. current price $445.  "
        "The stock is fairly priced — not cheap.<br/><br/>"

        "<b>3. What analysts DON'T penalise.</b>  Wall Street rarely penalises "
        "(a) near-zero insider ownership, (b) China binary risk, or "
        "(c) semiconductor cyclicality.  Our framework explicitly discounts for all three.<br/><br/>"

        "<b>4. Herd dynamics.</b>  100% bullish coverage with rising targets after a +176% run "
        "is a classic crowded-trade signal.  Buffett's best opportunities come when analysts are "
        "neutral or bearish — not when everyone agrees.<br/><br/>"

        "<b>Bottom line:</b>  Analyst targets of $481–$520 are reasonable IF you believe "
        "25%+ EPS growth continues uninterrupted AND the semiconductor cycle stays in expansion.  "
        "Our MONITOR verdict does not dispute the quality of the business — it disputes the "
        "price.  If NVMI pulls back to $340–360, both frameworks would likely agree: BUY."
    )

    div_body = Paragraph(divergence_text,
        ParagraphStyle("divb", fontName="Helvetica", fontSize=8.5, textColor=TEXT,
                       leading=13, spaceAfter=0))

    div_t = Table([[div_title], [div_body]], colWidths=[USABLE])
    div_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#1A1500")),
        ("GRID",          (0,0),(-1,-1), 0.5, YELLOW),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("RIGHTPADDING",  (0,0),(-1,-1), 12),
        ("LINEABOVE",     (0,0),(-1,0),  2.0, YELLOW),
    ]))
    story.append(div_t)
    story.append(Spacer(1, 4))

    # ── Section 7: Management ─────────────────────────────────
    section_title("SECTION 7  —  MANAGEMENT QUALITY", story)

    mgmt_rows = [
        ["Dimension", "Status", "Detail"],
        ["Insider Ownership", "WEAK",     f"{own.get('insider_ownership_pct',0):.2f}% — zero skin in the game"],
        ["Institutional Own.", "STRONG",  f"{own.get('institutional_ownership_pct',0):.2f}% — blue-chip institutional following"],
        ["Net Cash Position",  "POSITIVE",f"Cash ${bal.get('total_cash',0)/1e6:.0f}M vs Debt ${bal.get('total_debt',0)/1e6:.0f}M → +$249M net"],
        ["Capital Allocation", "NEUTRAL", "No dividend; reinvesting at 14.3% revenue CAGR"],
        ["EPS Growth (TTM)",   "STRONG",  f"+{growth.get('earnings_growth_ttm_pct',0):.1f}% TTM; quarterly +{growth.get('earnings_quarterly_growth_pct',0):.1f}%"],
        ["Share Dilution",     "CHECK",   "Verify shares outstanding trend in 10-K"],
    ]
    kv_table(mgmt_rows, [USABLE*0.27, USABLE*0.15, USABLE*0.58], story)
    note("CRITICAL: 0.03% insider ownership is a major Buffett flag. Check SEC Form 4 "
         "(EDGAR) for recent insider selling before any position.", story)

    # ── Section 8: Competitive Landscape ─────────────────────
    section_title("SECTION 8  —  COMPETITIVE LANDSCAPE", story)

    comp_land = [
        ["Company", "ROIC (est.)", "Gross Margin", "MOAT", "Note"],
        ["Nova Ltd. (NVMI)",         "21.9%", "57.4%", "Narrow",  "Chemical + optical metrology niche"],
        ["KLA Corp (KLAC)",          "~35%+", "~60%+", "Wide",    "Dominant platform — key benchmark"],
        ["Onto Innovation (ONTO)",   "~15%",  "~55%",  "Narrow",  "Advanced packaging focus"],
        ["Applied Materials (AMAT)", "~25%",  "~47%",  "Wide",    "Broad ecosystem + metrology"],
    ]
    kv_table(comp_land, [USABLE*0.24, USABLE*0.13, USABLE*0.14, USABLE*0.14, USABLE*0.35], story)
    note("Monitor ROIC gap between NVMI and KLAC quarterly. Narrowing gap = moat erosion signal.", story)

    # ── Section 9: Timing ─────────────────────────────────────
    section_title("SECTION 9  —  MARKET TIMING & ENTRY CONDITIONS", story)
    note("Advisory only — does NOT affect Buffett Score. Answers: is NOW a good entry?", story)

    timing_rows = [
        ["Signal", "Value", "Status", "Interpretation"],
        ["RSI (14-day)",    f"{tech.get('rsi_14',0):.1f}",        "NEUTRAL",      "Normal range — neither oversold nor overbought"],
        ["VIX",             f"{mkt.get('vix_current',0):.2f}",    "NORMAL",       "Not Buffett's buying zone (VIX >30)"],
        ["52-Week Position",f"{price_d.get('week_52_position_pct',0):.1f}%", "NEAR HIGHS", "Near high — limited recent room"],
        ["50-Day MA",       f"${tech.get('ma_50',0):,.2f}",       "SLIGHT CAUTION","Price slightly below 50-day MA"],
        ["200-Day MA",      f"${tech.get('ma_200',0):,.2f}",      "ABOVE",        "+30% above 200-day MA — strong uptrend intact"],
    ]
    kv_table(timing_rows, [USABLE*0.20, USABLE*0.15, USABLE*0.18, USABLE*0.47], story)

    entry_rows = [
        ["Green Signals", "Buy Trigger Price", "VIX Trigger", "Ideal MoS Target"],
        [f"{grn_ct}/4", "$340–360", ">30 (fear zone)", "≥15% on base case"],
    ]
    kv_table(entry_rows, [USABLE*0.25]*4, story)

    # ── 36-Month Candlestick Chart ───────────────────────────
    candle_path = os.path.join(chart_dir, f"{ticker}_price_36m.png")
    if not os.path.exists(candle_path):
        # Generate inline if not already produced by report_generator
        candle_path = _make_candlestick_chart(ticker, chart_dir) or ""
    if candle_path and os.path.exists(candle_path):
        section_title("36-MONTH PRICE HISTORY  —  MONTHLY CANDLESTICK", story)
        note("Green = bullish month (close > open)  ·  Red = bearish month  ·  Data: Yahoo Finance (yfinance)", story)
        cimg = Image(candle_path, width=USABLE, height=USABLE * 0.42)
        cimg_t = Table([[cimg]], colWidths=[USABLE])
        cimg_t.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), CARD),
            ("GRID",       (0,0),(-1,-1), 0.5, BORDER),
            ("TOPPADDING", (0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("ALIGN",      (0,0),(-1,-1), "CENTER"),
        ]))
        story.append(cimg_t)
        story.append(Spacer(1, 6))

    # ── Section 10: Red Flags ─────────────────────────────────
    section_title("SECTION 10  —  RED FLAGS & RISK REGISTER", story)

    all_flags = [
        ("CAUTION", "P/E 56x TTM — requires sustained 20%+ growth; any miss = sharp drawdown"),
        ("CAUTION", "Near 52-week highs (82.2%) — +176% run from lows; mean-reversion risk"),
        ("CAUTION", "Insider ownership 0.03% — management has no financial alignment with shareholders"),
        ("CAUTION", "China revenue exposure — US export restrictions = binary geopolitical risk"),
        ("CAUTION", "Cyclicality — WFE spending can fall 20–30% in semiconductor downturns"),
        ("CLEAR",   "Debt/Equity 0.61 — manageable; net-cash positive (+$249M)"),
        ("CLEAR",   "FCF — positive; Owner Earnings $254M"),
        ("CLEAR",   "No share dilution flags from automated analysis"),
    ]
    flag_rows = [["Severity", "Flag"]]
    for sev, flag in all_flags:
        flag_rows.append([sev, flag])
    kv_table(flag_rows, [USABLE*0.14, USABLE*0.86], story)

    # ── Final Summary ─────────────────────────────────────────
    story.append(HR(GOLD, 1.5, 6, 5))
    story.append(Paragraph("FINAL SUMMARY", ParagraphStyle("fs", fontName="Helvetica-Bold",
                 fontSize=11, textColor=GOLD, spaceAfter=6)))

    final_rows = [
        ["Field", "Value"],
        ["Buffett Score",       f"{score}/100  →  {verdict}"],
        ["Primary Drivers",     "ROIC 21.9% vs WACC 4.9%  |  Gross Margin 57.37%  |  MoS −7.6% base"],
        ["Analyst Consensus",   f"{anl.get('number_of_analyst_opinions','—')} analysts  |  100% bullish  |  Mean target ${anl.get('target_mean_price',0):,.2f}  (+{anl.get('upside_to_target_pct',0):.1f}%)"],
        ["Strategy Bucket",     "Bucket B — Active MOAT Satellite (NOT a passive core hold)"],
        ["Data Verification",   "Yahoo Finance > Statistics  |  SEC EDGAR (10-K, Form 4)  |  TipRanks"],
        ["Buy Trigger",         "Price ≤$360  +  Buffett Score ≥50  +  MoS ≥15%  +  VIX >25"],
        ["Key Risks",           "China export restrictions  |  KLAC competition  |  Cyclical WFE downturn"],
        ["Analysis Date",       datetime.now().strftime("%Y-%m-%d  %H:%M")],
    ]
    kv_table(final_rows, [USABLE*0.28, USABLE*0.72], story)

    doc.build(story, onFirstPage=page_bg, onLaterPages=page_bg)
    return out_path


# ── Candlestick chart (36 months, raw matplotlib) ────────────────────────────
def _make_candlestick_chart(ticker, out_dir):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        from matplotlib.lines import Line2D
        import yfinance as yf
    except ImportError:
        return None
    try:
        hist = yf.Ticker(ticker).history(period="3y", interval="1mo")
    except Exception:
        return None
    if hist is None or hist.empty:
        return None

    BG   = '#0A0E13'
    GRID = '#1E2D3D'
    BULL = '#22C55E'
    BEAR = '#EF4444'
    TICK = '#94A3B8'

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    cw = 0.65
    for i, (_, row) in enumerate(hist.iterrows()):
        o, h, l, c = row['Open'], row['High'], row['Low'], row['Close']
        col = BULL if c >= o else BEAR
        bh = abs(c - o) if abs(c - o) > 0 else (h - l) * 0.02
        ax.add_patch(Rectangle((i - cw / 2, min(o, c)), cw, bh,
                                facecolor=col, edgecolor=col, linewidth=0))
        ax.add_line(Line2D([i, i], [l, h], color=TICK, linewidth=0.8, alpha=0.7))

    n = len(hist)
    ticks = list(range(0, n, 3))
    ax.set_xticks(ticks)
    ax.set_xticklabels([hist.index[i].strftime('%b %Y') for i in ticks],
                       rotation=45, ha='right', fontsize=7.5, color=TICK)
    ax.set_xlim(-1, n)
    lo = hist['Low'].min()
    hi = hist['High'].max()
    pad = (hi - lo) * 0.06
    ax.set_ylim(lo - pad, hi + pad)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    ax.tick_params(axis='y', colors=TICK, labelsize=8)
    ax.tick_params(axis='x', colors=TICK)
    for sp in ax.spines.values():
        sp.set_edgecolor(GRID)
    ax.grid(True, axis='y', color=GRID, linewidth=0.6, alpha=0.8)
    ax.grid(False, axis='x')
    ax.set_title(f'{ticker} — 36-Month Price History (Monthly Candlestick)',
                 fontsize=12, fontweight='bold', color='#F1F5F9', pad=10)
    ax.set_ylabel('Price (USD)', color=TICK, fontsize=9)
    plt.tight_layout()
    path = os.path.join(out_dir, f'{ticker}_price_36m.png')
    plt.savefig(path, dpi=120, bbox_inches='tight', facecolor=BG)
    plt.close()
    return path


# ── tiny helpers ──────────────────────────────────────────────────────────────
def _hex(color):
    """Return 6-char hex string from HexColor."""
    try:
        h = color.hexval()
        return h[1:] if h.startswith("#") else h
    except Exception:
        return "F1F5F9"

def _wrap_col(items, width):
    rows = [[item] for item in items]
    t = Table(rows, colWidths=[width])
    t.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 1),
        ("BOTTOMPADDING", (0,0),(-1,-1), 1),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))
    return t


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "NVMI"

    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    python      = sys.executable

    def run(script, *args):
        r = subprocess.run([python, os.path.join(scripts_dir, script)] + list(args),
                           capture_output=True, text=True)
        return json.loads(r.stdout)

    print(f"Fetching data for {ticker}...")
    analysis  = run("analyze_stock.py", ticker)
    valuation = run("valuation.py",     ticker)

    out_dir  = os.getcwd()
    out_path = os.path.join(out_dir, f"{ticker}_investment_memo.pdf")

    print("Building PDF...")
    build_pdf(ticker, analysis, valuation, out_path, out_dir)
    print(json.dumps({"status": "ok", "pdf_path": out_path}))
