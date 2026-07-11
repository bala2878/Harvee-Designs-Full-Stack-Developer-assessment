from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def to_csv_bytes(columns: list[str], rows: list[dict]) -> bytes:
    df = pd.DataFrame(rows, columns=columns)
    buf = BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def to_excel_bytes(columns: list[str], rows: list[dict]) -> bytes:
    df = pd.DataFrame(rows, columns=columns)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Query Result")
    return buf.getvalue()


def to_pdf_bytes(title: str, columns: list[str], rows: list[dict], max_rows: int = 200) -> bytes:

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Heading2"]), Spacer(1, 12)]

    display_rows = rows[:max_rows]
    table_data = [columns] + [[str(r.get(c, "")) for c in columns] for r in display_rows]

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366F1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FC")]),
            ]
        )
    )
    elements.append(table)
    if len(rows) > max_rows:
        elements.append(Spacer(1, 8))
        elements.append(
            Paragraph(f"Showing first {max_rows} of {len(rows)} rows. Use Excel/CSV export for the full result.", styles["Normal"])
        )

    doc.build(elements)
    return buf.getvalue()
