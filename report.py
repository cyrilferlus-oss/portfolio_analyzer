import io
from datetime import date

import pandas as pd
import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

W, H = A4
BRAND_COLOR = colors.HexColor("#1f4e79")
ACCENT_COLOR = colors.HexColor("#2e75b6")
LIGHT_GRAY = colors.HexColor("#f2f2f2")
RED_LIGHT = colors.HexColor("#ffe0e0")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", fontSize=22, textColor=BRAND_COLOR,
                                alignment=TA_CENTER, spaceAfter=4, fontName="Helvetica-Bold"),
        "subtitle": ParagraphStyle("subtitle", fontSize=11, textColor=ACCENT_COLOR,
                                   alignment=TA_CENTER, spaceAfter=2, fontName="Helvetica"),
        "section": ParagraphStyle("section", fontSize=13, textColor=BRAND_COLOR,
                                  spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold"),
        "normal": base["Normal"],
        "caption": ParagraphStyle("caption", fontSize=8, textColor=colors.gray,
                                  alignment=TA_CENTER, fontName="Helvetica-Oblique"),
    }


def _chart_to_image(fig: go.Figure, width_px: int = 500, height_px: int = 300) -> io.BytesIO:
    img_bytes = fig.to_image(format="png", width=width_px, height=height_px, scale=2)
    return io.BytesIO(img_bytes)


def _df_to_table(df: pd.DataFrame, col_widths: list[float] | None = None) -> Table:
    headers = list(df.columns)
    data = [headers] + df.astype(str).values.tolist()

    available = W - 4 * cm
    if col_widths is None:
        col_widths = [available / len(headers)] * len(headers)

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ])
    tbl.setStyle(style)
    return tbl


def generate_pdf(
    summary_df: pd.DataFrame,
    overweight_df: pd.DataFrame,
    fig_geo: go.Figure,
    fig_holdings: go.Figure,
    fig_currency: go.Figure,
    fig_category: go.Figure,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )

    S = _styles()
    story = []

    # ── PAGE 1 ──────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Rapport d'Analyse de Portefeuille", S["title"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"Généré le {date.today().strftime('%d/%m/%Y')}", S["subtitle"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=12))

    story.append(Paragraph("Composition du portefeuille", S["section"]))
    col_w = [2.8, 3.2, 2.2, 2.2, 2.2, 2.0, 1.8]
    story.append(_df_to_table(summary_df, col_widths=[x * cm for x in col_w]))

    if not overweight_df.empty:
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("Positions > 5% du portefeuille", S["section"]))
        story.append(_df_to_table(overweight_df))

    story.append(PageBreak())

    # ── PAGE 2 ──────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Analyses Graphiques", S["title"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=10))

    chart_w_cm = (W - 4 * cm) / 2
    chart_h_cm = chart_w_cm * 0.62

    charts = [
        (fig_geo, "Répartition Géographique"),
        (fig_holdings, "Répartition par Action"),
        (fig_currency, "Répartition par Devise"),
        (fig_category, "Répartition par Catégorie"),
    ]

    for i in range(0, len(charts), 2):
        row_items = []
        for fig, caption in charts[i:i + 2]:
            img_buf = _chart_to_image(fig, width_px=520, height_px=320)
            img = Image(img_buf, width=chart_w_cm, height=chart_h_cm)
            cap = Paragraph(caption, S["caption"])
            cell = Table([[img], [cap]], colWidths=[chart_w_cm])
            cell.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
            row_items.append(cell)

        if len(row_items) == 1:
            row_items.append("")

        grid = Table([row_items], colWidths=[chart_w_cm, chart_w_cm])
        grid.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(grid)
        story.append(Spacer(1, 0.3 * cm))

    doc.build(story)
    return buf.getvalue()
