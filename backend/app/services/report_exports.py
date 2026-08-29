"""Generic PDF and Excel renderers fed by the shared report service output."""
from io import BytesIO
from datetime import datetime, timezone

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors


def _rows(report):
    rows = []
    for item in report["data"]:
        if isinstance(item, dict) and "items" in item:
            for child in item["items"]:
                rows.append({"section": item.get("section"), **child})
        else: rows.append(item)
    return rows


def report_pdf(report: dict) -> BytesIO:
    output = BytesIO(); doc = SimpleDocTemplate(output, pagesize=A4); styles = getSampleStyleSheet(); story = [Paragraph(report["report_type"].replace("_", " ").title(), styles["Title"]), Paragraph(f"Period: {report['period']['start_date']} to {report['period']['end_date']}", styles["Normal"]), Paragraph(f"Generated: {datetime.now(timezone.utc).isoformat()}", styles["Normal"]), Spacer(1, 12)]
    story.append(Table([[key.replace("_", " "), str(value)] for key, value in report["summary"].items()], colWidths=[190, 330], style=TableStyle([("BACKGROUND", (0,0), (-1,0), colors.whitesmoke), ("GRID", (0,0), (-1,-1), .25, colors.lightgrey)]))); story.append(Spacer(1, 12))
    rows = _rows(report)
    if rows:
        keys = list(dict.fromkeys(key for row in rows for key in row))
        values = [[key.replace("_", " ") for key in keys]] + [[str(row.get(key, ""))[:70] for key in keys] for row in rows]
        story.append(Table(values, repeatRows=1, style=TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#6947c8")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), .25, colors.lightgrey), ("FONTSIZE", (0,0), (-1,-1), 7)])))
    doc.build(story); output.seek(0); return output


def report_excel(report: dict) -> BytesIO:
    book = Workbook(); sheet = book.active; sheet.title = "Report"; sheet.append([report["report_type"].replace("_", " ").title()]); sheet.append(["Period", f"{report['period']['start_date']} to {report['period']['end_date']}"]); sheet.append(["Generated", datetime.now(timezone.utc).isoformat()]); sheet.append([]); sheet.append(["Summary", "Value"])
    for key, value in report["summary"].items(): sheet.append([key.replace("_", " "), str(value)])
    rows = _rows(report)
    if rows:
        sheet.append([]); keys = list(dict.fromkeys(key for row in rows for key in row)); sheet.append(keys)
        for row in rows: sheet.append([str(row.get(key, "")) for key in keys])
    for column in sheet.columns:
        letter = column[0].column_letter; sheet.column_dimensions[letter].width = min(45, max(14, max(len(str(cell.value or "")) for cell in column) + 2))
    output = BytesIO(); book.save(output); output.seek(0); return output
