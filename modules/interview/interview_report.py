# =============================================================================
# modules/interview/interview_report.py  —  CareerVerse AI
# Generates a professional PDF Interview Preparation Report using ReportLab.
#
# Called by app.py after generate_interview_questions() returns results.
# Output saved to /reports/ and served via /download/report/<id>.
# =============================================================================

from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, KeepTogether
)

# Brand colours — match CareerVerse AI CSS design tokens
COLOR_PRIMARY   = colors.HexColor('#4F46E5')
COLOR_SECONDARY = colors.HexColor('#06B6D4')
COLOR_ACCENT    = colors.HexColor('#8B5CF6')
COLOR_SUCCESS   = colors.HexColor('#22C55E')
COLOR_WARNING   = colors.HexColor('#F59E0B')
COLOR_TEXT      = colors.HexColor('#1E293B')
COLOR_MUTED     = colors.HexColor('#64748B')
COLOR_BORDER    = colors.HexColor('#E2E8F0')
COLOR_BG_LIGHT  = colors.HexColor('#F8FAFC')

# Per-category accent colours (match interview.html accordion headers)
CATEGORY_COLORS = {
    'technical':  (colors.HexColor('#EDE9FE'), COLOR_PRIMARY),    # violet
    'hr':         (colors.HexColor('#E0F9FF'), COLOR_SECONDARY),   # cyan
    'project':    (colors.HexColor('#F3E8FF'), COLOR_ACCENT),      # purple
    'behavioral': (colors.HexColor('#FFF7ED'), COLOR_WARNING),     # amber
}

CATEGORY_LABELS = {
    'technical':  'Technical Questions',
    'hr':         'HR Questions',
    'project':    'Project Questions',
    'behavioral': 'Behavioral Questions',
}


# =============================================================================
# STYLES
# =============================================================================

def _build_styles() -> dict:
    return {
        'report_title': ParagraphStyle(
            'RT', fontName='Helvetica-Bold', fontSize=22,
            textColor=COLOR_PRIMARY, alignment=TA_CENTER, spaceAfter=4,
        ),
        'report_subtitle': ParagraphStyle(
            'RS', fontName='Helvetica', fontSize=11,
            textColor=COLOR_MUTED, alignment=TA_CENTER, spaceAfter=2,
        ),
        'section_title': ParagraphStyle(
            'ST', fontName='Helvetica-Bold', fontSize=13,
            textColor=COLOR_TEXT, spaceBefore=14, spaceAfter=2,
        ),
        'meta': ParagraphStyle(
            'ME', fontName='Helvetica', fontSize=9,
            textColor=COLOR_MUTED, spaceAfter=3,
        ),
        'body': ParagraphStyle(
            'BO', fontName='Helvetica', fontSize=10,
            textColor=COLOR_TEXT, leading=15,
            alignment=TA_JUSTIFY, spaceAfter=4,
        ),
        'question_num': ParagraphStyle(
            'QN', fontName='Helvetica-Bold', fontSize=10,
            textColor=COLOR_PRIMARY,
        ),
        'question_text': ParagraphStyle(
            'QT', fontName='Helvetica', fontSize=10,
            textColor=COLOR_TEXT, leading=15, spaceAfter=2,
        ),
        'tip': ParagraphStyle(
            'TIP', fontName='Helvetica-Oblique', fontSize=9,
            textColor=COLOR_MUTED, leading=13, spaceAfter=6,
        ),
        'category_label': ParagraphStyle(
            'CL', fontName='Helvetica-Bold', fontSize=12,
            textColor=COLOR_TEXT, spaceAfter=2,
        ),
        'count_badge': ParagraphStyle(
            'CB', fontName='Helvetica-Bold', fontSize=10,
            textColor=COLOR_MUTED, alignment=TA_LEFT,
        ),
        'footer': ParagraphStyle(
            'FT', fontName='Helvetica', fontSize=8,
            textColor=COLOR_MUTED, alignment=TA_CENTER,
        ),
    }


# =============================================================================
# ANSWER TIP HINTS (shown below each question as a preparation guide)
# =============================================================================

_TIPS = {
    'technical':  'Tip: Structure your answer with a brief explanation, a concrete example from your work, and the outcome.',
    'hr':         'Tip: Be concise and specific. Tie your answer back to the role and the company where possible.',
    'project':    'Tip: Use the STAR format — Situation, Task, Action, Result — to walk through your project clearly.',
    'behavioral': 'Tip: Use the STAR format — Situation, Task, Action, Result — and keep the focus on your individual contribution.',
}


# =============================================================================
# CATEGORY SECTION RENDERER
# =============================================================================

def _render_category(
    category: str,
    questions: list[str],
    styles: dict,
    W: float,
) -> list:
    """Build the flowable elements for one accordion/category section."""
    bg_color, accent_color = CATEGORY_COLORS.get(
        category, (COLOR_BG_LIGHT, COLOR_PRIMARY)
    )
    label = CATEGORY_LABELS.get(category, category.title())
    tip   = _TIPS.get(category, '')
    elements = []

    # ---- Category header bar ----
    header_tbl = Table(
        [[
            Paragraph(label, ParagraphStyle(
                'CH', fontName='Helvetica-Bold', fontSize=12,
                textColor=accent_color,
            )),
            Paragraph(f'{len(questions)} Questions', ParagraphStyle(
                'CQ', fontName='Helvetica', fontSize=10,
                textColor=COLOR_MUTED, alignment=TA_LEFT,
            )),
        ]],
        colWidths=[W * 0.75, W * 0.25],
    )
    header_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('BOX',        (0, 0), (-1, -1), 1.0, accent_color),
        ('PADDING',    (0, 0), (-1, -1), 10),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(KeepTogether([header_tbl]))
    elements.append(Spacer(1, 4))

    # ---- Tip line ----
    if tip:
        elements.append(Paragraph(tip, styles['tip']))

    # ---- Questions ----
    for i, question in enumerate(questions, start=1):
        q_tbl = Table(
            [[
                Paragraph(f'Q{i}.', styles['question_num']),
                Paragraph(question, styles['question_text']),
            ]],
            colWidths=[12 * mm, W - 12 * mm],
        )
        q_tbl.setStyle(TableStyle([
            ('ROWBACKGROUNDS', (0, 0), (-1, -1),
             [colors.white, COLOR_BG_LIGHT] if i % 2 == 0 else [COLOR_BG_LIGHT, colors.white]),
            ('BOX',      (0, 0), (-1, -1), 0.3, COLOR_BORDER),
            ('PADDING',  (0, 0), (-1, -1), 7),
            ('VALIGN',   (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(q_tbl)
        elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 12))
    return elements


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_interview_pdf(
    output_path: str,
    user_name: str,
    role: str,
    questions: dict,
) -> None:
    """
    Generate and save an Interview Preparation PDF report.

    Parameters:
        output_path — full path where the PDF will be saved
        user_name   — from session, shown in report metadata
        role        — target role string selected by the user
        questions   — dict returned by question_generator.generate_interview_questions()
                      Shape: { "technical": [...], "hr": [...],
                               "project": [...], "behavioral": [...] }
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize     = A4,
        leftMargin   = 20 * mm,
        rightMargin  = 20 * mm,
        topMargin    = 20 * mm,
        bottomMargin = 20 * mm,
    )

    styles = _build_styles()
    story  = []
    W      = A4[0] - 40 * mm

    total_count = sum(len(v) for v in questions.values())

    # -------------------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------------------
    story.append(Paragraph('CareerVerse AI', styles['report_title']))
    story.append(Paragraph(
        'Intelligent Career &amp; Document Analysis Platform',
        styles['report_subtitle']
    ))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width=W, thickness=1, color=COLOR_PRIMARY))
    story.append(Spacer(1, 6))
    story.append(Paragraph('Interview Preparation Report', ParagraphStyle(
        'IH', fontName='Helvetica-Bold', fontSize=15,
        textColor=COLOR_TEXT, alignment=TA_CENTER, spaceAfter=4,
    )))
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # METADATA TABLE
    # -------------------------------------------------------------------------
    meta_rows = [
        ['Prepared For',  user_name],
        ['Generated On',  datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')],
        ['Target Role',   role],
        ['Total Questions', str(total_count)],
    ]
    meta_tbl = Table(
        [[Paragraph(k, styles['meta']), Paragraph(v, styles['body'])]
         for k, v in meta_rows],
        colWidths=[50 * mm, W - 50 * mm],
    )
    meta_tbl.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (0, -1), COLOR_BG_LIGHT),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, COLOR_BG_LIGHT]),
        ('BOX',            (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('INNERGRID',      (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ('PADDING',        (0, 0), (-1, -1), 6),
        ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 14))

    # -------------------------------------------------------------------------
    # SUMMARY BANNER  (4 category count boxes)
    # -------------------------------------------------------------------------
    summary_data = [[
        Paragraph(
            f'<b>{len(questions.get(cat, []))}</b><br/>'
            f'<font color="#64748B" size="9">{CATEGORY_LABELS[cat]}</font>',
            ParagraphStyle(
                f'SB_{cat}', fontName='Helvetica-Bold', fontSize=18,
                textColor=CATEGORY_COLORS[cat][1], alignment=TA_CENTER,
            )
        )
        for cat in ['technical', 'hr', 'project', 'behavioral']
    ]]
    summary_tbl = Table(summary_data, colWidths=[W / 4] * 4)
    summary_tbl.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (0, -1), CATEGORY_COLORS['technical'][0]),
        ('BACKGROUND',  (1, 0), (1, -1), CATEGORY_COLORS['hr'][0]),
        ('BACKGROUND',  (2, 0), (2, -1), CATEGORY_COLORS['project'][0]),
        ('BACKGROUND',  (3, 0), (3, -1), CATEGORY_COLORS['behavioral'][0]),
        ('BOX',         (0, 0), (-1, -1), 1.0, COLOR_PRIMARY),
        ('INNERGRID',   (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('PADDING',     (0, 0), (-1, -1), 14),
        ('ALIGN',       (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(summary_tbl)
    story.append(Spacer(1, 16))

    # -------------------------------------------------------------------------
    # HOW TO USE THIS REPORT
    # -------------------------------------------------------------------------
    story.append(HRFlowable(width=W, thickness=0.5, color=COLOR_BORDER))
    story.append(Spacer(1, 6))
    story.append(Paragraph('How to Use This Report', styles['section_title']))
    story.append(Spacer(1, 4))
    usage_tips = [
        '1.  Review each section before your interview — focus on Technical questions specific to your role.',
        '2.  For Behavioral and Project questions, prepare STAR-format answers (Situation · Task · Action · Result).',
        '3.  Practice answering out loud — fluency matters as much as accuracy.',
        '4.  For HR questions, research the company beforehand so your answers feel personalised.',
        '5.  Use the answer tip under each section as a guide, not a script.',
    ]
    for tip in usage_tips:
        story.append(Paragraph(tip, styles['body']))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width=W, thickness=0.5, color=COLOR_BORDER))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # QUESTION CATEGORIES  (Technical → HR → Project → Behavioral)
    # -------------------------------------------------------------------------
    category_order = ['technical', 'hr', 'project', 'behavioral']
    for category in category_order:
        q_list = questions.get(category, [])
        if not q_list:
            continue
        story.extend(_render_category(category, q_list, styles, W))

    # -------------------------------------------------------------------------
    # FOOTER
    # -------------------------------------------------------------------------
    story.append(HRFlowable(width=W, thickness=0.5, color=COLOR_BORDER))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f'Interview Preparation Report generated by CareerVerse AI · '
        f'{datetime.utcnow().strftime("%B %d, %Y")} · '
        f'Target Role: {role} · {total_count} Questions',
        styles['footer']
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        'Questions are generated based on your resume and selected role. '
        'Actual interview questions may vary. Good luck!',
        styles['footer']
    ))

    doc.build(story)