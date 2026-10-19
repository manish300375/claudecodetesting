"""Render a branded PDF (ReportLab) from an analysis JSON.

Usage: python tools/build_report_pdf.py <analysis.json> <out.pdf>
"""
import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_brand import load_brand  # noqa: E402

W, H = A4
MARGIN = 18 * mm


def logo_flowable(path: str, height: float):
    """Return a flowable for the logo (PNG/JPG via Image, SVG via svglib), scaled to `height`."""
    if path.lower().endswith(".svg"):
        from svglib.svglib import svg2rlg
        d = svg2rlg(path)
        s = height / d.height
        d.scale(s, s)
        d.width, d.height = d.width * s, d.height * s
        d.hAlign = "LEFT"
        return d
    img = Image(path)
    s = height / img.imageHeight
    img.drawWidth, img.drawHeight = img.imageWidth * s, height
    img.hAlign = "LEFT"
    return img


def setup_fonts(brand: dict):
    heading, body = "Helvetica-Bold", "Helvetica"
    if brand.get("heading_path"):
        pdfmetrics.registerFont(TTFont("BrandHeading", brand["heading_path"]))
        heading = "BrandHeading"
    if brand.get("body_path"):
        pdfmetrics.registerFont(TTFont("BrandBody", brand["body_path"]))
        body = "BrandBody"
        bold = "BrandBody"
        if brand.get("body_bold_path"):
            pdfmetrics.registerFont(TTFont("BrandBodyBold", brand["body_bold_path"]))
            bold = "BrandBodyBold"
        pdfmetrics.registerFontFamily("BrandBody", normal="BrandBody", bold=bold, italic="BrandBody", boldItalic=bold)
    return heading, body


def esc(v) -> str:
    return escape(str(v)) if v is not None else ""


def render(data: dict, out: Path) -> Path:
    brand = load_brand()
    c = {k: colors.HexColor(v) for k, v in brand["colors"].items()}
    c.setdefault("muted", colors.HexColor("#F3F5F8"))
    heading, body = setup_fonts(brand)

    st = {
        "body": ParagraphStyle("body", fontName=body, fontSize=10, leading=14.5, textColor=c["text"]),
        "small": ParagraphStyle("small", fontName=body, fontSize=8, leading=10, textColor=colors.HexColor("#666666")),
        "h2": ParagraphStyle("h2", fontName=heading, fontSize=17, leading=21, textColor=c["primary"], spaceBefore=10, spaceAfter=4, keepWithNext=1),
        "h3": ParagraphStyle("h3", fontName=heading, fontSize=12, leading=15, textColor=c["primary"], spaceAfter=2),
        "cell": ParagraphStyle("cell", fontName=body, fontSize=9, leading=12, textColor=c["text"]),
        "th": ParagraphStyle("th", fontName=heading, fontSize=9, leading=12, textColor=colors.white),
    }
    P = lambda t, s="body": Paragraph(esc(t), st[s])  # noqa: E731
    story = []

    def h2(t):
        from reportlab.platypus import HRFlowable
        rule = HRFlowable(width="100%", thickness=2, color=c["accent"], spaceAfter=6)
        rule.keepWithNext = 1
        story.extend([Paragraph(esc(t), st["h2"]), rule])

    def card(items):
        t = Table([[items]], colWidths=[W - 2 * MARGIN])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), c["muted"]), ("LINEBEFORE", (0, 0), (0, -1), 3, c["secondary"]),
                               ("LEFTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        story.extend([KeepTogether(t), Spacer(1, 4)])

    def table(header, rows, widths=None):
        data_ = [[Paragraph(esc(h), st["th"]) for h in header]] + [[Paragraph(esc(x), st["cell"]) for x in r] for r in rows]
        t = Table(data_, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), c["primary"]), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c["muted"]]),
                               ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")), ("PADDING", (0, 0), (-1, -1), 4)]))
        story.extend([t, Spacer(1, 8)])

    def bullets(label, items):
        return [Paragraph(f"<b>{esc(label)}</b>", st["body"])] + [Paragraph("• " + esc(i), st["body"]) for i in items]

    cover_title, cover_sub = data["title"], data.get("subtitle", "")
    cover_date = data.get("date", "")
    cover_styles = {
        "title": ParagraphStyle("ct", fontName=heading, fontSize=30, leading=36, textColor=colors.white),
        "sub": ParagraphStyle("cs", fontName=body, fontSize=13, leading=18, textColor=c["accent"]),
        "date": ParagraphStyle("cd", fontName=body, fontSize=10, leading=14, textColor=colors.white),
    }

    def cover(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(c["primary"])
        canvas.rect(0, 0, W, H, stroke=0, fill=1)
        lg = logo_flowable(brand["logo_light_path"], 16 * mm)
        lg.wrapOn(canvas, W, H)
        lg.drawOn(canvas, MARGIN, H - 30 * mm)
        y = H * 0.52
        for text, style in ((cover_title, cover_styles["title"]), (cover_sub, cover_styles["sub"]), (cover_date, cover_styles["date"])):
            para = Paragraph(esc(text), style)
            _, ph = para.wrapOn(canvas, W - 2 * MARGIN, H)
            y -= ph + 8
            para.drawOn(canvas, MARGIN, y)
        canvas.restoreState()

    def later(canvas, doc):
        canvas.saveState()
        lg = logo_flowable(brand["logo_path"], 8 * mm)
        lg.wrapOn(canvas, W, H)
        lg.drawOn(canvas, MARGIN, H - 16 * mm)
        canvas.setStrokeColor(c["accent"])
        canvas.setLineWidth(1.5)
        canvas.line(MARGIN, H - 19 * mm, W - MARGIN, H - 19 * mm)
        canvas.setFont(body, 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawString(MARGIN, 10 * mm, f"{brand['company_name']} · Confidential")
        canvas.drawRightString(W - MARGIN, 10 * mm, str(doc.page - 1))
        canvas.restoreState()

    story.extend([PageBreak()])
    h2("Executive Summary"); story.append(P(data["executive_summary"]))
    h2("Market Overview"); story.append(P(data["market_overview"]))
    h2("Competitor Profiles")
    for comp in data["competitors"]:
        card([Paragraph(f"{esc(comp['name'])} — <font color='#{c['secondary'].hexval()[2:]}' size=9>{esc(comp['category'])}</font>", st["h3"]),
              P(comp["website"], "small"), P(comp["positioning"])] + bullets("Strengths", comp["strengths"]) + bullets("Weaknesses", comp["weaknesses"]))
    if data.get("comparison"):
        h2("Comparison Matrix")
        cmp_ = data["comparison"]
        table([""] + cmp_["columns"], [[r["label"]] + r["values"] for r in cmp_["rows"]])
    h2("What's Working for Competitors")
    for w in data["whats_working"]:
        card([Paragraph(esc(w["competitor"]), st["h3"]), P(w["insight"]), P("Evidence: " + w["evidence"], "small")])
    h2(f"Opportunities for {brand['company_name']}")
    for o in data["opportunities"]:
        card([Paragraph(esc(o["title"]), st["h3"]), P(o["detail"])])
    h2("Prioritized Recommendations")
    table(["Recommendation", "Impact", "Effort"], [[f"{r['title']}: {r['detail']}", r["impact"], r["effort"]] for r in data["recommendations"]],
          [W - 2 * MARGIN - 50 * mm, 25 * mm, 25 * mm])
    if data.get("what_to_watch"):
        h2("What to Watch")
        for w in data["what_to_watch"]:
            story.append(Paragraph("• " + esc(w), st["body"]))
    h2("Sources")
    for s in data["sources"]:
        story.append(P(s, "small"))

    out.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(out), pagesize=A4, title=cover_title, author=brand["company_name"])
    frame = Frame(MARGIN, 18 * mm, W - 2 * MARGIN, H - 40 * mm, id="f")
    doc.addPageTemplates([PageTemplate("cover", [Frame(0, 0, W, H, id="c")], onPage=cover, autoNextPageTemplate="body"),
                          PageTemplate("body", [frame], onPage=later)])
    doc.build(story)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print(render(json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2])))
