from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
import os
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

# ── Colors ────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0B1F3A")
TEAL       = colors.HexColor("#00A99D")
BLACK      = colors.HexColor("#000000")
WHITE      = colors.white
LIGHT_GRAY = colors.HexColor("#F5F5F5")
LINK_BLUE  = colors.HexColor("#0000EE")


def star_string(rating) -> str:
    """Convert number to star display"""
    try:
        n = int(rating)
        return f"{'★' * n}{'✩' * (5 - n)}  ({n}/5)"
    except:
        return str(rating)


def generate_pdf(data: dict) -> bytes:
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )

    elements = []

    # ── Styles ────────────────────────────────────────────────
    platform_style = ParagraphStyle(
        "platform",
        fontSize=9,
        textColor=TEAL,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        leading=14,
        spaceAfter=2
    )
    title_style = ParagraphStyle(
        "title",
        fontSize=14,
        textColor=WHITE,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        leading=18,
        spaceAfter=2
    )
    state_style = ParagraphStyle(
        "state",
        fontSize=11,
        textColor=WHITE,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        leading=14
    )
    label_style = ParagraphStyle(
        "label",
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=BLACK,
        leftIndent=4,
        leading=12
    )
    value_style = ParagraphStyle(
        "value",
        fontSize=9,
        fontName="Helvetica",
        textColor=BLACK,
        leftIndent=4,
        leading=12
    )
    link_style = ParagraphStyle(
        "link",
        fontSize=8,
        fontName="Helvetica",
        textColor=LINK_BLUE,
        leftIndent=4
    )

    # ── Header Banner ─────────────────────────────────────────
    # INFINITE branding — always hardcoded, never dynamic
    # ── Logo ──────────────────────────────────────────────────
   # ── Logo ──────────────────────────────────────────────────
    logo_path = os.path.join("static", "logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2.5 * inch, height=0.8 * inch)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 0.1 * inch))

    # ── Title and State below logo ────────────────────────────
    title_para = Paragraph("FACILITY ASSESSMENT SNAPSHOT", ParagraphStyle(
        "title2",
        fontSize=14,
        textColor=colors.HexColor("#424242"),
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        leading=18,
    ))

    state_para = Paragraph(data["state"], ParagraphStyle(
        "state2",
        fontSize=11,
        textColor=colors.HexColor("#2196F3"),
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        leading=14,
    ))

    elements.append(title_para)
    elements.append(Spacer(1, 0.05 * inch))
    elements.append(state_para)
    elements.append(Spacer(1, 0.15 * inch))

    # ── Helper ────────────────────────────────────────────────
    def row(label, value, is_star=False):
        val = star_string(value) if is_star else str(value)
        return [
            Paragraph(label, label_style),
            Paragraph(val, value_style)
        ]

    # ── Medicare link ─────────────────────────────────────────
    medicare_link = (
        f'<link href="{data["medicare_url"]}" color="#0000EE">'
        f'View on Medicare Care Compare →'
        f'</link>'
    )

    # ── Data Table ────────────────────────────────────────────
    table_data = [
        # Facility info
        row("Name of Facility",                             data["facility_name"]),
        row("Location",                                     data["location"]),
        row("EMR",                                          data["emr"]),
        row("Census Capacity",                              data["census_capacity"]),
        row("Current Census",                               data["current_census"]),
        row("Type of Patient",                              data["patient_type"]),
        row("Previous Coverage from Medelite",              data["previous_coverage"]),
        row("Previous Provider Performance from Medelite",  data["previous_performance"]),
        row("Medical Coverage",                             data["medical_coverage"]),

        # Star ratings
        row("Overall Star Rating",       data["overall_rating"],          is_star=True),
        row("Health Inspection",         data["health_inspection_rating"], is_star=True),
        row("Staffing",                  data["staffing_rating"],          is_star=True),
        row("Quality of Resident Care",  data["quality_measure_rating"],   is_star=True),

        # 12 hospitalization metrics
        row("Short Term Hospitalization",            data["str_hospitalization"]),
        row("STR National Avg. for Hospitalization", data["str_hosp_national_avg"]),
        row("STR State Avg. for Hospitalization",    data["str_hosp_state_avg"]),
        row("STR ED Visit",                          data["str_ed_visit"]),
        row("STR ED Visits National Avg.",           data["str_ed_national_avg"]),
        row("STR ED Visits State Avg.",              data["str_ed_state_avg"]),
        row("LT Hospitalization",                    data["lt_hospitalization"]),
        row("LT National Avg. for Hospitalization",  data["lt_hosp_national_avg"]),
        row("LT State Avg. for Hospitalization",     data["lt_hosp_state_avg"]),
        row("ED Visit",                              data["lt_ed_visit"]),
        row("LT ED Visits National Avg.",            data["lt_ed_national_avg"]),
        row("LT ED Visits State Avg.",               data["lt_ed_state_avg"]),

        # Medicare hyperlink — required by brief
        [
            Paragraph("Medicare Source", label_style),
            Paragraph(medicare_link, link_style)
        ],
    ]

    report_table = Table(
        table_data,
        colWidths=[3.0 * inch, 4.0 * inch]
    )

    # ── Table Style — clean white like reference ──────────────
    report_table.setStyle(TableStyle([
        # All borders
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),

        # Outer border thicker
        ("BOX",         (0, 0), (-1, -1), 1, colors.HexColor("#000000")),

        # Alternating row colors — white and very light gray
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),

        # Padding
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),

        # Vertical alignment
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        # Left column bold
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (0, -1), 9),
    ]))

    elements.append(report_table)

    # ── Build ─────────────────────────────────────────────────
    doc.build(elements)
    return buffer.getvalue()