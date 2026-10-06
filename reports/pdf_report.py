"""
MOVA PDF Report Generator using ReportLab
Produces a beautiful, publication-grade PDF report summarizing the user's session.
Strictly adheres to non-medical language (Section 2) and YOU vs. YOUR PREVIOUS PERFORMANCE (Section 1).
"""

import io
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

class PDFReportGenerator:
    @classmethod
    def generate_pdf(cls, session_metadata: Dict[str, Any],
                     game_results: List[Dict[str, Any]],
                     trend_analysis: Dict[str, Any],
                     coach_text: str) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            'MOVALogo',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=26,
            leading=30,
            textColor=colors.HexColor('#7928CA')
        )
        tagline_style = ParagraphStyle(
            'MOVATagline',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#0070F3')
        )
        heading_style = ParagraphStyle(
            'MOVAHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#1E1E2E')
        )
        body_style = ParagraphStyle(
            'MOVABody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#333333')
        )
        disclaimer_style = ParagraphStyle(
            'MOVADisclaimer',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#777777')
        )

        story = []

        # Header Title
        story.append(Paragraph("MOVA", title_style))
        story.append(Paragraph("MULTIMODAL SPATIAL GAMING & MOVEMENT INTELLIGENCE", tagline_style))
        story.append(Paragraph("<b>MOVE. PLAY. IMPROVE.</b>", body_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#7928CA'), spaceBefore=5, spaceAfter=15))

        # Session Metadata Summary Table
        date_str = session_metadata.get("timestamp", "Recent")
        duration_s = session_metadata.get("duration", 0.0)
        tot_score = session_metadata.get("total_score", 0)
        completed = session_metadata.get("games_completed", len(game_results))

        meta_data = [
            ["Session ID:", session_metadata.get("session_id", "SES-001"), "Date:", str(date_str)[:19]],
            ["Duration:", f"{duration_s:.1f} seconds", "Total Score:", f"{tot_score:,}"],
            ["Games Played:", str(completed), "Comparison:", "YOU vs. PREVIOUS PERFORMANCE"]
        ]
        meta_table = Table(meta_data, colWidths=[110, 160, 110, 160])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#222222')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 15))

        # Personal Trend & AI Coach Briefing
        story.append(Paragraph("AI Movement Coach Observation", heading_style))
        story.append(Paragraph(coach_text or "Great session engagement with consistent spatial pacing.", body_style))
        story.append(Spacer(1, 10))

        # Trend Status
        trend_status = trend_analysis.get("trend_status", "Baseline Established")
        trend_summary = trend_analysis.get("summary", "Personal baseline recorded.")
        story.append(Paragraph(f"<b>Personal Progress Trend:</b> {trend_status}", body_style))
        story.append(Paragraph(trend_summary, body_style))
        story.append(Spacer(1, 15))

        # Game Results Breakdown Table
        story.append(Paragraph("Activity Performance Breakdown", heading_style))
        headers = ["Activity", "Score", "Accuracy", "Reaction", "Coordination", "Stability"]
        table_rows = [headers]

        for res in game_results:
            table_rows.append([
                res.get("game_name", "Game"),
                f"{res.get('score', 0):,}",
                f"{int(res.get('accuracy', 0.8) * 100)}%",
                f"{res.get('reaction_time', 0.7):.2f}s",
                f"{res.get('multimodal_coordination', 85.0):.1f}%",
                f"{res.get('stability_score', 90.0):.1f}"
            ])

        res_table = Table(table_rows, colWidths=[150, 75, 75, 75, 85, 80])
        res_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7928CA')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F6')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ]))
        story.append(res_table)
        story.append(Spacer(1, 20))

        # Important Positioning Disclaimer (Section 2)
        disclaimer = (
            "NOTICE & POSITIONING: MOVA is an experimental multimodal spatial gaming and movement intelligence platform. "
            "MOVA is NOT a medical diagnostic device, medical treatment system, or clinical diagnosis engine. "
            "Metrics reflect interactive gaming performance and are measured strictly against your own historical baseline."
        )
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CCCCCC'), spaceBefore=10, spaceAfter=8))
        story.append(Paragraph(disclaimer, disclaimer_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
