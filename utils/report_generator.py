"""
utils/report_generator.py
──────────────────────────
Generates downloadable CSV and PDF report files from any table data.
Uses Python's built-in csv module for CSV and reportlab for PDF.
"""

import csv
import os
from datetime import datetime
from PyQt6.QtWidgets import QFileDialog, QMessageBox

# ── ReportLab imports (PDF) ───────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, HRFlowable,
    )
    # Colour constants — only defined when reportlab is available
    _RED   = colors.HexColor("#c0392b")
    _DARK  = colors.HexColor("#16213e")
    _LGREY = colors.HexColor("#f0f2f5")
    _WHITE = colors.white
    _BLACK = colors.HexColor("#2d3748")
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def export_csv(parent, title: str, headers: list[str],
               rows: list[list], default_name: str = None) -> bool:
    """
    Open a save-file dialog, write *rows* as CSV, show success toast.
    Returns True if file was saved, False if cancelled.
    """
    if default_name is None:
        stamp       = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"STASH_{title.replace(' ', '_')}_{stamp}.csv"

    filename, _ = QFileDialog.getSaveFileName(
        parent,
        f"Export {title}",
        os.path.join(os.path.expanduser("~"), "Downloads", default_name),
        "CSV Files (*.csv);;All Files (*)",
    )
    if not filename:
        return False

    try:
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            # Report header metadata
            writer.writerow(["STASH – Hotel Inventory Management System"])
            writer.writerow([f"Report: {title}"])
            writer.writerow([f"Generated: {datetime.now().strftime('%B %d, %Y  %H:%M')}"])
            writer.writerow([])
            # Column headers
            writer.writerow(headers)
            # Data rows
            for row in rows:
                writer.writerow([str(v) if v is not None else "" for v in row])

        QMessageBox.information(
            parent, "Report Exported",
            f"✔  Report saved successfully!\n\n{filename}",
        )
        return True

    except Exception as exc:
        QMessageBox.critical(parent, "Export Failed", f"Could not save file:\n{exc}")
        return False


# ── Convenience wrappers ──────────────────────────────────────────────────────

def export_inventory_report(parent, items: list[dict]) -> bool:
    headers = ["ID", "Name", "SKU", "Category", "Unit",
               "Unit Cost (₱)", "Stock Qty", "Min Stock", "Status"]
    rows = [
        [
            r["id"], r["name"], r["sku"] or "", r["category"],
            r["unit"] or "", f"{float(r['unit_cost']):.2f}",
            r["stock_qty"], r["min_stock"],
            "Low Stock" if r["stock_qty"] < r["min_stock"] else "OK",
        ]
        for r in items
    ]
    return export_csv(parent, "Inventory Report", headers, rows)


def export_purchase_report(parent, purchases: list[dict]) -> bool:
    headers = ["ID", "Date", "Supplier", "Created By",
               "Expected Date", "Total (₱)", "Status"]
    rows = [
        [
            r["id"], str(r["created_at"])[:10], r.get("supplier", ""),
            r.get("created_by", ""), str(r.get("expected_date", "")),
            f"{float(r['total_amount']):.2f}", r["status"],
        ]
        for r in purchases
    ]
    return export_csv(parent, "Purchase Report", headers, rows)


def export_low_stock_report(parent, items: list[dict]) -> bool:
    headers = ["Item", "Category", "Current Stock", "Min Stock", "Deficit"]
    rows = [
        [r["name"], r["category"], r["stock_qty"],
         r["min_stock"], r.get("deficit", r["min_stock"] - r["stock_qty"])]
        for r in items
    ]
    return export_csv(parent, "Low Stock Alert Report", headers, rows)


def export_movement_report(parent, movements: list[dict]) -> bool:
    headers = ["ID", "Item", "Movement Type", "Quantity",
               "User", "Department", "Notes", "Date"]
    rows = [
        [
            r["id"], r["item_name"], r["movement_type"],
            r["quantity"], r["user_name"],
            r.get("department", ""), r.get("notes", ""),
            str(r["created_at"])[:16],
        ]
        for r in movements
    ]
    return export_csv(parent, "Inventory Movement Report", headers, rows)


def export_damage_report(parent, damages: list[dict]) -> bool:
    headers = ["ID", "Item", "Category", "Quantity",
               "Reason", "Reported By", "Status", "Date"]
    rows = [
        [
            r["id"], r.get("item_name", ""), r.get("category", ""),
            r["quantity"], r.get("reason", ""),
            r.get("created_by", ""), r["status"],
            str(r["created_at"])[:16],
        ]
        for r in damages
    ]
    return export_csv(parent, "Damage Report", headers, rows)


def export_dept_consumption(parent, items: list[dict], department: str) -> bool:
    headers = ["Item Name", "Total Consumed"]
    rows = [[r["item_name"], r["total_used"]] for r in items]
    return export_csv(parent, f"{department} Consumption Report", headers, rows)



# ── PDF export ────────────────────────────────────────────────────────────────

def export_pdf(parent, title: str, headers: list[str],
               rows: list[list], default_name: str = None) -> bool:
    """
    Open a save-file dialog, write a styled PDF report, show success toast.
    Returns True if saved, False if cancelled or reportlab not installed.
    """
    if not HAS_REPORTLAB:
        QMessageBox.warning(
            parent, "Missing Library",
            "reportlab is not installed.\n\n"
            "Run:  pip install reportlab\n\nThen restart the application.",
        )
        return False

    if default_name is None:
        stamp        = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"STASH_{title.replace(' ', '_')}_{stamp}.pdf"

    filename, _ = QFileDialog.getSaveFileName(
        parent,
        f"Export {title} as PDF",
        os.path.join(os.path.expanduser("~"), "Downloads", default_name),
        "PDF Files (*.pdf);;All Files (*)",
    )
    if not filename:
        return False

    try:
        # Use landscape for wide tables (many columns)
        page = landscape(A4) if len(headers) > 6 else A4
        doc  = SimpleDocTemplate(
            filename,
            pagesize=page,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=2*cm,    bottomMargin=2*cm,
        )

        styles = getSampleStyleSheet()
        story  = []

        # ── Header block ──────────────────────────────────────────────────────
        story.append(Paragraph(
            "STASH – Hotel Inventory Management System",
            ParagraphStyle("brand", fontSize=14, textColor=_RED,
                           fontName="Helvetica-Bold", spaceAfter=4),
        ))
        story.append(Paragraph(
            title,
            ParagraphStyle("rptitle", fontSize=11, textColor=_DARK,
                           fontName="Helvetica-Bold", spaceAfter=2),
        ))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y  %H:%M')}",
            ParagraphStyle("meta", fontSize=8, textColor=colors.HexColor("#718096"),
                           spaceAfter=8),
        ))
        story.append(HRFlowable(width="100%", thickness=1,
                                color=_RED, spaceAfter=10))

        # ── Table data ────────────────────────────────────────────────────────
        safe_headers = [str(h) for h in headers]
        safe_rows    = [[str(v) if v is not None else "" for v in r] for r in rows]
        table_data   = [safe_headers] + safe_rows

        # Auto-distribute column widths
        page_w = page[0] - 3*cm   # usable width
        col_w  = page_w / max(len(headers), 1)
        col_widths = [col_w] * len(headers)

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            # Header row
            ("BACKGROUND",  (0, 0), (-1, 0), _DARK),
            ("TEXTCOLOR",   (0, 0), (-1, 0), _WHITE),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, 0), 8),
            ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
            ("TOPPADDING",  (0, 0), (-1, 0), 7),
            ("BOTTOMPADDING",(0,0), (-1, 0), 7),
            # Data rows
            ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 1), (-1, -1), 7.5),
            ("ALIGN",       (0, 1), (-1, -1), "CENTER"),
            ("TOPPADDING",  (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING",(0,1), (-1, -1), 5),
            # Alternating row colours
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _LGREY]),
            # Grid
            ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
            ("BOX",         (0, 0), (-1, -1), 0.8, _DARK),
            ("LINEBELOW",   (0, 0), (-1, 0),  1.2, _RED),
        ]))
        story.append(tbl)

        # ── Footer note ───────────────────────────────────────────────────────
        story.append(Spacer(1, 14))
        story.append(Paragraph(
            f"Total records: {len(rows)}   |   "
            "STASH Hotel Inventory Management System",
            ParagraphStyle("footer", fontSize=7,
                           textColor=colors.HexColor("#a0aec0"),
                           alignment=TA_CENTER),
        ))

        doc.build(story)

        QMessageBox.information(
            parent, "PDF Exported",
            f"Report saved successfully!\n\n{filename}",
        )
        return True

    except Exception as exc:
        QMessageBox.critical(parent, "Export Failed", f"Could not save PDF:\n{exc}")
        return False


# ── PDF convenience wrappers ──────────────────────────────────────────────────

def export_inventory_pdf(parent, items: list[dict]) -> bool:
    headers = ["ID", "Name", "SKU", "Category", "Unit",
               "Unit Cost (PHP)", "Stock Qty", "Min Stock", "Status"]
    rows = [
        [
            r["id"], r["name"], r["sku"] or "", r["category"],
            r["unit"] or "", f"{float(r['unit_cost']):.2f}",
            r["stock_qty"], r["min_stock"],
            "Low Stock" if r["stock_qty"] < r["min_stock"] else "OK",
        ]
        for r in items
    ]
    return export_pdf(parent, "Inventory Report", headers, rows)


def export_purchase_pdf(parent, purchases: list[dict]) -> bool:
    headers = ["ID", "Date", "Supplier", "Created By",
               "Expected Date", "Total (PHP)", "Status"]
    rows = [
        [
            r["id"], str(r["created_at"])[:10], r.get("supplier", ""),
            r.get("created_by", ""), str(r.get("expected_date", "")),
            f"{float(r['total_amount']):.2f}", r["status"],
        ]
        for r in purchases
    ]
    return export_pdf(parent, "Purchase Report", headers, rows)


def export_low_stock_pdf(parent, items: list[dict]) -> bool:
    headers = ["Item", "Category", "Current Stock", "Min Stock", "Deficit"]
    rows = [
        [r["name"], r["category"], r["stock_qty"],
         r["min_stock"], r.get("deficit", r["min_stock"] - r["stock_qty"])]
        for r in items
    ]
    return export_pdf(parent, "Low Stock Alert Report", headers, rows)


def export_movement_pdf(parent, movements: list[dict]) -> bool:
    headers = ["ID", "Item", "Movement Type", "Quantity",
               "User", "Department", "Notes", "Date"]
    rows = [
        [
            r["id"], r["item_name"], r["movement_type"],
            r["quantity"], r["user_name"],
            r.get("department", ""), r.get("notes", ""),
            str(r["created_at"])[:16],
        ]
        for r in movements
    ]
    return export_pdf(parent, "Inventory Movement Report", headers, rows)


def export_damage_pdf(parent, damages: list[dict]) -> bool:
    headers = ["ID", "Item", "Category", "Quantity",
               "Reason", "Reported By", "Status", "Date"]
    rows = [
        [
            r["id"], r.get("item_name", ""), r.get("category", ""),
            r["quantity"], r.get("reason", ""),
            r.get("created_by", ""), r["status"],
            str(r["created_at"])[:16],
        ]
        for r in damages
    ]
    return export_pdf(parent, "Damage Report", headers, rows)


def export_dept_consumption_pdf(parent, items: list[dict], department: str) -> bool:
    headers = ["Item Name", "Total Consumed"]
    rows = [[r["item_name"], r["total_used"]] for r in items]
    return export_pdf(parent, f"{department} Consumption Report", headers, rows)