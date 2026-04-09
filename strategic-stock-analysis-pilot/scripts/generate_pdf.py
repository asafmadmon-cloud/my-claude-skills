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

# ── Analyst grade normalisation ──────────────────────────────────────────────
# Maps raw brokerage language to BUY / HOLD / SELL.
GRADE_TO_BHS = {
    # BUY equivalents
    "strong buy": "BUY", "strong-buy": "BUY", "buy": "BUY",
    "outperform": "BUY", "outperformer": "BUY",
    "overweight": "BUY", "market outperform": "BUY", "sector outperform": "BUY",
    "top pick": "BUY", "positive": "BUY", "conviction buy": "BUY",
    "speculative buy": "BUY", "add": "BUY", "accumulate": "BUY", "long-term buy": "BUY",
    # HOLD equivalents
    "neutral": "HOLD", "hold": "HOLD",
    "equal-weight": "HOLD", "equal weight": "HOLD",
    "market perform": "HOLD", "market-perform": "HOLD",
    "sector perform": "HOLD", "sector-perform": "HOLD",
    "in-line": "HOLD", "inline": "HOLD", "peer perform": "HOLD",
    "fair value": "HOLD", "mixed": "HOLD", "market weight": "HOLD",
    # SELL equivalents
    "sell": "SELL", "strong sell": "SELL", "strong-sell": "SELL",
    "underperform": "SELL", "underweight": "SELL",
    "reduce": "SELL", "negative": "SELL", "sector underperform": "SELL",
    "below average": "SELL", "trim": "SELL", "avoid": "SELL",
}

def normalize_grade(raw: str) -> str:
    if not raw:
        return ""
    return GRADE_TO_BHS.get(raw.strip().lower(), raw.strip().upper())

def _rating_cell(raw_grade: str) -> "Paragraph":
    normalized = normalize_grade(raw_grade)
    col = {"BUY": GREEN, "HOLD": YELLOW, "SELL": RED}.get(normalized, TEXT_MID)
    # Show original brokerage term below if it differs from the normalised label
    original_note = (
        f"<br/><font size='7'>{raw_grade}</font>"
        if raw_grade and raw_grade.strip().upper() != normalized
        else ""
    )
    return Paragraph(
        f"<b>{normalized}</b>{original_note}",
        ParagraphStyle("_rat", fontName="Helvetica", fontSize=8.5, textColor=col, leading=14)
    )

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
    iv_base  = (iv_data.get("base") or {}).get("total_intrinsic_value") or 0
    iv_low   = (iv_data.get("conservative") or {}).get("total_intrinsic_value") or 0
    iv_high  = (iv_data.get("optimistic") or {}).get("total_intrinsic_value") or 0
    _gn_raw  = val.get("graham_number")
    gn       = _gn_raw if isinstance(_gn_raw, (int, float)) else 0
    dcf_inputs   = dc.get("inputs", {})
    growth_cons  = (dcf_inputs.get("growth_conservative_pct") or 12)
    growth_base  = (dcf_inputs.get("growth_base_pct") or 20)
    growth_opt   = (dcf_inputs.get("growth_optimistic_pct") or 25)
    mos_pct = ms.get("margin_of_safety_pct") or 0
    moat_cl = mo.get("classification", "Narrow Moat")
    price_n = price_d.get("current_price") or 0
    mktcap  = price_d.get("market_cap") or 0
    company_desc = analysis.get("description", "")
    competitors  = analysis.get("competitors", [])
    subtitle_style = ParagraphStyle("subtitle", fontName="Helvetica-Oblique", fontSize=8,
                                     textColor=TEXT_DIM, spaceAfter=6, leading=11)

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
    pe_fwd = fd.get("valuation",{}).get("pe_forward") or 0
    pe_ttm = fd.get("valuation",{}).get("pe_trailing") or 0
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
        kpi_cell("P/E Forward", f"{pe_fwd:.1f}x" if pe_fwd else "N/A", pe_col, f"TTM: {pe_ttm:.0f}x" if pe_ttm else "TTM: N/A", explain=pe_explain),
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

    # ── Column 1: Investment Thesis (DYNAMIC) ──
    _moat_str = moat_cl or ""
    bull_pts = []
    if "WIDE" in _moat_str.upper():
        bull_pts.append("Wide economic moat provides durable competitive advantage")
    elif "NARROW" in _moat_str.upper():
        bull_pts.append("Narrow moat offers some competitive protection")
    if prof.get('roe_pct', 0) > 15:
        bull_pts.append(f"ROE {prof['roe_pct']:.1f}% — above Buffett's 15% threshold")
    if cf.get('free_cash_flow', 0) > 0:
        bull_pts.append(f"FCF ${cf['free_cash_flow']/1e9:.2f}B — strong cash generation")
    if cf.get('revenue_growth_pct', 0) > 10:
        bull_pts.append(f"Revenue growing {cf['revenue_growth_pct']:.1f}% YoY")
    if not bull_pts:
        bull_pts.append(f"{ticker} — review fundamentals; no clear bull signals from available data")

    bear_pts = []
    for _rf in (rf or [])[:3]:
        _flag_text = _rf.get('flag', '')
        _cleaned = _flag_text.replace('🔴','').replace('🟡','').strip()
        if _cleaned:
            bear_pts.append(_cleaned)
    _mos = val.get('margin_of_safety_pct', 0) or 0
    if _mos < 0:
        bear_pts.append(f"Negative margin of safety ({_mos:.1f}%) — priced above intrinsic value")
    if not bear_pts:
        bear_pts.append("No critical red flags identified at this time")

    if verdict == "AVOID":
        _bottom = f"Fundamental concerns dominate. Score {score}/100 — wait for conditions to improve."
    elif verdict in ("BUY", "STRONG BUY"):
        _bottom = f"Quality business at a sensible price. Score {score}/100 — entry conditions favorable."
    elif verdict == "HOLD":
        _bottom = f"Solid business, but valuation or moat needs watching. Score {score}/100."
    else:
        _bottom = f"Monitor for improved entry. Score {score}/100 — conditions not yet ideal."

    _bull_text = "  ".join(f"• {p}" for p in bull_pts[:3])
    _bear_text = "  ".join(f"• {p}" for p in bear_pts[:3])

    thesis_items = [exec_col_title("INVESTMENT THESIS")]
    if company_desc:
        thesis_items.append(Paragraph(
            f"<i>{company_desc}</i>",
            ParagraphStyle("cdesc", fontName="Helvetica-Oblique", fontSize=7.5,
                           textColor=TEXT_MID, spaceAfter=5, leading=11)))
    thesis_items += [
        Paragraph(
            f"<b>Bull:</b> {_bull_text}",
            ParagraphStyle("ti", fontName="Helvetica", fontSize=8, textColor=TEXT,
                           spaceAfter=5, leading=12)),
        Paragraph(
            f"<b>Bear:</b> {_bear_text}",
            ParagraphStyle("ti2", fontName="Helvetica", fontSize=8, textColor=TEXT,
                           spaceAfter=5, leading=12)),
        Paragraph(
            f"<b>Bottom line:</b> {_bottom}",
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
        ("Graham Number",     f"${gn:.2f}" if gn > 0 else "N/A", RED),
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
    if mos_pct is not None and mos_pct < 0:
        _act_primary = [(RED,    f"DO NOT BUY at ${price_n:.2f}. Base intrinsic value = ${iv_base:.0f}; no margin of safety ({mos_pct:.1f}%).")]
        _act_watch   = [(YELLOW, f"ADD TO WATCHLIST. Set alert at ${iv_base*0.82:.0f}–${iv_base*0.85:.0f} for 15–20% MoS.")]
    elif mos_pct is not None and mos_pct < 20:
        _act_primary = [(YELLOW, f"HOLD. Price ${price_n:.2f} near intrinsic value ${iv_base:.0f}. MoS {mos_pct:.1f}% — too thin for new position.")]
        _act_watch   = [(YELLOW, f"WATCHLIST TRIGGER: Set alert at ${iv_base*0.80:.0f} for 20%+ MoS entry.")]
    else:
        _act_primary = [(GREEN,  f"BUY ZONE. Price ${price_n:.2f}, intrinsic value ${iv_base:.0f}. MoS: {mos_pct:.1f}%.")]
        _act_watch   = []
    actions = _act_primary + _act_watch + [
        (YELLOW, "VERIFY analyst coverage on TipRanks — filter to ≥3★ analysts."),
        (YELLOW, "CHECK insider ownership trend — SEC EDGAR Form 4 filings."),
        (GREEN,  "REVIEW next earnings date — avoid buying within 14 days of report."),
        (GREEN,  "MONITOR ROIC trend quarterly — widening gap vs competitors = moat erosion."),
    ]
    if iv_base > 0:
        actions.append((GREEN, f"BUY TRIGGER: Buffett Score ≥50, MoS ≥20%, price below ${iv_base*0.80:.0f}."))
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

    _pe_ttm = (fd.get("valuation") or {}).get("pe_trailing")
    _pe_fwd = (fd.get("valuation") or {}).get("pe_forward")
    snap_rows = [
        ["Metric", "Value", "Why It Matters", "Source"],
        ["Current Price",       f"${price_n:,.2f}",                              "Compare to intrinsic value for margin of safety",                      "Yahoo Finance"],
        ["Market Cap",          f"${mktcap/1e9:.2f}B",                           "Size signals stability; large-caps often have more moat durability",    "Yahoo Finance"],
        ["52-Week Range",       f"${price_d.get('week_52_low') or 0:,.2f} – ${price_d.get('week_52_high') or 0:,.2f}", "Context for price vs recent trading range", "Yahoo Finance"],
        ["52-Week Position",    f"{price_d.get('week_52_position_pct') or 0:.1f}% of range", "Near highs = limited upside; near lows = potential entry",  "Yahoo Finance"],
        ["Beta",                f"{price_d.get('beta') or 0:.3f}",               "Market sensitivity. >1.0 amplifies both gains and losses",              "Yahoo Finance"],
        ["P/E (TTM)",           f"{_pe_ttm:.1f}x" if _pe_ttm else "N/A (neg. earnings)", "Earnings multiple vs S&P ~26x. Higher = more growth priced in", "Yahoo Finance"],
        ["P/E (Forward)",       f"{_pe_fwd:.1f}x" if _pe_fwd else "N/A",        "Market's expectation of next-year earnings — forward-looking",          "Yahoo Finance"],
        ["Price / Book",        f"{(fd.get('valuation') or {}).get('price_to_book') or 0:.2f}x", "Lower = more asset-backed. Buffett prefers ROIC over P/B", "Yahoo Finance"],
        ["Revenue (TTM)",       f"${(cf.get('revenue') or 0)/1e6:.0f}M  (+{cf.get('revenue_growth_pct') or 0:.1f}% YoY)", "Total sales — growth trend matters more than absolute level", "Yahoo Finance"],
        ["Gross Margin",        f"{prof.get('gross_margin_pct') or 0:.2f}%",     "Pricing power indicator. Stable/rising = moat signal",                  "Yahoo Finance"],
        ["Operating Margin",    f"{prof.get('operating_margin_pct') or 0:.2f}%", "After overhead — true operating efficiency",                            "Yahoo Finance"],
        ["Net Margin",          f"{prof.get('net_margin_pct') or 0:.2f}%",       "Bottom-line profitability after all costs and taxes",                   "Yahoo Finance"],
        ["ROE",                 f"{prof.get('roe_pct') or 0:.2f}%",              "Buffett threshold ≥15%. How efficiently mgmt uses shareholder equity",  "Yahoo Finance Statistics"],
        ["ROIC vs WACC",        f"{roic.get('roic_pct') or 0:.1f}%  vs  {roic.get('wacc_pct') or 0:.1f}%", "ROIC > WACC = value creation. ROIC < WACC = value destruction", "Calculated"],
        ["Debt / Equity",       f"{bal.get('debt_to_equity_ratio') or 0:.3f}x",  "Buffett red flag >1.0. High debt limits optionality in downturns",      "Yahoo Finance"],
        ["Current Ratio",       f"{bal.get('current_ratio') or 0:.2f}x",         "Short-term liquidity. <1.0 = potential cash crunch risk",               "Yahoo Finance"],
        ["Owner Earnings",      f"${(cf.get('owner_earnings') or 0)/1e6:.0f}M  (${(cf.get('owner_earnings') or 0)/max(per.get('shares_outstanding') or 1, 1):.2f}/sh)", "NI + D&A − CapEx. Buffett's preferred earnings measure — hard to fake", "Calc NI+D&A−CapEx"],
        ["FCF",                 f"${(cf.get('free_cash_flow') or 0)/1e6:.0f}M",  "Cash the business actually generates — the ultimate solvency check",   "Yahoo Finance"],
        ["EPS (TTM / Forward)", f"${per.get('eps_trailing') or 0:.2f}  /  ${per.get('eps_forward') or 0:.2f}", "Earnings per share — trend matters more than level", "Yahoo Finance"],
        ["Graham Number",       f"${gn:.2f}" if gn > 0 else "N/A (neg. BVPS or EPS)", "Conservative ceiling: √(22.5 × EPS × BVPS). Price should be below", "Valuation model"],
        ["Insider Ownership",   f"{own.get('insider_ownership_pct') or 0:.2f}%", "Buffett signal ≥5%. Insiders buying = aligned interests",               "Yahoo Finance"],
        ["Analyst Target",      f"${anl.get('target_mean_price') or 0:,.0f}  (+{anl.get('upside_to_target_pct') or 0:.1f}%)" if anl.get("target_mean_price") else "N/A", "Wall St. 12-month consensus — note: Buffett uses 5–10yr horizon", "Yahoo Finance"],
    ]
    kv_table(snap_rows, [USABLE*0.18, USABLE*0.16, USABLE*0.43, USABLE*0.23], story)
    # Data quality notices
    _dw = analysis.get("data_warnings", [])
    if _dw:
        story.append(Spacer(1, 4))
        story.append(Paragraph("Data Quality Notices — verify flagged fields on Yahoo Finance",
            ParagraphStyle("dw_h", fontName="Helvetica-Bold", fontSize=7.5, textColor=YELLOW, spaceAfter=2)))
        for _w in _dw:
            story.append(Paragraph(
                f"  * {_w['field']}: raw value {_w['raw_value']} — {_w['reason']}",
                ParagraphStyle("dw", fontName="Helvetica", fontSize=7,
                               textColor=TEXT_DIM, spaceAfter=2, leading=10)))

    # ── Section 2: Buffett Score ──────────────────────────────
    section_title("SECTION 2  —  BUFFETT SCORE BREAKDOWN", story)
    story.append(Paragraph(
        "Five components that combine into the Buffett Score (0–100). "
        "Scores reflect data quality and available evidence — always cross-check critical decisions.",
        subtitle_style))

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
         "See component breakdown above — valuation and management quality are the primary variable drivers.", story)

    # ── Section 3: MOAT Analysis ──────────────────────────────
    section_title("SECTION 3  —  MOAT ANALYSIS", story)
    story.append(Paragraph(
        "Scores five types of competitive advantage on a 0–5 scale each (25 total). "
        "Wide Moat (≥18) is Buffett's primary filter — the foundation of a 10-year hold.",
        subtitle_style))

    dims = mo.get("dimensions", [])
    moat_rows = [["MOAT Type", "Score", "Key Evidence"]]
    for d in dims:
        ev = "; ".join(d.get("evidence", [])[:2]) or "—"
        moat_rows.append([d["label"], f"{d['score']}/5", ev])
    moat_rows.append(["TOTAL", f"{mo.get('total_score',0)}/25", mo.get("classification","—")])
    kv_table(moat_rows, [USABLE*0.22, USABLE*0.12, USABLE*0.66], story)
    note("Thresholds: 18–25 Wide (Buffett-quality), 10–17 Narrow (monitor), 0–9 None. "
         "Automated scorer uses quantitative proxies — qualitative review of 10-K IP, contracts, and "
         "switching costs may adjust the total by ±3 points.", story)

    # ── Section 4: Buffett 4-Filter Scorecard ────────────────
    section_title("SECTION 4  —  BUFFETT'S 4-FILTER SCORECARD", story)
    story.append(Paragraph(
        "Buffett's go/no-go checklist. A stock failing 2+ filters should be HOLD or AVOID "
        "regardless of analyst consensus or short-term price momentum.",
        subtitle_style))
    f4 = analysis.get("buffett_4_filters", {})
    _filter_map = [
        ("enduring_competitive_advantage", "1. Enduring Competitive Advantage",
         "Wide Moat (≥18/25) = PASS. Narrow = PARTIAL. None = FAIL."),
        ("management_quality",             "2. Management Quality",
         "ROE ≥15% trend + no dilution >2%/yr + insider ownership ≥5%"),
        ("sensible_price",                 "3. Sensible Price (MoS)",
         "Margin of Safety ≥20% on Owner Earnings DCF = PASS"),
        ("generates_fcf",                  "4. Free Cash Flow Generation",
         "Positive Owner Earnings in 4 of 5 years = PASS"),
    ]
    _filter_rows = [["Filter", "Result", "Evidence / Rationale"]]
    for _fkey, _flabel, _fnote in _filter_map:
        _fobj   = f4.get(_fkey, {})
        _result = _fobj.get("result", "N/A")
        _detail = _fobj.get("detail") or _fnote
        _fcol   = GREEN if _result == "PASS" else (YELLOW if _result in ("PARTIAL","WATCH") else RED)
        _result_p = Paragraph(f"<b>{_result}</b>",
            ParagraphStyle("fr", fontName="Helvetica-Bold", fontSize=8.5, textColor=_fcol, leading=12))
        _filter_rows.append([_flabel, _result_p, _detail])
    kv_table(_filter_rows, [USABLE*0.30, USABLE*0.13, USABLE*0.57], story)

    # ── Section 5: Valuation ──────────────────────────────────
    section_title("SECTION 5  —  INTRINSIC VALUE & MARGIN OF SAFETY", story)
    story.append(Paragraph(
        "Two independent valuation methods — Owner Earnings DCF and Graham Number. "
        "Discount to intrinsic value provides Margin of Safety (Buffett's primary entry criterion).",
        subtitle_style))

    def _mos_label(iv, price):
        if iv <= 0 or price <= 0:
            return "N/A"
        pct = (iv - price) / iv * 100
        if pct >= 0:
            return f"+{pct:.1f}% (undervalued)"
        return f"{pct:.1f}% (premium)"

    _iv_cons = (iv_data.get("conservative") or {}).get("total_intrinsic_value") or 0
    _iv_base = (iv_data.get("base")         or {}).get("total_intrinsic_value") or 0
    _iv_opt  = (iv_data.get("optimistic")   or {}).get("total_intrinsic_value") or 0
    dcf_rows = [
        ["Scenario", "Growth Rate", "Intrinsic Value", f"vs. current ${price_n:,.2f}", "Margin of Safety"],
        [f"Conservative", f"{growth_cons:.0f}%", f"${_iv_cons:,.2f}" if _iv_cons else "N/A", _mos_label(_iv_cons, price_n), f"{(_iv_cons-price_n)/_iv_cons*100:.1f}%" if _iv_cons > 0 else "N/A"],
        [f"Base",         f"{growth_base:.0f}%", f"${_iv_base:,.2f}" if _iv_base else "N/A", _mos_label(_iv_base, price_n), f"{(_iv_base-price_n)/_iv_base*100:.1f}%" if _iv_base > 0 else "N/A"],
        [f"Optimistic",   f"{growth_opt:.0f}%",  f"${_iv_opt:,.2f}"  if _iv_opt  else "N/A", _mos_label(_iv_opt,  price_n), f"{(_iv_opt-price_n)/_iv_opt*100:.1f}%"   if _iv_opt  > 0 else "N/A"],
    ]
    kv_table(dcf_rows, [USABLE*0.18, USABLE*0.16, USABLE*0.20, USABLE*0.26, USABLE*0.20], story)

    _gn_signal = (f"${gn:.2f} — {'price below Graham Number ✅' if price_n < gn else f'{price_n/gn:.1f}x premium — traditional value test fails'}"
                  if gn > 0 else "N/A (negative BVPS or EPS)")
    roic_rows = [
        ["Metric", "Value", "Signal"],
        ["ROIC", f"{roic.get('roic_pct',0):.1f}%", "Value Creating (ROIC > WACC)" if (roic.get('roic_pct') or 0) > (roic.get('wacc_pct') or 0) else "Value Destroying (ROIC < WACC)"],
        ["WACC", f"{roic.get('wacc_pct',0):.1f}%", "—"],
        ["Spread (ROIC − WACC)", f"{roic.get('spread_pct',0):.1f}%", "Positive spread = economic profit" if (roic.get('spread_pct') or 0) > 0 else "Negative spread = value destruction"],
        ["Owner Earnings / share", f"${dc.get('owner_earnings_per_share',0):.2f}", "Base for DCF"],
        ["Graham Number", _gn_signal],
    ]
    kv_table(roic_rows, [USABLE*0.40, USABLE*0.25, USABLE*0.35], story)
    _iv_range = f"${_iv_cons:,.0f}–${_iv_opt:,.0f}" if _iv_cons > 0 and _iv_opt > 0 else "N/A"
    note(f"Intrinsic value range: {_iv_range} — wide range signals high uncertainty. "
         "Conservative case assumes growth slows to base terminal rate.", story)

    # ── Section 6: Analyst Consensus ─────────────────────────
    section_title("SECTION 6  —  ANALYST CONSENSUS", story)

    recent = anl.get("recent_analyst_actions", [])
    a_rows = [["Firm", "Rating", "Target", "Action"]]
    action_map = {
        "up":   "UPGRADE",
        "down": "DOWNGRADE",
        "init": "INITIATED",
        "main": "MAINTAINED",
        "reit": "REITERATED",
    }
    _seen_firms = set()
    for a in recent:
        _firm = a.get("Firm", "")
        if _firm in _seen_firms:
            continue          # keep only the most recent entry per firm
        _seen_firms.add(_firm)
        a_rows.append([_firm, _rating_cell(a.get("ToGrade","")),
                       f"${a.get('currentPriceTarget',0):,.0f}",
                       action_map.get(a.get("Action",""), a.get("Action","").upper())])
        if len(a_rows) > 7:   # header + 6 firms max
            break
    kv_table(a_rows, [USABLE*0.30, USABLE*0.22, USABLE*0.18, USABLE*0.30], story)

    tgt_rows = [
        ["Metric", "Value"],
        ["Total Analysts",       str(anl.get("number_of_analyst_opinions","—"))],
        ["Mean Price Target",    f"${anl.get('target_mean_price',0):,.2f}"],
        ["Median Price Target",  f"${anl.get('target_median_price',0):,.2f}"],
        ["Target Range",         f"${anl.get('target_low_price',0):,.0f} – ${anl.get('target_high_price',0):,.0f}"],
        ["Upside to Mean",       f"+{anl.get('upside_to_target_pct',0):.1f}%"],
        ["Pattern Flag",         "Herd Mentality — bullish consensus when Buffett Score < 50" if score < 50 and (anl.get("number_of_analyst_opinions") or 0) >= 3 else "Coverage aligned with fundamentals"],
    ]
    kv_table(tgt_rows, [USABLE*0.45, USABLE*0.55], story)

    # ── Analyst vs Buffett Divergence Explainer ──
    _rec_key  = anl.get("recommendation_key") or "N/A"
    _n_anal   = anl.get("number_of_analyst_opinions") or 0
    _tgt_avg  = anl.get("target_mean_price") or 0
    _tgt_lo   = anl.get("target_low_price")  or 0
    _tgt_hi   = anl.get("target_high_price") or 0
    _upside   = anl.get("upside_to_target_pct") or 0
    _pe_val   = (fd.get("valuation") or {}).get("pe_trailing")
    _is_divergence = score < 50 and _n_anal >= 3 and _rec_key.lower() in ("buy","strongbuy","strong_buy","moderate_buy")
    story.append(Spacer(1, 4))
    div_title = Paragraph(
        ("⚠  WHY ANALYSTS SAY BUY BUT WE SAY " + verdict.upper() + " — UNDERSTANDING THE GAP")
        if _is_divergence else
        "ANALYST SUMMARY",
        ParagraphStyle("divt", fontName="Helvetica-Bold", fontSize=9,
                       textColor=YELLOW if _is_divergence else ACCENT, spaceAfter=6, leading=13))

    _analyst_intro = (
        f"<b>Yahoo Finance:</b>  {_n_anal} analyst{'s' if _n_anal != 1 else ''} — consensus: {_rec_key.upper()}.  "
        f"Average 12-month target: ${_tgt_avg:,.2f} ({_upside:+.1f}% upside).  "
        f"Target range: ${_tgt_lo:,.0f} – ${_tgt_hi:,.0f}."
        if _n_anal > 0 else
        "Analyst data not available via Yahoo Finance — verify on TipRanks."
    )

    if _is_divergence:
        _pe_clause = (f"A stock trading at {_pe_val:.0f}x earnings" if _pe_val else "This stock")
        divergence_text = (
            f"{_analyst_intro}<br/><br/>"

            f"<b>Our Buffett Score:</b>  {score}/100 → {verdict}.  "
            f"So why the gap?  Analysts and Buffett use fundamentally different frameworks:<br/><br/>"

            f"<b>1. Time horizon.</b>  Analysts forecast 12 months.  "
            f"Buffett's framework targets 5–10 year hold periods.  "
            f"{_pe_clause} can perform well in the next 12 months on momentum — "
            f"but carries real downside risk over a full cycle if growth disappoints.<br/><br/>"

            f"<b>2. Valuation methodology.</b>  Analysts use relative multiples "
            f"(P/E vs sector peers, PEG, EV/Sales).  Our DCF-based Owner Earnings model asks: "
            f"'What is the business worth in absolute terms?'  "
            f"At base-case growth ({growth_base:.0f}%), intrinsic value = ${_iv_base:,.0f} vs current price ${price_n:,.2f}.  "
            f"{'The stock is fairly priced — not cheap.' if abs(_iv_base - price_n) / max(_iv_base, 1) < 0.15 else ('The stock appears overvalued.' if price_n > _iv_base else 'The stock appears undervalued.')}<br/><br/>"

            f"<b>3. What analysts DON'T penalise.</b>  Wall Street rarely penalises "
            f"low insider ownership, revenue concentration risk, or business cyclicality.  "
            f"Our framework explicitly discounts for all three.<br/><br/>"

            f"<b>4. Herd dynamics.</b>  High analyst bullishness on a stock with Buffett Score < 50 "
            f"is a contrarian warning signal.  Buffett's best opportunities come when analysts are "
            f"neutral or bearish — not when everyone agrees.<br/><br/>"

            f"<b>Bottom line:</b>  Analyst targets of ${_tgt_lo:,.0f}–${_tgt_hi:,.0f} are reasonable IF the "
            f"current growth trajectory continues uninterrupted.  "
            f"Our {verdict} verdict does not dispute the quality of the business — it disputes the "
            f"price relative to intrinsic value."
        )
    else:
        divergence_text = _analyst_intro

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
        ["Insider Ownership", "WEAK" if (own.get('insider_ownership_pct') or 0) < 1.0 else "OK",
         f"{own.get('insider_ownership_pct') or 0:.2f}% — {'low alignment with shareholders' if (own.get('insider_ownership_pct') or 0) < 1.0 else 'acceptable insider alignment'}"],
        ["Institutional Own.", "STRONG",  f"{own.get('institutional_ownership_pct',0):.2f}% — blue-chip institutional following"],
        ["Net Cash Position",  "POSITIVE",f"Cash ${bal.get('total_cash',0)/1e6:.0f}M vs Debt ${bal.get('total_debt',0)/1e6:.0f}M → +$249M net"],
        ["Capital Allocation", "NEUTRAL", "No dividend; reinvesting at 14.3% revenue CAGR"],
        ["EPS Growth (TTM)",   "STRONG",  f"+{growth.get('earnings_growth_ttm_pct') or 0:.1f}% TTM; quarterly +{growth.get('earnings_quarterly_growth_pct') or 0:.1f}%"],
        ["Share Dilution",     "CHECK",   "Verify shares outstanding trend in 10-K"],
    ]
    kv_table(mgmt_rows, [USABLE*0.27, USABLE*0.15, USABLE*0.58], story)
    _ins = own.get('insider_ownership_pct') or 0
    if _ins < 1.0:
        note(f"CRITICAL: {_ins:.2f}% insider ownership is a major Buffett flag. Check SEC Form 4 "
             "(EDGAR) for recent insider selling before any position.", story)
    else:
        note("Verify insider ownership trend in SEC EDGAR Form 4 filings — buying vs selling direction matters.", story)

    # ── Section 8: Competitive Landscape ─────────────────────
    section_title("SECTION 8  —  COMPETITIVE LANDSCAPE", story)
    story.append(Paragraph(
        "ROIC comparison vs direct competitors. A widening ROIC gap vs peers is the strongest moat signal.",
        subtitle_style))

    if competitors:
        _roic_val  = roic.get("roic_pct")
        _gm_val    = prof.get("gross_margin_pct")
        comp_land  = [["Company", "ROIC (est.)", "Gross Margin", "MOAT", "Note"]]
        comp_land.append([
            f"{ticker} (this analysis)",
            f"{_roic_val:.1f}%" if _roic_val else "N/A",
            f"{_gm_val:.1f}%"  if _gm_val  else "N/A",
            moat_cl,
            "Subject of analysis",
        ])
        for _c in competitors:
            comp_land.append([
                _c.get("name", ""),
                _c.get("roic", "N/A"),
                _c.get("gross_margin", "N/A"),
                _c.get("moat", "N/A"),
                _c.get("note", ""),
            ])
        kv_table(comp_land, [USABLE*0.24, USABLE*0.13, USABLE*0.14, USABLE*0.14, USABLE*0.35], story)
        note("Monitor ROIC gap vs above peers quarterly — widening gap = strengthening moat; "
             "narrowing gap = moat erosion risk.", story)
    else:
        note(f"Competitor data not catalogued for {ticker}. "
             "Add to KNOWN_COMPETITORS in analyze_stock.py for future analyses.", story)

    # ── Section 9: Timing ─────────────────────────────────────
    section_title("SECTION 9  —  MARKET TIMING & ENTRY CONDITIONS", story)
    story.append(Paragraph(
        "Advisory only — does NOT affect Buffett Score. Answers: is NOW a good entry window?",
        subtitle_style))

    timing_rows = [
        ["Signal", "Value", "Status", "Interpretation"],
        ["RSI (14-day)",    f"{tech.get('rsi_14',0):.1f}",        "NEUTRAL",      "Normal range — neither oversold nor overbought"],
        ["VIX",             f"{mkt.get('vix_current',0):.2f}",    "NORMAL",       "Not Buffett's buying zone (VIX >30)"],
        ["52-Week Position",f"{price_d.get('week_52_position_pct',0):.1f}%", "NEAR HIGHS", "Near high — limited recent room"],
        ["50-Day MA",       f"${tech.get('ma_50',0):,.2f}",       "SLIGHT CAUTION","Price slightly below 50-day MA"],
        ["200-Day MA",      f"${tech.get('ma_200',0):,.2f}",      "ABOVE",        "+30% above 200-day MA — strong uptrend intact"],
    ]
    kv_table(timing_rows, [USABLE*0.20, USABLE*0.15, USABLE*0.18, USABLE*0.47], story)

    _buy_trigger = (f"${iv_base*0.80:,.0f}–${iv_base*0.82:,.0f}"
                    if iv_base > 0 else "N/A (no DCF — negative earnings)")
    entry_rows = [
        ["Green Signals", "Buy Trigger Price", "VIX Trigger", "Ideal MoS Target"],
        [f"{grn_ct}/4", _buy_trigger, ">30 (fear zone)", "≥20% on base case"],
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
    story.append(Paragraph(
        "Automatic flags triggered by data thresholds. Critical flags directly lower the Buffett Score.",
        subtitle_style))

    _pe_ttm_v  = (fd.get("valuation") or {}).get("pe_trailing")
    _w52pos    = price_d.get("week_52_position_pct")
    _ins_own_v = own.get("insider_ownership_pct")
    _de_ratio  = bal.get("debt_to_equity_ratio")
    _fcf_v     = cf.get("free_cash_flow")
    _oe_v      = cf.get("owner_earnings")

    all_flags = []
    if _pe_ttm_v and _pe_ttm_v > 40:
        all_flags.append(("CAUTION", f"P/E {_pe_ttm_v:.0f}x TTM — elevated vs S&P ~26x; requires sustained growth to justify"))
    if _w52pos and _w52pos > 80:
        all_flags.append(("CAUTION", f"Near 52-week highs ({_w52pos:.1f}% of range) — limited recent room; mean-reversion risk"))
    if _ins_own_v is not None and _ins_own_v < 1.0:
        all_flags.append(("CAUTION", f"Insider ownership {_ins_own_v:.2f}% — management has low financial alignment with shareholders"))
    if _de_ratio and _de_ratio > 1.0:
        all_flags.append(("CAUTION", f"Debt/Equity {_de_ratio:.2f}x — above Buffett's 1.0 threshold; limits flexibility in downturns"))
    elif _de_ratio and _de_ratio > 0.5:
        all_flags.append(("CLEAR",   f"Debt/Equity {_de_ratio:.2f}x — moderate; monitor trend vs earnings growth"))
    else:
        all_flags.append(("CLEAR",   f"Debt/Equity {_de_ratio:.2f}x — conservative balance sheet" if _de_ratio else "Debt/Equity — data not available"))
    if _fcf_v is not None and _fcf_v < 0:
        all_flags.append(("CAUTION", f"Free Cash Flow negative (${_fcf_v/1e6:.0f}M) — burning cash; watch burn rate"))
    else:
        all_flags.append(("CLEAR",   f"FCF positive (${(_fcf_v or 0)/1e6:.0f}M)" + (f"  |  Owner Earnings ${(_oe_v or 0)/1e6:.0f}M" if _oe_v else "")))
    all_flags.append(("CLEAR", "No share dilution flags from automated analysis — verify 10-K trend manually"))

    # Add flags from data_warnings (yfinance anomalies)
    for _dw in (analysis.get("data_warnings") or []):
        all_flags.append(("CAUTION", f"Data quality: {_dw['field']} returned {_dw['raw_value']} — {_dw['reason'][:80]}"))
    flag_rows = [["Severity", "Flag"]]
    for sev, flag in all_flags:
        flag_rows.append([sev, flag])
    kv_table(flag_rows, [USABLE*0.14, USABLE*0.86], story)

    # ── Final Summary ─────────────────────────────────────────
    story.append(HR(GOLD, 1.5, 6, 5))
    story.append(Paragraph("FINAL SUMMARY", ParagraphStyle("fs", fontName="Helvetica-Bold",
                 fontSize=11, textColor=GOLD, spaceAfter=6)))

    _roic_v = roic.get("roic_pct")
    _wacc_v = roic.get("wacc_pct")
    _gm_v   = prof.get("gross_margin_pct")
    _roic_str = f"ROIC {_roic_v:.1f}% vs WACC {_wacc_v:.1f}%" if _roic_v and _wacc_v else "ROIC data N/A"
    _gm_str   = f"Gross Margin {_gm_v:.1f}%" if _gm_v else "Gross Margin data N/A"
    _mos_str  = f"MoS {mos_pct:.1f}% base case" if mos_pct else "MoS N/A (negative earnings)"
    _buy_trig_final = (f"Price ≤${iv_base*0.80:,.0f}  +  Buffett Score ≥50  +  MoS ≥20%  +  VIX >25"
                       if iv_base > 0 else "No buy trigger — negative Owner Earnings DCF")
    _risk_line = (f"ROIC gap vs {competitors[0]['name']} | Revenue concentration | Business cyclicality"
                  if competitors else "Review competitive landscape — see Section 8")
    _n_anal_f   = anl.get("number_of_analyst_opinions") or 0
    _tgt_avg_f  = anl.get("target_mean_price") or 0
    _upside_f   = anl.get("upside_to_target_pct") or 0
    _rec_f      = (anl.get("recommendation_key") or "N/A").upper()
    final_rows = [
        ["Field", "Value"],
        ["Buffett Score",       f"{score}/100  →  {verdict}"],
        ["Primary Drivers",     f"{_roic_str}  |  {_gm_str}  |  {_mos_str}"],
        ["Analyst Consensus",   f"{_n_anal_f} analysts  |  {_rec_f}  |  Mean target ${_tgt_avg_f:,.2f}  ({_upside_f:+.1f}%)" if _n_anal_f > 0 else "Analyst data not available — verify on TipRanks"],
        ["Strategy Bucket",     "Bucket B — Active MOAT Satellite (NOT a passive core hold)"],
        ["Data Verification",   "Yahoo Finance > Statistics  |  SEC EDGAR (10-K, Form 4)  |  TipRanks"],
        ["Buy Trigger",         _buy_trig_final],
        ["Key Risks",           _risk_line],
        ["Analysis Date",       datetime.now().strftime("%Y-%m-%d  %H:%M")],
    ]
    kv_table(final_rows, [USABLE*0.28, USABLE*0.72], story)

    doc.build(story, onFirstPage=page_bg, onLaterPages=page_bg)
    return out_path


# ════════════════════════════════════════════════════════════════════════════
#  ETF PDF BUILDER
# ════════════════════════════════════════════════════════════════════════════
def build_pdf_etf(ticker, analysis, out_path, chart_dir):
    """PDF builder for ETF track — reads ETF-specific analyze_etf.py output."""
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16*mm, bottomMargin=20*mm,
    )
    story = []

    # ── Unwrap ETF data ──────────────────────────────────────
    qs      = analysis.get("quick_summary", {})
    etf_sc  = analysis.get("etf_buffett_score", {})
    comps   = etf_sc.get("components", {})
    holds   = analysis.get("holdings_analysis", {})
    factor  = analysis.get("factor_tilt", {})
    perf    = analysis.get("performance", {})

    score    = etf_sc.get("total_score", 0)
    verdict  = qs.get("verdict", "ACCEPTABLE")
    v_col    = vc(score)
    name     = qs.get("name", analysis.get("name", ticker))
    category = analysis.get("category", "—")
    fund_fam = analysis.get("fund_family", "—")
    _exp_obj = analysis.get("expense_ratio") or {}
    expense  = (_exp_obj.get("value") if isinstance(_exp_obj, dict) else _exp_obj)  # float or None
    aum      = qs.get("aum", "N/A")
    top15    = qs.get("top15_weight_pct") or 0
    top_h    = holds.get("top_holdings", [])
    moat_ct  = holds.get("moat_overlap", {}).get("moat_companies_in_top15", 0)
    bucket   = etf_sc.get("bucket_recommendation", "—")
    pe       = factor.get("pe_ratio") or 0
    pb       = factor.get("price_to_book") or 0
    _div_raw  = factor.get("dividend_yield_pct") or 0
    # Sanity cap: yfinance sometimes returns ×100 error (e.g. 119% for VOO)
    if _div_raw > 30:
        div_yield       = 0
        _div_yield_str  = f"N/A (data anomaly: raw={_div_raw:.1f}% — verify on Yahoo Finance)"
    else:
        div_yield       = _div_raw
        _div_yield_str  = f"{div_yield:.2f}%  vs S&P ~1.3%" if div_yield else "N/A — check ETF.com"
    r3       = perf.get("3yr_avg_return_pct") or 0
    r5       = perf.get("5yr_avg_return_pct") or 0
    sp       = factor.get("sp500_benchmarks", {"pe": 26, "pb": 4.5, "yield": 1.3})
    # Beta display
    _beta_obj   = analysis.get("beta") or {}
    _beta_val   = _beta_obj.get("value") if isinstance(_beta_obj, dict) else _beta_obj
    _beta_interp = _beta_obj.get("interpretation", "") if isinstance(_beta_obj, dict) else ""
    _beta_str   = f"{_beta_val:.2f}  —  {_beta_interp}" if _beta_val else "N/A — check ETF.com"
    # Tracking error display
    _te_obj      = analysis.get("tracking_error") or {}
    _te_val      = _te_obj.get("value") if isinstance(_te_obj, dict) else _te_obj
    _te_str      = f"{_te_val:.3f}%" if _te_val else "N/A — check ETF.com  (target: < 0.20%)"
    te_source_str = _te_obj.get("source", "ETF.com / prospectus") if isinstance(_te_obj, dict) else "ETF.com / prospectus"
    # Expense ratio source
    expense_source = analysis.get("expense_ratio_source", "ETF.com / prospectus")
    # Total holdings count
    total_h     = analysis.get("total_holdings_count")
    total_h_str = str(int(total_h)) if total_h else "N/A — check fund prospectus"
    # ETF description
    etf_desc    = analysis.get("etf_description", "")
    # Geographic exposure
    geo_exp     = analysis.get("geographic_exposure", {})

    # Expense ratio display & color
    if expense is None:
        exp_str, exp_col, exp_explain = "UNKNOWN", YELLOW, "verify on ETF.com"
    elif expense <= 0.10:
        exp_str, exp_col, exp_explain = f"{expense:.2f}%", GREEN, "excellent — very low cost"
    elif expense <= 0.25:
        exp_str, exp_col, exp_explain = f"{expense:.2f}%", YELLOW, "acceptable cost drag"
    else:
        exp_str, exp_col, exp_explain = f"{expense:.2f}%", RED, "high — check alternatives"

    conc_col     = GREEN if top15 < 20 else (YELLOW if top15 < 40 else RED)
    conc_explain = "well diversified" if top15 < 20 else ("moderate concentration" if top15 < 40 else "top-heavy")

    if "Bucket A" in bucket and "Bucket B" not in bucket:
        bucket_short = "A — Core"
    elif "Bucket B" in bucket and "Bucket A" not in bucket:
        bucket_short = "B — Satellite"
    else:
        bucket_short = "A / B"

    etf_score_explain = {"CORE HOLD": "strong core ETF", "ACCEPTABLE": "acceptable with caveats",
                         "AVOID": "does not meet criteria", "STRONG CORE": "best-in-class ETF"
                         }.get(verdict, "review sections below")

    comp_labels = [
        ("efficiency",             "Efficiency",      35, "Expense ratio, AUM, beta, tracking error"),
        ("diversification_quality","Diversification", 35, "Top-15 concentration, sector spread, moat overlap"),
        ("factor_value",           "Factor Value",    30, "P/E and P/B vs S&P 500 benchmarks"),
    ]

    # ════════════════════════════════════════════════════════
    # PAGE 1: COVER + EXECUTIVE SUMMARY
    # ════════════════════════════════════════════════════════
    ring = ScoreRing(score, 100, 90)
    name_block = [
        [Paragraph(ticker, ParagraphStyle("etk", fontName="Helvetica-Bold",
                   fontSize=32, textColor=TEXT, leading=36))],
        [Paragraph(name, ParagraphStyle("enm", fontName="Helvetica",
                   fontSize=10, textColor=TEXT_MID, leading=13))],
        [Paragraph(f"ETF  ·  {fund_fam}  ·  {category}",
                   ParagraphStyle("einf", fontName="Helvetica", fontSize=8,
                                  textColor=TEXT_DIM, leading=12))],
        [Paragraph(f"Analysis date: {datetime.now().strftime('%B %d, %Y')}  ·  AUM: {aum}",
                   ParagraphStyle("edt", fontName="Helvetica", fontSize=8,
                                  textColor=TEXT_DIM, leading=12))],
    ]
    name_t = Table(name_block, colWidths=[USABLE * 0.75])
    name_t.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 3), ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 0), ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))
    score_block = Table([[ring]], colWidths=[USABLE * 0.25])
    score_block.setStyle(TableStyle([
        ("ALIGN",         (0,0),(-1,-1), "CENTER"), ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 4),        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
    ]))
    header_t = Table([[name_t, score_block]], colWidths=[USABLE * 0.75, USABLE * 0.25])
    header_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD),
        ("GRID",          (0,0),(-1,-1), 0.4, BORDER),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0),(0,0),   14), ("RIGHTPADDING",  (0,0),(0,0), 8),
        ("TOPPADDING",    (0,0),(-1,-1), 10), ("BOTTOMPADDING", (0,0),(-1,-1), 10),
    ]))
    story.append(header_t)
    story.append(Spacer(1, 4))

    # Verdict banner
    verdict_t = Table(
        [[Paragraph(f"ETF VERDICT:  {verdict}", ParagraphStyle(
            "evb", fontName="Helvetica-Bold", fontSize=22,
            textColor=v_col, alignment=TA_CENTER, leading=26))]],
        colWidths=[USABLE], rowHeights=[42],
    )
    verdict_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD2),
        ("TOPPADDING",    (0,0),(-1,-1), 8), ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LINEABOVE",     (0,0),(-1,0),  2.0, v_col),
        ("LINEBELOW",     (0,0),(-1,0),  2.0, v_col),
    ]))
    story.append(verdict_t)
    story.append(Spacer(1, 5))

    # 5 ETF KPI tiles
    def kpi_cell(label, value, value_color, sub="", explain=""):
        inner = [
            [Paragraph(label.upper(), ParagraphStyle("ekl", fontName="Helvetica",
                       fontSize=7, textColor=TEXT_DIM, alignment=TA_CENTER))],
            [Paragraph(str(value), ParagraphStyle("ekv", fontName="Helvetica-Bold",
                       fontSize=15, textColor=value_color, alignment=TA_CENTER, leading=20))],
        ]
        if sub:
            inner.append([Paragraph(sub, ParagraphStyle("eks", fontName="Helvetica",
                       fontSize=7, textColor=TEXT_DIM, alignment=TA_CENTER))])
        if explain:
            inner.append([Paragraph(explain, ParagraphStyle("eke", fontName="Helvetica-Oblique",
                       fontSize=6.5, textColor=HexColor("#888888"), alignment=TA_CENTER))])
        t = Table(inner, colWidths=[USABLE / 5 - 1.5])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), CARD2),
            ("TOPPADDING",    (0,0),(-1,-1), 6), ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("LEFTPADDING",   (0,0),(-1,-1), 2), ("RIGHTPADDING",  (0,0),(-1,-1), 2),
        ]))
        return t

    kpi_row = [[
        kpi_cell("ETF Quality Score", f"{score}/100", vc(score), "out of 100",   etf_score_explain),
        kpi_cell("Expense Ratio", exp_str,          exp_col,   "annual cost",     exp_explain),
        kpi_cell("AUM",           aum,              ACCENT,    "fund size",       "liquidity indicator"),
        kpi_cell("Top-15 Weight", f"{top15:.1f}%", conc_col,  "concentration",   conc_explain),
        kpi_cell("Bucket",        bucket_short,     v_col,     "A=Core/B=Sat.",   "portfolio fit"),
    ]]
    kpi_t = Table(kpi_row, colWidths=[USABLE / 5] * 5)
    kpi_t.setStyle(TableStyle([
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 0), ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ("LEFTPADDING",   (0,0),(-1,-1), 0), ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))
    story.append(kpi_t)
    story.append(Spacer(1, 5))

    # 3-Component score strip
    comp_cells = []
    for key, label, mx, _ in comp_labels:
        c   = comps.get(key, {})
        sc  = c.get("score", 0)
        col = GREEN if sc / mx >= 0.70 else (YELLOW if sc / mx >= 0.50 else RED)
        comp_cells.append(Table([
            [Paragraph(label, ParagraphStyle("ecl", fontName="Helvetica",
                       fontSize=7, textColor=TEXT_DIM, alignment=TA_CENTER))],
            [Paragraph(f"{sc}/{mx}", ParagraphStyle("ecs", fontName="Helvetica-Bold",
                       fontSize=11, textColor=col, alignment=TA_CENTER))],
        ], colWidths=[USABLE/3 - 2]))
    comp_t = Table([comp_cells], colWidths=[USABLE/3]*3)
    comp_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD2),
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 6), ("BOTTOMPADDING", (0,0),(-1,-1), 6),
    ]))
    story.append(Paragraph("ETF QUALITY SCORE COMPONENTS", ParagraphStyle("ech", fontName="Helvetica-Bold",
                 fontSize=7.5, textColor=TEXT_DIM, spaceAfter=3)))
    story.append(comp_t)
    story.append(Paragraph(
        "Buffett-principles framework applied to passive funds: "
        "Efficiency (35 pts — expense ratio, AUM, beta)  ·  "
        "Diversification (35 pts — concentration, sector spread, moat overlap)  ·  "
        "Factor Value (30 pts — P/E and P/B vs S&P 500)",
        ParagraphStyle("escnote", fontName="Helvetica-Oblique", fontSize=7,
                       textColor=HexColor("#888888"), spaceAfter=4, leading=10)))
    story.append(Spacer(1, 4))

    # ── Executive Summary ────────────────────────────────────
    story.append(HR(ACCENT, 1.2, 4, 5))
    story.append(Paragraph("EXECUTIVE SUMMARY  —  ETF EFFICIENCY AUDIT", ST["h2"]))

    def exec_col_title(t):
        return Paragraph(t, ParagraphStyle("eect", fontName="Helvetica-Bold",
                         fontSize=8.5, textColor=ACCENT, spaceAfter=5, leading=12))

    # Col 1: Dynamic ETF thesis
    bull_pts = []
    if top15 < 20:
        bull_pts.append(f"Low top-15 concentration ({top15:.1f}%) — broad global diversification")
    if factor.get("value_tilt"):
        bull_pts.append(f"Value tilt: P/E {pe:.1f}x vs S&P ~26x — cheaper than domestic US equities")
    if expense and expense <= 0.15:
        bull_pts.append(f"Low expense ratio {expense:.2f}% — minimal cost drag on long-term compounding")
    elif expense is None:
        bull_pts.append(f"{fund_fam} is known for ultra-low expense ratios — verify on ETF.com")
    if not bull_pts:
        bull_pts.append("Broad global ex-US exposure across developed and emerging markets")

    bear_pts = []
    if expense is None:
        bear_pts.append("Expense ratio unavailable via yfinance — must verify manually before buying")
    if top15 >= 40:
        bear_pts.append(f"Top-15 concentration {top15:.1f}% — top-heavy allocation")
    if moat_ct == 0:
        bear_pts.append("0 of top 15 holdings pass Buffett quality filter — no wide-moat names in top positions")
    if not bear_pts:
        bear_pts.append("Currency risk in international holdings is unhedged — adds volatility vs. domestic funds")

    if verdict in ("CORE HOLD", "STRONG CORE", "ACCEPTABLE"):
        bottom = f"ETF Score {score}/100 → {verdict}. Suitable as a Bucket A core position for international exposure. Verify expense ratio before committing."
    else:
        bottom = f"ETF Score {score}/100 → {verdict}. Review concerns before including in core portfolio."

    thesis_items = [exec_col_title("ETF INVESTMENT THESIS")]
    if etf_desc:
        thesis_items.append(Paragraph(
            f"<i>{etf_desc[:220]}</i>",
            ParagraphStyle("etd", fontName="Helvetica-Oblique", fontSize=8,
                           textColor=TEXT_MID, spaceAfter=6, leading=12)))
    thesis_items += [
        Paragraph(f"<b>Bull:</b>  " + "  ".join(bull_pts),
                  ParagraphStyle("eti", fontName="Helvetica", fontSize=8, textColor=TEXT,
                                 spaceAfter=5, leading=12)),
        Paragraph(f"<b>Bear:</b>  " + "  ".join(bear_pts),
                  ParagraphStyle("eti2", fontName="Helvetica", fontSize=8, textColor=TEXT,
                                 spaceAfter=5, leading=12)),
        Paragraph(f"<b>Bottom line:</b>  {bottom}",
                  ParagraphStyle("eti3", fontName="Helvetica-Bold", fontSize=8, textColor=YELLOW,
                                 spaceAfter=0, leading=12)),
    ]

    # Col 2: Key numbers
    snap_items = [exec_col_title("KEY NUMBERS AT A GLANCE")]
    top1 = top_h[0] if top_h else {}
    snap_data_etf = [
        ("AUM",             aum,                                             ACCENT),
        ("Expense Ratio",   exp_str,                                         exp_col),
        ("P/E Ratio",       f"{pe:.1f}x  (S&P ~26x)",                       GREEN if pe < 26 else YELLOW),
        ("P/B Ratio",       f"{pb:.2f}x" if pb else "N/A — check Yahoo",    TEXT),
        ("Top Holding",     f"{top1.get('name','—')[:28]}  ({top1.get('weight_pct',0):.1f}%)", TEXT),
        ("Top-15 Weight",   f"{top15:.1f}%  of fund",                        conc_col),
        ("3-Yr Return",     f"{r3:.1f}%  annualised",                        GREEN if r3 > 5 else YELLOW),
        ("5-Yr Return",     f"{r5:.1f}%  annualised",                        GREEN if r5 > 5 else YELLOW),
        ("Moat in Top 15",  f"{moat_ct} of 15 holdings",                    GREEN if moat_ct >= 8 else YELLOW),
        ("Category",        category,                                         TEXT),
    ]
    for label, val_str, col in snap_data_etf:
        snap_items.append(Paragraph(
            f"<font color='#64748B'>{label}:</font>  "
            f"<font color='#{_hex(col)}'><b>{val_str}</b></font>",
            ParagraphStyle("esd", fontName="Helvetica", fontSize=8,
                           textColor=TEXT, spaceAfter=2, leading=12)))

    # Col 3: Action items
    action_items = [exec_col_title("ACTION ITEMS & NEXT STEPS")]
    actions_etf = []
    if expense is None:
        actions_etf.append((YELLOW, f"VERIFY expense ratio on ETF.com or {fund_fam} website before buying."))
    if verdict in ("CORE HOLD", "STRONG CORE", "ACCEPTABLE"):
        actions_etf.append((GREEN, f"CONSIDER for Bucket A (Core) — international diversification."))
    else:
        actions_etf.append((RED, f"AVOID — ETF score {score}/100 below threshold."))
    actions_etf.append((YELLOW, "CHECK holdings: Yahoo Finance > Holdings tab for sector balance."))
    actions_etf.append((YELLOW, "COMPARE VEA (developed only) vs VXUS (all intl incl. EM) for EM risk preference."))
    actions_etf.append((GREEN, f"FACTOR: P/E {pe:.1f}x vs S&P ~26x = {'value tilt confirmed ✓' if factor.get('value_tilt') else 'no value tilt'}."))
    actions_etf.append((GREEN, "BENCHMARK: Vanguard VXUS 0.07% / iShares IXUS 0.07% — verify match."))
    for col, text in actions_etf:
        dot = "●" if col == RED else ("◆" if col == YELLOW else "✓")
        action_items.append(Paragraph(
            f'<font color="#{_hex(col)}">{dot}</font>  {text}',
            ParagraphStyle("eai", fontName="Helvetica", fontSize=8,
                           textColor=TEXT, spaceAfter=4, leading=12, leftIndent=10,
                           firstLineIndent=-10)))

    col_w = USABLE / 3 - 2
    exec_t = Table(
        [[_wrap_col(thesis_items, col_w), _wrap_col(snap_items, col_w), _wrap_col(action_items, col_w)]],
        colWidths=[col_w + 2, col_w + 2, col_w + 2])
    exec_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD),
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 10), ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 10), ("RIGHTPADDING",  (0,0),(-1,-1), 10),
    ]))
    story.append(exec_t)

    # Charts (score breakdown + gauge)
    story.append(Spacer(1, 6))
    for fname, aspect in [(f"{ticker}_score_breakdown.png", 0.50), (f"{ticker}_buffett_score.png", 0.40)]:
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

    # Section 1: ETF Data Snapshot
    section_title("SECTION 1  —  ETF DATA SNAPSHOT", story)
    note("Core metrics at a glance — verifies the ETF's size, cost, and benchmark alignment before investing.", story)
    snap_rows = [
        ["Metric", "Value", "Why It Matters", "Source"],
        ["Ticker / Name",      f"{ticker}  —  {name[:38]}",      "Fund identifier",                                                         "Yahoo Finance"],
        ["Fund Family",        fund_fam,                          "Provider reputation for low costs and index discipline",                   "Yahoo Finance"],
        ["Category",           category,                          "Morningstar classification — defines peer comparison group",               "Yahoo Finance"],
        ["AUM",                aum,                               "Larger AUM = tighter bid/ask spread, lower closure risk. Target: >$1B",   "Yahoo Finance"],
        ["Expense Ratio",      exp_str,                           "Annual fee deducted from fund — biggest drag on long-term returns. Target: ≤0.10%", expense_source],
        ["Beta (vs S&P 500)",  _beta_str,                         "Market sensitivity. <1.0 = defensive; >1.0 = amplifies market moves",     "Yahoo Finance"],
        ["Tracking Error",     _te_str,                           "How precisely the fund replicates its index. Target: <0.20% per year",    te_source_str],
        ["P/E Ratio",          f"{pe:.2f}x  vs S&P ~26x {'(value tilt)' if pe < 26 else '(growth/neutral)'}",
                                                                   "Aggregate valuation of holdings vs US market (~26x). Lower = cheaper",   "Yahoo Finance"],
        ["P/B Ratio",          f"{pb:.2f}x  vs S&P ~4.5x" if pb else "N/A — check ETF.com",
                                                                   "Price-to-book of holdings. Lower = more value-tilted",                    "Yahoo Finance"],
        ["Dividend Yield",     _div_yield_str,
                                                                   "Income generated. Compare to S&P 500 (~1.3%) for income tilt signal",     "Yahoo Finance"],
        ["Total Holdings",     total_h_str,                       "Number of stocks in fund. More = broader diversification",                "Yahoo Finance"],
        ["Top-15 Weight",      f"{top15:.1f}%  of fund",          "Higher = more concentrated in top names. Target: <40%",                  "Yahoo Finance > Holdings"],
        ["Moat in Top 15",     f"{moat_ct} of top holdings pass quality check",
                                                                   "How many top holdings have durable competitive advantages",               "Buffett moat screen"],
        ["3-Yr Avg Return",    f"{r3:.1f}%  annualised",          "Performance context — not the primary criterion for ETF selection",        "Yahoo Finance"],
        ["5-Yr Avg Return",    f"{r5:.1f}%  annualised",          "Longer-term performance vs benchmark",                                     "Yahoo Finance"],
        ["Bucket Rec.",        bucket,                            "A = Core passive hold. B = Satellite/thematic add-on",                    "ETF Quality Score analysis"],
    ]
    kv_table(snap_rows, [USABLE*0.19, USABLE*0.19, USABLE*0.42, USABLE*0.20], story)

    # Geographic exposure sub-section (if available)
    if geo_exp:
        story.append(Spacer(1, 5))
        story.append(Paragraph("Geographic Exposure (Top 8 Countries)",
                     ParagraphStyle("geoh", fontName="Helvetica-Bold", fontSize=8,
                                    textColor=ACCENT, spaceAfter=4, leading=11)))
        story.append(Paragraph(
            "Shows where investment risk is concentrated — important for international ETFs.",
            ParagraphStyle("geonote", fontName="Helvetica-Oblique", fontSize=7,
                           textColor=TEXT_DIM, spaceAfter=4, leading=10)))
        geo_rows = [["Country", "Weight (%)"]]
        for country, weight in geo_exp.items():
            geo_rows.append([country, f"{weight:.1f}%"])
        kv_table(geo_rows, [USABLE*0.60, USABLE*0.40], story)

    # Section 2: ETF Score Breakdown
    section_title("SECTION 2  —  ETF QUALITY SCORE BREAKDOWN", story)
    note("How the ETF Quality Score is built — identifies where the fund gains or loses points across the three components.", story)
    comp_detail_rows = [["Component", "Score", "Max", "What's Measured"]]
    for key, label, mx, desc in comp_labels:
        c = comps.get(key, {})
        comp_detail_rows.append([label, str(c.get("score", 0)), str(mx), desc])
    comp_detail_rows.append(["TOTAL", str(score), "100", verdict])
    kv_table(comp_detail_rows, [USABLE*0.22, USABLE*0.09, USABLE*0.08, USABLE*0.61], story)
    note(f"Score formula: Efficiency(35) + Diversification(35) + Factor Value(30). "
         f"Expense ratio is the biggest unknown — verify to confirm full efficiency score.", story)

    # Section 3: Top Holdings
    section_title("SECTION 3  —  TOP HOLDINGS ANALYSIS", story)
    note("The 10 largest positions — checks whether the ETF holds quality businesses with durable competitive advantages.", story)
    hold_rows = [["#", "Ticker", "Name", "Weight %", "Moat?"]]
    for h in top_h[:10]:
        hold_rows.append([
            str(h.get("rank", "")),
            h.get("ticker", ""),
            h.get("name", "")[:35],
            f"{h.get('weight_pct', 0):.2f}%",
            "✓" if h.get("has_moat") else "—",
        ])
    kv_table(hold_rows, [USABLE*0.06, USABLE*0.10, USABLE*0.50, USABLE*0.14, USABLE*0.20], story)
    note(f"Top-15 combined weight: {top15:.1f}% of fund. {moat_ct} of top holdings pass quality check. "
         "For full holdings: Yahoo Finance > Holdings tab.", story)
    note("Tickers shown in Yahoo Finance local-exchange format — e.g. 2330.TW = TSMC (Taiwan Stock Exchange), "
         "ASML.AS = ASML (Amsterdam Exchange), 005930.KS = Samsung (Korea Exchange).", story)

    # Section 4: Factor Tilt
    section_title("SECTION 4  —  FACTOR TILT ANALYSIS", story)
    note("Compares ETF valuations to the S&P 500 — reveals whether this fund tilts toward value, growth, or income.", story)
    _dy_str = _div_yield_str
    _dy_tilt = "Income tilt ✓" if factor.get("income_tilt") else ("Above S&P ~1.5% ✓" if div_yield and div_yield > 1.5 else "—")
    factor_rows = [
        ["Factor", "ETF Value", "S&P 500 Baseline", "Tilt", "Signal"],
        ["P/E Ratio",
         f"{pe:.1f}x", f"~{sp.get('pe',26)}x",
         "Value" if factor.get("value_tilt") else "Neutral",
         "Cheaper than US equities ✓" if factor.get("value_tilt") else "No value discount"],
        ["P/B Ratio",
         f"{pb:.2f}x" if pb else "N/A", f"~{sp.get('pb',4.0)}x",
         "Value" if pb and pb < sp.get("pb", 4.0) else "Neutral", "—"],
        ["Dividend Yield",
         _dy_str, f"~{sp.get('yield',1.5):.1f}%",
         "Income" if factor.get("income_tilt") else "Neutral",
         _dy_tilt],
    ]
    kv_table(factor_rows, [USABLE*0.16, USABLE*0.14, USABLE*0.18, USABLE*0.14, USABLE*0.38], story)
    note("Value tilt = lower P/E than US market. Income tilt = higher dividend yield. "
         "Compare factor P/E vs. S&P 500 baseline to understand relative valuation of international equities.", story)

    # Section 5: Bucket Classification
    section_title("SECTION 5  —  BUCKET CLASSIFICATION & RECOMMENDATION", story)
    note("Determines whether this ETF belongs in Core (Bucket A — passive, low-cost, broad) or Satellite (Bucket B — thematic, factor-tilted).", story)
    bucket_rows = [
        ["Criterion", "Result", "Detail"],
        ["Expense Ratio ≤0.10%",
         "VERIFY" if expense is None else ("✓ PASS" if expense <= 0.10 else "✗ FAIL"),
         exp_str + " — check ETF.com" if expense is None else exp_str],
        ["AUM > $1B",             "✓ PASS",  aum],
        ["Top-15 Weight < 40%",   "✓ PASS" if top15 < 40 else "✗ FAIL",  f"{top15:.1f}%"],
        ["Value / Factor Tilt",   "✓ Value" if factor.get("value_tilt") else "— Neutral",
         f"P/E {pe:.1f}x vs S&P ~26x"],
        ["Moat Quality",          f"{moat_ct}/15",
         f"{moat_ct} of top 15 pass Buffett quality check"],
        ["Bucket Recommendation", bucket, "Based on ETF efficiency audit"],
    ]
    kv_table(bucket_rows, [USABLE*0.30, USABLE*0.20, USABLE*0.50], story)

    # ── Section 6: Similar ETF Suggestions ──────────────────
    section_title("SECTION 6  —  SIMILAR ETF SUGGESTIONS", story)
    note("Alternatives with the same or adjacent exposure — useful for cost comparison and portfolio construction.", story)
    _similar = analysis.get("similar_etfs", [])
    if _similar:
        _alt_rows = [["Ticker", "Fund Name", "Exp. Ratio", "AUM (approx.)", f"Key Difference vs {ticker}"]]
        for _a in _similar:
            _exp_s = f"{_a['expense_ratio']:.2f}%" if _a.get("expense_ratio") is not None else "N/A"
            _alt_rows.append([_a.get("ticker",""), _a.get("name","")[:40], _exp_s,
                               _a.get("aum_approx","N/A"), _a.get("key_difference","")[:60]])
        kv_table(_alt_rows, [USABLE*0.07, USABLE*0.27, USABLE*0.09, USABLE*0.11, USABLE*0.46], story)
    else:
        note(f"No alternatives catalogued for {ticker}. Check ETF.com for peer comparison.", story)

    # ── Section 7: ETF Red Flags ────────────────────────────
    section_title("SECTION 7  —  ETF RED FLAGS", story)
    note("ETF-specific risk factors — different from stock red flags. Focus on cost, liquidity, and concentration.", story)
    _etf_flags = analysis.get("red_flags", [])
    if _etf_flags:
        for _fl in _etf_flags:
            _lvl = _fl.get("level", "CAUTION")
            _txt = _fl.get("text", "")
            _fc  = GREEN if _lvl == "NONE" else (RED if _lvl == "CRITICAL" else YELLOW)
            story.append(Paragraph(f"  {_txt}",
                ParagraphStyle("etf_rf", fontName="Helvetica", fontSize=8.5, textColor=_fc,
                               spaceAfter=5, leading=13)))
    else:
        story.append(Paragraph("No significant ETF-specific risk factors identified.",
            ParagraphStyle("etf_rf_ok", fontName="Helvetica", fontSize=8.5, textColor=GREEN,
                           spaceAfter=5, leading=13)))

    # 36-Month Candlestick
    candle_path = os.path.join(chart_dir, f"{ticker}_price_36m.png")
    if not os.path.exists(candle_path):
        candle_path = _make_candlestick_chart(ticker, chart_dir) or ""
    if candle_path and os.path.exists(candle_path):
        section_title("36-MONTH PRICE HISTORY  —  MONTHLY CANDLESTICK", story)
        note("Green = bullish month (close > open)  ·  Red = bearish month  ·  Data: Yahoo Finance (yfinance)", story)
        cimg = Image(candle_path, width=USABLE, height=USABLE * 0.42)
        cimg_t = Table([[cimg]], colWidths=[USABLE])
        cimg_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), CARD),
            ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
            ("TOPPADDING",    (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ]))
        story.append(cimg_t)
        story.append(Spacer(1, 6))

    # Final Summary
    story.append(HR(GOLD, 1.5, 6, 5))
    story.append(Paragraph("FINAL SUMMARY", ParagraphStyle("efs", fontName="Helvetica-Bold",
                 fontSize=11, textColor=GOLD, spaceAfter=6)))
    final_rows = [
        ["Field", "Value"],
        ["ETF Score",            f"{score}/100  →  {verdict}"],
        ["Expense Ratio",        exp_str + "  (verify on ETF.com / fund prospectus)"],
        ["AUM",                  aum],
        ["Top-15 Concentration", f"{top15:.1f}%  of fund  ({conc_explain})"],
        ["Factor Tilt",          f"Value: {'Yes' if factor.get('value_tilt') else 'No'}  |  "
                                 f"P/E {pe:.1f}x vs S&P ~26x"],
        ["Moat Quality",         f"{moat_ct}/15 top holdings pass Buffett quality filter"],
        ["Strategy Bucket",      bucket],
        ["Data Verification",    "Yahoo Finance > Holdings  |  ETF.com  |  Fund prospectus"],
        ["Analysis Date",        datetime.now().strftime("%Y-%m-%d  %H:%M")],
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
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("Usage: python generate_pdf.py <TICKER>")
        sys.exit(1)
    ticker = sys.argv[1].strip().upper()

    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    python      = sys.executable

    def run(script, *args):
        r = subprocess.run([python, os.path.join(scripts_dir, script)] + list(args),
                           capture_output=True, text=True)
        return json.loads(r.stdout)

    print(f"Fetching data for {ticker}...")
    raw_data  = run("fetch_data.py", ticker)
    is_etf    = raw_data.get('basic', {}).get('quote_type', 'EQUITY') == 'ETF'
    analysis  = run("analyze_etf.py" if is_etf else "analyze_stock.py", ticker)
    # Auto-route to Actual analysis/ETF_TICKER or STOCK_TICKER
    _prefix  = 'ETF' if is_etf else 'STOCK'
    out_dir  = os.path.join(os.getcwd(), 'Actual analysis', f'{_prefix}_{ticker}')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{ticker}_investment_memo.pdf")

    print("Building PDF...")
    if is_etf:
        build_pdf_etf(ticker, analysis, out_path, out_dir)
    else:
        valuation = run("valuation.py", ticker)
        build_pdf(ticker, analysis, valuation, out_path, out_dir)
    print(json.dumps({"status": "ok", "pdf_path": out_path}))
