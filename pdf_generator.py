from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

# ── Brand Colors ──────────────────────────────────────────────
NAVY        = colors.HexColor("#0B1F3A")
TEAL        = colors.HexColor("#00A99D")
LIGHT_GRAY  = colors.HexColor("#F0F4F8")
WHITE       = colors.white
DARK_TEXT   = colors.HexColor("#1A1A2E")
LINK_BLUE   = colors.HexColor("#0000FF")


def star_string(rating) -> str:
    """Convert a number like 3 into stars like ★★★☆☆"""
    try:
        n = int(rating)
        return "★" * n + "☆" * (5 - n)
    except:
        return str(rating)


def generate_pdf(data: dict) -> bytes:
    """
    Takes the report data dictionary from cms_client.py
    and builds a polished PDF using ReportLab.
    Returns the PDF as bytes so FastAPI can stream it.
    """

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.5 * inch
    )

    elements = []

    # ── Text Styles ───────────────────────────────────────────
    platform_style = ParagraphStyle(
        "platform",
        fontSize=10,
        textColor=TEAL,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        leading=14
    )
    title_style = ParagraphStyle(
        "title",
        fontSize=15,
        textColor=WHITE,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        leading=20
    )
    state_style = ParagraphStyle(
        "state",
        fontSize=12,
        textColor=WHITE,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        leading=16
    )
    label_style = ParagraphStyle(
        "label",
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=DARK_TEXT,
        leftIndent=4
    )
    value_style = ParagraphStyle(
        "value",
        fontSize=9,
        fontName="Helvetica",
        textColor=DARK_TEXT,
        leftIndent=4
    )
    link_style = ParagraphStyle(
        "link",
        fontSize=8,
        fontName="Helvetica",
        textColor=LINK_BLUE,
        leftIndent=4
    )

    # ── Header Banner ─────────────────────────────────────────
    # This is the dark navy banner at the top
    # INFINITE branding is always hardcoded here — never dynamic
    header_data = [
        [Paragraph(data["platform"], platform_style)],
        [Paragraph(data["report_title"], title_style)],
        [Paragraph(data["state"], state_style)],
    ]

    header_table = Table(header_data, colWidths=[7.5 * inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 0.2 * inch))

    # ── Helper to build a table row ───────────────────────────
    def row(label, value, is_star=False):
        val = star_string(value) if is_star else str(value)
        return [
            Paragraph(label, label_style),
            Paragraph(val, value_style)
        ]

    # ── Medicare hyperlink row ────────────────────────────────
    medicare_link = (
        f'<link href="{data["medicare_url"]}" color="blue">'
        f'View on Medicare Care Compare →'
        f'</link>'
    )

    # ── Report Data Table ─────────────────────────────────────
    # This is the two-column table with all 26 fields
    table_data = [
        # Header row
        [
            Paragraph("Field", label_style),
            Paragraph("Value", label_style)
        ],

        # Facility info — from CMS API and manual inputs
        row("Name of Facility",                             data["facility_name"]),
        row("Location",                                     data["location"]),
        row("EMR",                                          data["emr"]),
        row("Census Capacity",                              data["census_capacity"]),
        row("Current Census",                               data["current_census"]),
        row("Type of Patient",                              data["patient_type"]),
        row("Previous Coverage from Medelite",              data["previous_coverage"]),
        row("Previous Provider Performance from Medelite",  data["previous_performance"]),
        row("Medical Coverage",                             data["medical_coverage"]),

        # Star ratings — from CMS API
        row("Overall Star Rating",      data["overall_rating"],         is_star=True),
        row("Health Inspection",        data["health_inspection_rating"],is_star=True),
        row("Staffing",                 data["staffing_rating"],         is_star=True),
        row("Quality of Resident Care", data["quality_measure_rating"],  is_star=True),

        # 12 Hospitalization and ED metrics — from CMS Claims API
        row("Short Term Hospitalization",           data["str_hospitalization"]),
        row("STR National Avg. for Hospitalization",data["str_hosp_national_avg"]),
        row("STR State Avg. for Hospitalization",   data["str_hosp_state_avg"]),
        row("STR ED Visit",                         data["str_ed_visit"]),
        row("STR ED Visits National Avg.",          data["str_ed_national_avg"]),
        row("STR ED Visits State Avg.",             data["str_ed_state_avg"]),
        row("LT Hospitalization",                   data["lt_hospitalization"]),
        row("LT National Avg. for Hospitalization", data["lt_hosp_national_avg"]),
        row("LT State Avg. for Hospitalization",    data["lt_hosp_state_avg"]),
        row("ED Visit",                             data["lt_ed_visit"]),
        row("LT ED Visits National Avg.",           data["lt_ed_national_avg"]),
        row("LT ED Visits State Avg.",              data["lt_ed_state_avg"]),

        # Medicare source hyperlink — required by the brief
        [
            Paragraph("Medicare Source", label_style),
            Paragraph(medicare_link, link_style)
        ],
    ]

    report_table = Table(
        table_data,
        colWidths=[3.2 * inch, 4.3 * inch]
    )

    # ── Table Styling ─────────────────────────────────────────
    report_table.setStyle(TableStyle([
        # Header row styling
        ("BACKGROUND",  (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),

        # Grid lines
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D8E4")),

        # Alternating row colors
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),

        # Padding for all cells
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),

        # Vertical alignment
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(report_table)

    # ── Build the PDF ─────────────────────────────────────────
    doc.build(elements)
    return buffer.getvalue()