# =============================================================================
# modules/plagiarism/report_generator.py  —  CareerVerse AI
# Clean and properly aligned PDF plagiarism report
# =============================================================================

from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)

# -----------------------------------------------------------------------------
# BRAND COLORS
# -----------------------------------------------------------------------------
COLOR_PRIMARY   = colors.HexColor('#4F46E5')   # indigo
COLOR_SECONDARY = colors.HexColor('#06B6D4')   # cyan
COLOR_ACCENT    = colors.HexColor('#8B5CF6')   # violet
COLOR_SUCCESS   = colors.HexColor('#22C55E')   # green
COLOR_WARNING   = colors.HexColor('#F59E0B')   # amber
COLOR_DANGER    = colors.HexColor('#EF4444')   # red

COLOR_TEXT      = colors.HexColor('#0F172A')
COLOR_MUTED     = colors.HexColor('#64748B')
COLOR_BORDER    = colors.HexColor('#E2E8F0')
COLOR_BG_LIGHT  = colors.HexColor('#F8FAFC')
COLOR_BG_SOFT   = colors.HexColor('#F1F5F9')
COLOR_WHITE     = colors.white


# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def _status_colour(status: str):
    if status == 'High':
        return COLOR_DANGER
    if status == 'Moderate':
        return COLOR_WARNING
    return COLOR_SUCCESS


def _safe(text):
    """Escape minimal HTML-sensitive chars for ReportLab Paragraph."""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _build_styles():
    return {
        'brand_title': ParagraphStyle(
            'brand_title',
            fontName='Helvetica-Bold',
            fontSize=28,
            leading=32,
            alignment=TA_CENTER,
            textColor=COLOR_PRIMARY,
            spaceAfter=4,
        ),

        'brand_tagline': ParagraphStyle(
            'brand_tagline',
            fontName='Helvetica',
            fontSize=11,
            leading=15,
            alignment=TA_CENTER,
            textColor=COLOR_MUTED,
            spaceAfter=12,
        ),

        'report_title': ParagraphStyle(
            'report_title',
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            textColor=COLOR_TEXT,
            spaceAfter=12,
        ),

        'section_title': ParagraphStyle(
            'section_title',
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            alignment=TA_LEFT,
            textColor=COLOR_PRIMARY,
            spaceAfter=8,
            spaceBefore=8,
        ),

        'meta_label': ParagraphStyle(
            'meta_label',
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT,
            textColor=COLOR_MUTED,
            spaceAfter=2,
        ),

        'meta_value': ParagraphStyle(
            'meta_value',
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
            textColor=COLOR_TEXT,
        ),

        'score_pct': ParagraphStyle(
            'score_pct',
            fontName='Helvetica-Bold',
            fontSize=30,
            leading=34,
            alignment=TA_CENTER,
            textColor=COLOR_WARNING,
        ),

        'score_status': ParagraphStyle(
            'score_status',
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            alignment=TA_LEFT,
            textColor=COLOR_TEXT,
        ),

        'score_sub': ParagraphStyle(
            'score_sub',
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            alignment=TA_LEFT,
            textColor=COLOR_MUTED,
        ),

        'stat_value': ParagraphStyle(
            'stat_value',
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            textColor=COLOR_TEXT,
        ),

        'stat_label': ParagraphStyle(
            'stat_label',
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=COLOR_MUTED,
        ),

        'body': ParagraphStyle(
            'body',
            fontName='Helvetica',
            fontSize=10.5,
            leading=16,
            alignment=TA_LEFT,
            textColor=COLOR_TEXT,
        ),

        'match_header_left': ParagraphStyle(
            'match_header_left',
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
            textColor=COLOR_TEXT,
        ),

        'match_header_right': ParagraphStyle(
            'match_header_right',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            textColor=COLOR_SUCCESS,
        ),

        'match_label': ParagraphStyle(
            'match_label',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            alignment=TA_LEFT,
            textColor=COLOR_PRIMARY,
        ),

        'match_text': ParagraphStyle(
            'match_text',
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            alignment=TA_LEFT,
            textColor=COLOR_TEXT,
        ),

        'footer': ParagraphStyle(
            'footer',
            fontName='Helvetica',
            fontSize=8,
            leading=12,
            alignment=TA_CENTER,
            textColor=COLOR_MUTED,
        ),
    }


# -----------------------------------------------------------------------------
# MAIN GENERATOR
# -----------------------------------------------------------------------------
def generate_plagiarism_pdf(
    output_path: str,
    user_name: str,
    file1_name: str,
    file2_name: str,
    similarity: float,
    status: str,
    matched: list,
    summary: str,
    recommendation: str,
) -> None:

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )

    styles = _build_styles()
    story = []

    page_width = A4[0]
    usable_width = page_width - (28 * mm)

    status_color = _status_colour(status)

    # =========================================================================
    # HEADER
    # =========================================================================
    story.append(Spacer(1, 4))
    story.append(Paragraph("CareerVerse AI", styles['brand_title']))
    story.append(Paragraph("Intelligent Career &amp; Document Analysis Platform", styles['brand_tagline']))
    story.append(HRFlowable(width="100%", thickness=1.2, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=12))
    story.append(Paragraph("PLAGIARISM DETECTION REPORT", styles['report_title']))
    story.append(Spacer(1, 4))

    # =========================================================================
    # META CARD (4 equal boxes)
    # =========================================================================
    meta_cells = [
        Paragraph(
            f"<font color='#64748B'><b>GENERATED BY</b></font><br/><br/><b>{_safe(user_name)}</b>",
            ParagraphStyle(
                'meta_box_text', fontName='Helvetica', fontSize=10, leading=14,
                textColor=COLOR_TEXT, alignment=TA_LEFT
            )
        ),
        Paragraph(
            f"<font color='#64748B'><b>GENERATED ON</b></font><br/><br/><b>{datetime.utcnow().strftime('%B %d, %Y')}</b><br/>{datetime.utcnow().strftime('%H:%M UTC')}",
            ParagraphStyle(
                'meta_box_text2', fontName='Helvetica', fontSize=10, leading=14,
                textColor=COLOR_TEXT, alignment=TA_LEFT
            )
        ),
        Paragraph(
            f"<font color='#64748B'><b>DOCUMENT 1</b></font><br/><br/><b>{_safe(file1_name)}</b>",
            ParagraphStyle(
                'meta_box_text3', fontName='Helvetica', fontSize=10, leading=14,
                textColor=COLOR_TEXT, alignment=TA_LEFT
            )
        ),
        Paragraph(
            f"<font color='#64748B'><b>DOCUMENT 2</b></font><br/><br/><b>{_safe(file2_name)}</b>",
            ParagraphStyle(
                'meta_box_text4', fontName='Helvetica', fontSize=10, leading=14,
                textColor=COLOR_TEXT, alignment=TA_LEFT
            )
        ),
    ]

    meta_table = Table(
        [meta_cells],
        colWidths=[usable_width / 4.0] * 4
    )
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_WHITE),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#BFD4FF')),
        ('INNERGRID', (0, 0), (-1, -1), 0.6, COLOR_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 16))

    # =========================================================================
    # SCORE CARD
    # =========================================================================
    matched_sentences_count = len(matched or [])
    matched_paragraphs = max(1, matched_sentences_count // 5) if matched_sentences_count else 0
    words_compared = 0  # optional if not passed here from app.py

    left_score = Table(
        [[Paragraph(f"{similarity:.1f}%", ParagraphStyle(
            'score_big',
            fontName='Helvetica-Bold',
            fontSize=34,
            leading=38,
            alignment=TA_CENTER,
            textColor=status_color
        ))]],
        colWidths=[50 * mm],
        rowHeights=[42 * mm]
    )
    left_score.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, status_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ROUNDEDCORNERS', [20, 20, 20, 20]),
    ]))

    score_right_top = Paragraph(
        f"<font color='{status_color}'><b>{_safe(status)} Similarity</b></font><br/>"
        f"<font color='#64748B'>Overall document similarity score</font>",
        ParagraphStyle(
            'score_right_top',
            fontName='Helvetica',
            fontSize=14,
            leading=20,
            alignment=TA_LEFT,
            textColor=COLOR_TEXT,
        )
    )

    stat1 = Table([[
        Paragraph(str(matched_sentences_count), styles['stat_value']),
        Paragraph(str(matched_paragraphs), styles['stat_value']),
        Paragraph(str(words_compared), styles['stat_value']),
    ], [
        Paragraph("Matched Sentences", styles['stat_label']),
        Paragraph("Matched Paragraphs", styles['stat_label']),
        Paragraph("Words Compared", styles['stat_label']),
    ]], colWidths=[38 * mm, 38 * mm, 38 * mm])

    stat1.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBEFORE', (1, 0), (1, 1), 0.5, COLOR_BORDER),
        ('LINEBEFORE', (2, 0), (2, 1), 0.5, COLOR_BORDER),
    ]))

    right_block = Table(
        [[score_right_top], [Spacer(1, 4)], [stat1]],
        colWidths=[usable_width - 56 * mm]
    )
    right_block.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    score_card = Table(
        [[left_score, right_block]],
        colWidths=[56 * mm, usable_width - 56 * mm]
    )
    score_card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_WHITE),
        ('BOX', (0, 0), (-1, -1), 1.2, colors.HexColor('#FFD7A0') if status == 'Moderate' else status_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [14, 14, 14, 14]),
    ]))
    story.append(score_card)
    story.append(Spacer(1, 16))

    # =========================================================================
    # SUMMARY CARD
    # =========================================================================
    story.append(Paragraph("SUMMARY", styles['section_title']))

    summary_table = Table(
        [[Paragraph(_safe(summary), styles['body'])]],
        colWidths=[usable_width]
    )
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FBFF')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#BFD4FF')),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [12, 12, 12, 12]),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # =========================================================================
    # MATCHED PASSAGES
    # =========================================================================
    story.append(Paragraph("MATCHED PASSAGES", styles['section_title']))
    story.append(Spacer(1, 2))

    if matched:
        for idx, match in enumerate(matched, start=1):
            sim_pct = float(match.get('similarity', 0))
            doc1 = _safe(match.get('doc1_sentence', ''))
            doc2 = _safe(match.get('doc2_sentence', ''))

            if sim_pct >= 70:
                match_color = COLOR_SUCCESS
                badge_bg = colors.HexColor('#ECFDF3')
            elif sim_pct >= 40:
                match_color = COLOR_WARNING
                badge_bg = colors.HexColor('#FFF7ED')
            else:
                match_color = COLOR_PRIMARY
                badge_bg = colors.HexColor('#EEF2FF')

            header_table = Table(
                [[
                    Paragraph(f"Match {idx}", styles['match_header_left']),
                    Paragraph(
                        f"<font color='{match_color}'><b>{sim_pct:.1f}% MATCH</b></font>",
                        ParagraphStyle(
                            f'match_pct_{idx}',
                            fontName='Helvetica-Bold',
                            fontSize=10,
                            leading=12,
                            alignment=TA_CENTER,
                            textColor=match_color
                        )
                    )
                ]],
                colWidths=[usable_width - 42 * mm, 42 * mm]
            )
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), COLOR_BG_SOFT),
                ('BACKGROUND', (1, 0), (1, 0), badge_bg),
                ('BOX', (0, 0), (-1, -1), 0.7, COLOR_BORDER),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            body_table = Table(
                [
                    [Paragraph("Document 1:", styles['match_label']), Paragraph(doc1, styles['match_text'])],
                    [Paragraph("Document 2:", styles['match_label']), Paragraph(doc2, styles['match_text'])],
                ],
                colWidths=[28 * mm, usable_width - 28 * mm]
            )
            body_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), COLOR_WHITE),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#FFFDF8')),
                ('BOX', (0, 0), (-1, -1), 0.7, COLOR_BORDER),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))

            story.append(header_table)
            story.append(body_table)
            story.append(Spacer(1, 10))
    else:
        empty_table = Table(
            [[Paragraph("No significant matched passages were detected between the uploaded documents.", styles['body'])]],
            colWidths=[usable_width]
        )
        empty_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ]))
        story.append(empty_table)
        story.append(Spacer(1, 10))

    # =========================================================================
    # RECOMMENDATION
    # =========================================================================
    story.append(Spacer(1, 4))
    story.append(Paragraph("RECOMMENDATION", styles['section_title']))

    recommendation_table = Table(
        [[Paragraph(_safe(recommendation), styles['body'])]],
        colWidths=[usable_width]
    )
    recommendation_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7FFF9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#B7E4C7')),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [12, 12, 12, 12]),
    ]))
    story.append(recommendation_table)
    story.append(Spacer(1, 18))

    # =========================================================================
    # FOOTER
    # =========================================================================
    story.append(HRFlowable(width="100%", thickness=0.7, color=COLOR_BORDER, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "This report was generated automatically by CareerVerse AI. Results are based on semantic text comparison and should be reviewed by a qualified instructor or supervisor before taking action.",
        styles['footer']
    ))

    doc.build(story)