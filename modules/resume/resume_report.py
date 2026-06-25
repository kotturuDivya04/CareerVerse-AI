# =============================================================================
# modules/resume/resume_report.py  —  CareerVerse AI
# Generates a polished PDF report for Resume Analyzer
# =============================================================================

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.units import inch


def generate_resume_pdf(output_path, user_name, resume_name, role, result):
    """
    Generate Resume Analyzer PDF report.

    Parameters
    ----------
    output_path : str
        Full output PDF path
    user_name : str
        Logged in user name
    resume_name : str
        Uploaded resume filename
    role : str
        Selected target role
    result : dict
        Output from analyze_resume()
    """

    # -------------------------------------------------------------------------
    # Extract values safely from result
    # -------------------------------------------------------------------------
    ats_score = result.get("ats_score", 0)
    role_match_score = result.get("role_match_score", 0)
    skills_found = result.get("skills_found", [])
    missing_skills = result.get("missing_skills", [])
    strengths = result.get("strengths", [])
    suggestions = result.get("suggestions", [])
    section_scores = result.get("section_scores", {})

    # -------------------------------------------------------------------------
    # PDF document setup
    # -------------------------------------------------------------------------
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    # -------------------------------------------------------------------------
    # Custom styles
    # -------------------------------------------------------------------------
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=colors.HexColor("#6C3EF4"),
        alignment=TA_CENTER,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#6B7280"),
        alignment=TA_CENTER,
        leading=14,
        spaceAfter=18
    )

    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=colors.white,
        backColor=colors.HexColor("#6C3EF4"),
        leftIndent=0,
        rightIndent=0,
        spaceBefore=10,
        spaceAfter=8,
        borderPadding=(6, 8, 6)
    )

    label_style = ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.HexColor("#111827"),
        leading=14
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#374151"),
        leading=14,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        "BulletStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#374151"),
        leading=14,
        leftIndent=12,
        bulletIndent=0,
        spaceAfter=4
    )

    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#6B7280"),
        leading=12
    )

    score_big_style = ParagraphStyle(
        "ScoreBig",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#111827"),
        alignment=TA_CENTER
    )

    score_label_style = ParagraphStyle(
        "ScoreLabel",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#6B7280"),
        alignment=TA_CENTER
    )

    # -------------------------------------------------------------------------
    # Helper functions
    # -------------------------------------------------------------------------
    def section_header(text):
        return Paragraph(text, section_title_style)

    def list_to_paragraphs(items, empty_text="Not available"):
        if not items:
            return [Paragraph(empty_text, normal_style)]
        return [Paragraph(f"• {item}", bullet_style) for item in items]

    def dict_to_table(data_dict):
        if not data_dict:
            return Table([["No section score data available", "—"]], colWidths=[300, 120])

        rows = [["Section", "Score"]]
        for key, value in data_dict.items():
            label = str(key).replace("_", " ").title()
            rows.append([label, str(value)])

        table = Table(rows, colWidths=[300, 120])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6C3EF4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),

            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#111827")),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),

            ("ALIGN", (1, 1), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return table

    # -------------------------------------------------------------------------
    # Build PDF elements
    # -------------------------------------------------------------------------
    elements = []

    # Title
    elements.append(Paragraph("CareerVerse AI", title_style))
    elements.append(Paragraph("Smart Resume Analysis Report", subtitle_style))
    elements.append(Spacer(1, 6))

    # User / file details
    info_data = [
        ["Candidate", user_name],
        ["Resume File", resume_name],
        ["Target Role", role]
    ]

    info_table = Table(info_data, colWidths=[110, 390])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2FF")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 16))

    # Scores cards
    score_data = [
        [
            Paragraph(f"{ats_score}", score_big_style),
            Paragraph(f"{role_match_score}%", score_big_style)
        ],
        [
            Paragraph("ATS Score", score_label_style),
            Paragraph("Role Match Score", score_label_style)
        ]
    ]

    score_table = Table(score_data, colWidths=[250, 250], rowHeights=[32, 24])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#E0F2FE")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#EDE9FE")),
        ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#F8FAFC")),
        ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#D1D5DB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.8, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 18))

    # Skills found
    elements.append(section_header("Skills Found"))
    elements.extend(list_to_paragraphs(skills_found, "No matched skills found."))
    elements.append(Spacer(1, 10))

    # Missing skills
    elements.append(section_header("Missing Skills"))
    elements.extend(list_to_paragraphs(missing_skills, "No major missing skills identified."))
    elements.append(Spacer(1, 10))

    # Strengths
    elements.append(section_header("Strengths"))
    elements.extend(list_to_paragraphs(strengths, "No specific strengths available."))
    elements.append(Spacer(1, 10))

    # Suggestions
    elements.append(section_header("Suggestions for Improvement"))
    elements.extend(list_to_paragraphs(suggestions, "No suggestions available."))
    elements.append(Spacer(1, 10))

    # Section scores
    elements.append(section_header("Section-wise Resume Evaluation"))
    elements.append(dict_to_table(section_scores))
    elements.append(Spacer(1, 14))

    # Footer note
    elements.append(Paragraph(
        "This report was generated by CareerVerse AI based on the uploaded resume and selected target role. "
        "Use the suggestions to improve ATS performance and role alignment.",
        small_style
    ))

    # -------------------------------------------------------------------------
    # Build PDF
    # -------------------------------------------------------------------------
    doc.build(elements)