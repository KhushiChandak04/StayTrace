from __future__ import annotations

from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors


def build_report(path: Path, project_name: str, room_name: str, findings: list[dict], claims: list[dict], metadata: dict | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = [
        Paragraph("StayTrace — Visual Condition Evidence Report", styles["Title"]),
        Paragraph(f"Project: {escape(project_name)} | Room: {escape(room_name)}", styles["Normal"]),
        Paragraph(f"Generated: {datetime.now().isoformat(timespec='seconds')}", styles["Normal"]),
        Spacer(1, 16),
    ]
    rows = [["Object / Region", "Status", "Confidence", "Explanation"]]
    for f in findings:
        rows.append([
            str(f.get("object_label", "")),
            str(f.get("status", "")),
            f"{float(f.get('confidence', 0))*100:.0f}%",
            str(f.get("explanation", "")),
        ])
    table = Table(rows, colWidths=[100, 75, 65, 300])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    story += [Paragraph("Comparison findings", styles["Heading2"]), table, Spacer(1, 16)]

    story.append(Paragraph("Claim analyses", styles["Heading2"]))
    if claims:
        for claim in claims:
            story += [
                Paragraph(f"<b>Claim:</b> {escape(str(claim.get('claim', '')))}", styles["Normal"]),
                Paragraph(f"<b>Outcome:</b> {escape(str(claim.get('outcome', '')))}", styles["Normal"]),
                Paragraph(f"{escape(str(claim.get('rationale', '')))}", styles["BodyText"]),
                Spacer(1, 8),
            ]
    else:
        story.append(Paragraph("No claim analyses have been stored.", styles["BodyText"]))

    story += [Spacer(1, 12), Paragraph("Scope note: StayTrace is an evidence organization and visual comparison prototype. It does not determine legal responsibility, causation, or liability.", styles["BodyText"])]
    doc.build(story)
    return path
