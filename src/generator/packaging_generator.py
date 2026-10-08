"""Packaging SKU Catalog and 6-File Multi-Format Document Generator (RFI + 5 Vendor Proposals).
Features:
- Master RFI specification document generation (Excel & Prompt)
- SKU Catalog with realistic order volumes (50 - 500) and diverse UOMs (Piece, Kg, Metre, Roll, Pack)
- Realistic vendor bid noise: MOQs, BOQ variances, freight costs, duplicate lines, extra items, missing items
- Always at least one vendor quoting in USD (Vendor 5 or mixed)
- 2-Part angled smartphone image generation for physical rate cards
- Dynamic vendor name & rate randomization with feedback-aware mutation
- Auto-archiving of prior runs, in-memory caching, and full ZIP bundle creation
"""
import os
import io
import shutil
import random
import zipfile
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Document generation libraries
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image, ImageDraw, ImageEnhance

# ---------------------------------------------------------------------------
# IN-MEMORY FILE & STATE CACHE FOR ZERO-LATENCY DOWNLOADS & TESTING
# ---------------------------------------------------------------------------
_DATASET_CACHE: Dict[str, bytes] = {}
_LAST_GENERATED_SKUS: Optional[List[Dict[str, Any]]] = None
_LAST_GENERATED_VENDORS: Optional[Dict[str, str]] = None

# ---------------------------------------------------------------------------
# VENDOR NAME POOLS (Realistic B2B Packaging Suppliers)
# ---------------------------------------------------------------------------
VENDOR_POOLS = {
    "vendor_1": [
        "Alpha Pack Solutions Pvt Ltd",
        "Apex Packaging Systems",
        "Zenith Box Works Pvt Ltd",
        "MaxiPack Industrial Supplies",
        "Sterling Corrugated Containers"
    ],
    "vendor_2": [
        "Beta Box & Container Ltd",
        "BlueStar Packaging Ltd",
        "Sigma Corrugators & Box Ltd",
        "Vanguard Packaging Solutions",
        "Beacon Container Works Ltd"
    ],
    "vendor_3": [
        "Gamma Packaging Works",
        "GreenField Packing Corp",
        "Prime Pack Solutions",
        "Pinnacle Paper & Board Works",
        "Titan Packaging & Supplies"
    ],
    "vendor_4": [
        "Delta Print & Pack",
        "Dynamic Label & Pack Co",
        "Falcon Packaging & Print",
        "Orbit Print & Paper Solutions",
        "Matrix Industrial Pack"
    ],
    "vendor_5": [
        "Epsilon Global Packaging Pte Ltd",
        "Evergreen Global Supply Pte",
        "Nexus International Packaging",
        "Pacific Rim Packaging Pte",
        "Venture Global Pack Ltd"
    ],
}

# ---------------------------------------------------------------------------
# DEFAULT PACKAGING SKU CATALOG (30 Items, Order Volumes 50-500, Diverse UOMs)
# ---------------------------------------------------------------------------
DEFAULT_PACKAGING_SKUS: List[Dict[str, Any]] = [
    {"code": "PKG-001", "name": "3-Ply Corrugated Box (10x8x6 in)", "uom": "Piece", "base_rate": 18.50, "category": "Cartons", "annual_volume": 450},
    {"code": "PKG-002", "name": "5-Ply Heavy Duty Master Box (18x14x12 in)", "uom": "Piece", "base_rate": 45.00, "category": "Cartons", "annual_volume": 300},
    {"code": "PKG-003", "name": "7-Ply Industrial Shipping Box (24x20x18 in)", "uom": "Piece", "base_rate": 92.00, "category": "Cartons", "annual_volume": 120},
    {"code": "PKG-004", "name": "Kraft Paper Tape (48mm x 50m)", "uom": "Metre", "base_rate": 1.30, "category": "Tapes", "annual_volume": 500},
    {"code": "PKG-005", "name": "BOPP Clear Packing Tape 48M (48mm x 100m)", "uom": "Roll", "base_rate": 38.00, "category": "Tapes", "annual_volume": 350},
    {"code": "PKG-006", "name": "Cross-Weave Filament Tape (24mm x 50m)", "uom": "Metre", "base_rate": 2.40, "category": "Tapes", "annual_volume": 400},
    {"code": "PKG-007", "name": "LLDPE Hand Stretch Wrap Film (23Mic x 500mm)", "uom": "Kg", "base_rate": 160.00, "category": "Films", "annual_volume": 250},
    {"code": "PKG-008", "name": "Machine Grade Stretch Film (500mm x 1500m)", "uom": "Roll", "base_rate": 1450.00, "category": "Films", "annual_volume": 75},
    {"code": "PKG-009", "name": "Air Bubble Wrap Roll (1m x 100m, 10mm bubble)", "uom": "Metre", "base_rate": 6.80, "category": "Cushioning", "annual_volume": 500},
    {"code": "PKG-010", "name": "Anti-Static Bubble Roll Pink (1m x 50m)", "uom": "Metre", "base_rate": 17.00, "category": "Cushioning", "annual_volume": 300},
    {"code": "PKG-011", "name": "EPE Foam Sheet Roll 2mm (1m x 100m)", "uom": "Metre", "base_rate": 5.40, "category": "Cushioning", "annual_volume": 450},
    {"code": "PKG-012", "name": "Kraft Honeycomb Paper Wrap (500mm x 250m)", "uom": "Roll", "base_rate": 1100.00, "category": "Cushioning", "annual_volume": 80},
    {"code": "PKG-013", "name": "Standard Euro Wooden Pallet (1200x800mm HT)", "uom": "Piece", "base_rate": 850.00, "category": "Pallets", "annual_volume": 150},
    {"code": "PKG-014", "name": "HDPE Plastic Heavy Duty Pallet (1200x1000mm)", "uom": "Piece", "base_rate": 2400.00, "category": "Pallets", "annual_volume": 60},
    {"code": "PKG-015", "name": "PET Strapping Roll 15mm x 0.8mm x 1000m", "uom": "Metre", "base_rate": 1.85, "category": "Strapping", "annual_volume": 500},
    {"code": "PKG-016", "name": "PP Strapping Roll 12mm x 2000m (Yellow)", "uom": "Roll", "base_rate": 950.00, "category": "Strapping", "annual_volume": 100},
    {"code": "PKG-017", "name": "Heavy Duty Steel Strapping 19mm x 25kg", "uom": "Kg", "base_rate": 124.00, "category": "Strapping", "annual_volume": 350},
    {"code": "PKG-018", "name": "Corrugated Edge Protectors (50x50x3x1000mm)", "uom": "Piece", "base_rate": 14.00, "category": "Protectors", "annual_volume": 450},
    {"code": "PKG-019", "name": "Heavy Duty Plastic Corner Guards (Pack 100)", "uom": "Pack", "base_rate": 220.00, "category": "Protectors", "annual_volume": 120},
    {"code": "PKG-020", "name": "LDPE Transparent Poly Bags 200G (12x16 in)", "uom": "Kg", "base_rate": 165.00, "category": "Bags", "annual_volume": 400},
    {"code": "PKG-021", "name": "Zip Lock Reclosable Bags (8x10 in, Pack 500)", "uom": "Pack", "base_rate": 480.00, "category": "Bags", "annual_volume": 90},
    {"code": "PKG-022", "name": "VCI Anti-Rust Poly Envelopes (18x24 in)", "uom": "Piece", "base_rate": 28.00, "category": "Bags", "annual_volume": 250},
    {"code": "PKG-023", "name": "Thermal Barcode Labels 4x6 in (1000/roll)", "uom": "Roll", "base_rate": 290.00, "category": "Labels", "annual_volume": 200},
    {"code": "PKG-024", "name": "Fragile Advisory Stickers (Roll of 500)", "uom": "Roll", "base_rate": 180.00, "category": "Labels", "annual_volume": 150},
    {"code": "PKG-025", "name": "Silica Gel Desiccant Pouches 50g (Pack 100)", "uom": "Kg", "base_rate": 140.00, "category": "Protection", "annual_volume": 300},
    {"code": "PKG-026", "name": "Inflatable Air Cushion Bags (Roll of 1500)", "uom": "Roll", "base_rate": 1600.00, "category": "Cushioning", "annual_volume": 85},
    {"code": "PKG-027", "name": "Corrugated Grid Divider Inserts (12-Cell)", "uom": "Piece", "base_rate": 25.00, "category": "Cartons", "annual_volume": 350},
    {"code": "PKG-028", "name": "Self-Adhesive Packing List Envelopes A5", "uom": "Pack", "base_rate": 210.00, "category": "Labels", "annual_volume": 180},
    {"code": "PKG-029", "name": "Bubble Lined Kraft Mailers #4 (10x15 in)", "uom": "Piece", "base_rate": 16.50, "category": "Bags", "annual_volume": 450},
    {"code": "PKG-030", "name": "Biodegradable Loose Fill Peanuts (10 cu ft)", "uom": "Pack", "base_rate": 780.00, "category": "Cushioning", "annual_volume": 65},
]


def generate_random_base_skus() -> List[Dict[str, Any]]:
    """Generates randomized base pricing and demand volumes (50-500) for the SKU catalog."""
    randomized = []
    for item in DEFAULT_PACKAGING_SKUS:
        sku = dict(item)
        # Randomize base pricing by +/- 10%
        price_factor = random.uniform(0.90, 1.12)
        sku["base_rate"] = round(item["base_rate"] * price_factor, 2)
        # Randomize volume within 50 to 500 bounds
        vol_factor = random.uniform(0.85, 1.15)
        new_vol = int(item["annual_volume"] * vol_factor)
        sku["annual_volume"] = max(50, min(500, new_vol))
        randomized.append(sku)
    return randomized


def pick_random_vendors() -> Dict[str, str]:
    """Randomly selects distinct vendor names from the vendor pool."""
    return {
        "vendor_1": random.choice(VENDOR_POOLS["vendor_1"]),
        "vendor_2": random.choice(VENDOR_POOLS["vendor_2"]),
        "vendor_3": random.choice(VENDOR_POOLS["vendor_3"]),
        "vendor_4": random.choice(VENDOR_POOLS["vendor_4"]),
        "vendor_5": random.choice(VENDOR_POOLS["vendor_5"]),
    }


def apply_user_feedback(skus: List[Dict[str, Any]], feedback_text: str = "") -> List[Dict[str, Any]]:
    """
    Applies incremental modifications to an existing SKU catalog based on natural language feedback.
    """
    modified_skus = [dict(s) for s in skus]
    fb = feedback_text.lower().strip()
    if not fb:
        return modified_skus

    multiplier = 1.0
    if "price increase" in fb or "inflation" in fb or "increase" in fb or "surge" in fb:
        if "10%" in fb:
            multiplier = 1.10
        elif "15%" in fb:
            multiplier = 1.15
        elif "20%" in fb:
            multiplier = 1.20
        elif "25%" in fb:
            multiplier = 1.25
        elif "30%" in fb:
            multiplier = 1.30
        else:
            multiplier = 1.15
    elif "discount" in fb or "cheaper" in fb or "reduce" in fb or "decrease" in fb or "drop" in fb:
        if "10%" in fb:
            multiplier = 0.90
        elif "15%" in fb:
            multiplier = 0.85
        elif "20%" in fb:
            multiplier = 0.80
        elif "25%" in fb:
            multiplier = 0.75
        else:
            multiplier = 0.88

    carton_boost = 1.0
    if "carton" in fb or "box" in fb:
        if "increase" in fb or "higher" in fb or "surge" in fb:
            carton_boost = 1.18
        elif "discount" in fb or "cheaper" in fb:
            carton_boost = 0.82

    tape_boost = 1.0
    if "tape" in fb:
        if "discount" in fb or "cheaper" in fb:
            tape_boost = 0.85
        elif "increase" in fb:
            tape_boost = 1.15

    for s in modified_skus:
        cat_mult = 1.0
        if s.get("category") == "Cartons":
            cat_mult = carton_boost
        elif s.get("category") == "Tapes":
            cat_mult = tape_boost

        s["base_rate"] = round(s["base_rate"] * multiplier * cat_mult, 2)

    return modified_skus


# ---------------------------------------------------------------------------
# 6TH FILE: MASTER RFI SPECIFICATION DOCUMENT (Excel & Prompt Format)
# ---------------------------------------------------------------------------
def generate_rfi_excel(
    skus: List[Dict[str, Any]],
    out_path: str,
    rfx_ref: str = "RFI-PKG-2026-001"
) -> bytes:
    """
    Generates the 6th Master RFI Document: Official Excel Specification & BOQ.
    Contains target BOQ quantities (50-500), standard UOMs (Kg, Metre, Piece, Roll, Pack),
    quality standards, delivery guidelines, and mandatory bidding terms.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RFI Specification & BOQ"

    ws.append(["ENTERPRISE STRATEGIC SOURCING CELL - REQUEST FOR INFORMATION & QUOTATION (RFI/RFQ)"])
    ws.append([f"RFI Reference: {rfx_ref}", "", f"Date of Issue: {datetime.now().strftime('%d-%b-%Y')}", f"Target Validity: 90 Days"])
    ws.append(["Scope: Annual Packaging Consumables Portfolio", "", "Baseline Currency: INR (₹)", "Order Volume Scope: 50 - 500 Units"])
    ws.append([])

    headers = ["BOQ Item #", "SKU Code", "Item Description", "Category", "Target BOQ Quantity", "Standard UOM", "Internal Baseline (INR)", "Target Lead Time (Days)"]
    ws.append(headers)

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0D5C75", end_color="0D5C75", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")

    for col_idx, cell in enumerate(ws[5], start=1):
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 46
    ws.column_dimensions["D"].width = 16
    ws.column_dimensions["E"].width = 20
    ws.column_dimensions["F"].width = 14
    ws.column_dimensions["G"].width = 24
    ws.column_dimensions["H"].width = 22

    thin_border = Border(
        left=Side(style='thin', color='E0E0E0'),
        right=Side(style='thin', color='E0E0E0'),
        top=Side(style='thin', color='E0E0E0'),
        bottom=Side(style='thin', color='E0E0E0')
    )

    for idx, item in enumerate(skus, start=1):
        row_data = [
            f"BOQ-{idx:03d}",
            item["code"],
            item["name"],
            item["category"],
            item["annual_volume"],
            item["uom"],
            f"₹ {item['base_rate']:,.2f}",
            7
        ]
        ws.append(row_data)
        curr_row = ws.max_row
        for col_idx in range(1, 9):
            cell = ws.cell(row=curr_row, column=col_idx)
            cell.border = thin_border
            if col_idx in [5, 7, 8]:
                cell.alignment = right_align

    ws.append([])
    ws.append(["MANDATORY SOURCING & COMMERCIAL INSTRUCTIONS:"])
    inst_font = Font(name="Calibri", size=10, italic=True, color="333333")
    ws.append(["1. Bidders must quote unit prices in INR or USD (with FX rate indicated). All quotes must reference the exact BOQ SKU Code."])
    ws.append(["2. Any Minimum Order Quantity (MOQ) or lot size restrictions must be clearly declared per line item."])
    ws.append(["3. Freight terms (Ex-Works, Freight Included, or Freight Extra %) and replacement warranty SLAs must be specified in the proposal."])
    ws.append(["4. Volume discount thresholds and cash settlement terms should be explicitly noted."])

    for r in range(ws.max_row - 4, ws.max_row + 1):
        ws.cell(row=r, column=1).font = inst_font

    wb.save(out_path)
    buf = io.BytesIO()
    wb.save(buf)
    file_bytes = buf.getvalue()
    _DATASET_CACHE[os.path.basename(out_path)] = file_bytes
    return file_bytes


def generate_rfi_prompt_text(skus: List[Dict[str, Any]], out_path: str, rfx_ref: str = "RFI-PKG-2026-001") -> bytes:
    """Generates the prompt/text version of the RFI for triggering LLM agents or email sourcing."""
    lines = [
        f"=== ENTERPRISE REQUEST FOR INFORMATION (RFI): {rfx_ref} ===",
        f"Date: {datetime.now().strftime('%d-%b-%Y')} | Target Sourcing Portfolio: 30 SKUs",
        "Target Order Quantities: 50 to 500 units per line | Units: Piece, Kg, Metre, Roll, Pack",
        "",
        "Bidding Vendors are requested to provide itemized rates for the following Packaging Consumables:",
        "------------------------------------------------------------------------------------------------"
    ]
    for idx, s in enumerate(skus, start=1):
        lines.append(f"{idx:02d}. [{s['code']}] {s['name']} | Category: {s['category']} | Target Qty: {s['annual_volume']} {s['uom']} | Baseline: ₹{s['base_rate']}")

    lines.extend([
        "------------------------------------------------------------------------------------------------",
        "MANDATORY COMMERCIAL TERMS TO INCLUDE:",
        "- Clear indication of MOQ (Minimum Order Quantity) per line item",
        "- Freight / Shipping Cost (Ex-Works / Delivery Included / % extra)",
        "- Applicable Warranty SLA & Transit Damage Replacement Guarantee",
        "- Volume discounts, payment terms, and currency (INR / USD)"
    ])
    txt_content = "\n".join(lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(txt_content)
    
    file_bytes = txt_content.encode("utf-8")
    _DATASET_CACHE[os.path.basename(out_path)] = file_bytes
    return file_bytes


# ---------------------------------------------------------------------------
# VENDOR 1: EXCEL WITH CUSTOM HEADERS, MOQs, BOQ VARIANCES & GST NOTES
# ---------------------------------------------------------------------------
def generate_vendor1_excel(skus: List[Dict[str, Any]], out_path: str, vendor_name: str = "Alpha Pack Solutions Pvt Ltd") -> bytes:
    """Vendor 1: Custom Excel Layout with custom headers, MOQs, BOQ qty variances, and GST notes."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Commercial Proposal 2026"

    ws.append([f"{vendor_name.upper()} - COMMERCIAL QUOTATION"])
    ws.append(["Ref: APS/RFX-2026/099", "", "", f"Date: {datetime.now().strftime('%B %Y')}"])
    ws.append(["Client: Enterprise Procurement Cell", "", "", "Currency: INR (₹)"])
    ws.append([])

    headers = ["Item Ref", "Packaging Specification", "BOQ Qty Offered", "MOQ", "Rate per Unit (INR)", "Unit", "Lead Time (Days)"]
    ws.append(headers)

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")

    for col_idx, cell in enumerate(ws[5], start=1):
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    ws.column_dimensions["A"].width = 15
    ws.column_dimensions["B"].width = 45
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 22
    ws.column_dimensions["F"].width = 12
    ws.column_dimensions["G"].width = 18

    thin_border = Border(
        left=Side(style='thin', color='E0E0E0'),
        right=Side(style='thin', color='E0E0E0'),
        top=Side(style='thin', color='E0E0E0'),
        bottom=Side(style='thin', color='E0E0E0')
    )

    # Randomly introduce a slight quantity variance on 3 items
    diff_qty_indices = set(random.sample(range(len(skus)), 3))

    for idx, item in enumerate(skus):
        variance = random.uniform(-0.03, 0.02)
        rate = round(item["base_rate"] * (1 + variance), 2)
        moq = random.choice([50, 100, 150, 200])
        offered_qty = item["annual_volume"]
        if idx in diff_qty_indices:
            offered_qty = random.choice([offered_qty + 50, max(50, offered_qty - 50)])

        lead = random.choice([3, 5, 7, 10])
        row_data = [item["code"], item["name"], offered_qty, moq, rate, item["uom"], lead]
        ws.append(row_data)

        curr_row = ws.max_row
        for col_idx in range(1, 8):
            ws.cell(row=curr_row, column=col_idx).border = thin_border

    # Randomly add 1 duplicate SKU with a tiered volume note
    dup_item = skus[0]
    ws.append([dup_item["code"], f"{dup_item['name']} [Tier-2 High Volume Rate]", 500, 500, round(dup_item["base_rate"] * 0.94, 2), dup_item["uom"], 10])

    ws.append([])
    note_row = ws.max_row + 1
    ws.cell(row=note_row, column=1, value="* Note: Rates exclude 18% GST. Delivery terms: Ex-Works Warehouse. Freight extra at actuals. Payment: Net 30 days.").font = Font(italic=True, color="555555")
    
    wb.save(out_path)
    buf = io.BytesIO()
    wb.save(buf)
    file_bytes = buf.getvalue()
    _DATASET_CACHE[os.path.basename(out_path)] = file_bytes
    return file_bytes


# ---------------------------------------------------------------------------
# VENDOR 2: VECTOR PDF WITH BURIED FOOTNOTE DISCOUNT & MOQs
# ---------------------------------------------------------------------------
def generate_vendor2_pdf(skus: List[Dict[str, Any]], out_path: str, vendor_name: str = "Beta Box & Container Ltd") -> bytes:
    """Vendor 2: PDF with Buried Footnote Discount Clause, MOQs, and BOQ Quantities."""
    doc = SimpleDocTemplate(out_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#002B49'), spaceAfter=4)
    meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#4A5568'))
    footnote_style = ParagraphStyle('Footnote', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#C53030'), fontName="Helvetica-Bold")

    story.append(Paragraph(f"<b>{vendor_name.upper()}</b>", title_style))
    story.append(Paragraph(f"Official Quotation # BBC-PR-2026-884 | Date: {datetime.now().strftime('%d-%b-%Y')} | GSTIN: 27AAAAA0000A1Z5", meta_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#002B49'), spaceAfter=8))

    table_data = [["SKU Code", "Item Description", "BOQ Qty", "UOM", "MOQ", "Rate (INR)"]]
    for item in skus:
        variance = random.uniform(-0.02, 0.05)
        rate = round(item["base_rate"] * (1 + variance), 2)
        moq = random.choice([50, 100, 150])
        table_data.append([item["code"], item["name"][:32], str(item["annual_volume"]), item["uom"], str(moq), f"₹ {rate:,.2f}"])

    t = Table(table_data, colWidths=[65, 200, 55, 55, 45, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002B49')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('ALIGN', (2,1), (2,-1), 'RIGHT'),
        ('ALIGN', (4,1), (4,-1), 'CENTER'),
        ('ALIGN', (5,1), (5,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>COMMERCIAL TERMS & FOOTNOTE CONDITIONS:</b>", ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#002B49'))))
    story.append(Spacer(1, 4))
    story.append(Paragraph("1. <b>CRITICAL DISCOUNT CLAUSE:</b> A 5% Volume Discount is applied to the Total PO Value if total order quantity exceeds 1,500 units/kg/metres across items.", footnote_style))
    story.append(Paragraph("2. Payment Terms: Net 45 days. Freight included for full-truckload / consolidated deliveries over ₹50,000.", meta_style))
    story.append(Paragraph("3. Price Validity: 90 days from quote date. Minimum order quantity (MOQ) applies per line.", meta_style))

    doc.build(story)
    with open(out_path, "rb") as f:
        file_bytes = f.read()
    _DATASET_CACHE[os.path.basename(out_path)] = file_bytes
    return file_bytes


# ---------------------------------------------------------------------------
# VENDOR 3: WORD DOC WITH PROSE SLA, FREIGHT & EXTRA ITEMS
# ---------------------------------------------------------------------------
def generate_vendor3_docx(skus: List[Dict[str, Any]], out_path: str, vendor_name: str = "Gamma Packaging Works") -> bytes:
    """Vendor 3: Word Doc with Prose SLA/Warranty, Freight Cost, MOQ, and Extra Accessory Item."""
    doc = Document()
    doc.add_heading(f"{vendor_name} - Commercial Bid Response", level=1)
    doc.add_paragraph("Dear Procurement Committee,\nWe are pleased to submit our itemized rates for annual packaging supplies below.")

    p = doc.add_paragraph()
    p.add_run("Commercial Terms & Service Level Agreement: ").bold = True
    p.add_run("Rates are strictly valid for 60 calendar days. All items include a 100% quality replacement warranty. Freight is chargeable extra at actuals (~3% of PO value). Minimum order release: ₹15,000.")

    table = doc.add_table(rows=1, cols=5)
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text, hdr[4].text = "Part Number", "Description", "BOQ Qty", "Unit", "Rate (₹)"

    for item in skus:
        variance = random.uniform(-0.06, 0.01)
        rate = round(item["base_rate"] * (1 + variance), 2)
        row = table.add_row().cells
        row[0].text, row[1].text, row[2].text, row[3].text, row[4].text = item["code"], item["name"], str(item["annual_volume"]), item["uom"], f"{rate:.2f}"

    # Add 1 unrequested extra item (Vendor noise: extra items)
    extra_row = table.add_row().cells
    extra_row[0].text, extra_row[1].text, extra_row[2].text, extra_row[3].text, extra_row[4].text = "PKG-SUP-01", "Heavy Duty Tape Dispenser Gun (Extra Accessory)", "10", "Piece", "320.00"

    doc.add_paragraph("\nSpecial Conditions:\n- MOQ: 50 units/kg/metres per SKU release.\n- Delivery timeline: 4 business days post PO release.\n- Replacement Guarantee: 100% replacement for transit damages within 48 hours.\n- Freight terms: Extra 3% freight charge applicable for non-metro consignments.")
    doc.save(out_path)

    with open(out_path, "rb") as f:
        file_bytes = f.read()
    _DATASET_CACHE[os.path.basename(out_path)] = file_bytes
    return file_bytes


# ---------------------------------------------------------------------------
# VENDOR 4: ANGLED SMARTPHONE PHOTO (SUPPORTING 2-PART SPLIT IMAGES)
# ---------------------------------------------------------------------------
def _render_angled_card(skus_subset: List[Dict[str, Any]], part_label: str, vendor_name: str) -> Image.Image:
    """Helper to render a single physical card and apply perspective unwarp / rotation."""
    img_w, img_h = 1100, 1150
    base_img = Image.new('RGB', (img_w, img_h), color=(252, 251, 248))
    draw = ImageDraw.Draw(base_img)

    draw.rectangle([(35, 30), (img_w - 35, 115)], fill=(35, 75, 115))
    draw.text((55, 45), f"{vendor_name.upper()} - RATE CARD 2026 [{part_label}]", fill=(255, 255, 255))
    draw.text((55, 80), "Physical Copy - Confidential Enterprise RFx Bid | Volumes 50-500", fill=(210, 230, 250))

    y = 145
    draw.text((55, y), "Code | Item Description | Qty | UOM | Rate (INR) | MOQ", fill=(0, 0, 0))
    draw.line([(55, y + 22), (img_w - 55, y + 22)], fill=(0, 0, 0), width=2)
    y += 30

    for item in skus_subset:
        variance = random.uniform(-0.04, 0.04)
        rate = round(item["base_rate"] * (1 + variance), 2)
        moq = random.choice([50, 100])
        line = f"{item['code']} | {item['name'][:24]:<24} | {item['annual_volume']:<4} | {item['uom']:<6} | Rs. {rate:.2f} | MOQ:{moq}"
        draw.text((55, y), line, fill=(25, 25, 25))
        draw.line([(55, y + 22), (img_w - 55, y + 22)], fill=(225, 225, 225), width=1)
        y += 28
        if y > img_h - 90:
            break

    draw.text((55, y + 18), f"TERMS: Payment 30 Days | Freight Extra 2% | Stamp: [{vendor_name.upper()} VERIFIED]", fill=(90, 90, 90))

    src_pts = [(0, 0), (img_w, 0), (img_w, img_h), (0, img_h)]
    dst_pts = [
        (int(img_w * 0.05), int(img_h * 0.03)),
        (int(img_w * 0.95), int(img_h * 0.02)),
        (int(img_w * 0.97), int(img_h * 0.96)),
        (int(img_w * 0.03), int(img_h * 0.97))
    ]

    def find_perspective_coeffs(pa, pb):
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
        A_mat = np.array(matrix, dtype=float)
        B_mat = np.array(pb).reshape(8, 1)
        res = np.linalg.solve(A_mat, B_mat)
        return res.flatten()

    coeffs = find_perspective_coeffs(dst_pts, src_pts)
    angled_img = base_img.transform((img_w, img_h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    enhancer = ImageEnhance.Color(angled_img)
    return enhancer.enhance(0.92)


def generate_vendor4_angled_photo(
    skus: List[Dict[str, Any]],
    out_path: str,
    vendor_name: str = "Delta Print & Pack",
    generate_two_parts: bool = True
) -> bytes:
    """
    Vendor 4: Angled Smartphone Photo of Printed Physical Rate Card.
    Supports generating in 2 parts (Part 1 and Part 2) when requested, saving both
    and returning the primary/combined asset bytes.
    """
    if generate_two_parts:
        # Split SKUs into 2 parts
        mid = len(skus) // 2
        skus_p1 = skus[:mid]
        skus_p2 = skus[mid:]

        dir_name = os.path.dirname(out_path)
        p1_path = os.path.join(dir_name, "vendor4_delta_angled_ratecard_p1.png")
        p2_path = os.path.join(dir_name, "vendor4_delta_angled_ratecard_p2.png")

        img1 = _render_angled_card(skus_p1, "PART 1: CARTONS & TAPES", vendor_name)
        img2 = _render_angled_card(skus_p2, "PART 2: FILMS & SPECIALTY", vendor_name)

        img1.save(p1_path, "PNG")
        img2.save(p2_path, "PNG")

        # Also save the main out_path (combining or saving part 1)
        img1.save(out_path, "PNG")

        with open(p1_path, "rb") as f1:
            b1 = f1.read()
            _DATASET_CACHE[os.path.basename(p1_path)] = b1
        with open(p2_path, "rb") as f2:
            b2 = f2.read()
            _DATASET_CACHE[os.path.basename(p2_path)] = b2

        _DATASET_CACHE[os.path.basename(out_path)] = b1
        return b1
    else:
        img = _render_angled_card(skus, "FULL CATALOG", vendor_name)
        img.save(out_path, "PNG")
        with open(out_path, "rb") as f:
            file_bytes = f.read()
        _DATASET_CACHE[os.path.basename(out_path)] = file_bytes
        return file_bytes


# ---------------------------------------------------------------------------
# VENDOR 5: RAW EMAIL QUOTED IN USD WITH FREIGHT & OMITTED ITEMS
# ---------------------------------------------------------------------------
def generate_vendor5_email(
    skus: List[Dict[str, Any]],
    out_path: str,
    vendor_name: str = "Epsilon Global Packaging Pte Ltd"
) -> bytes:
    """Vendor 5: Raw Email Quoted in USD with Currency, MOQs, Flat Freight ($350) & Omitted Line Items."""
    USD_INR_RATE = 84.0
    # Randomly select 3 omitted items
    omitted_indices = set(random.sample(range(len(skus)), 3))

    email_lines = [
        f"From: Sales Team <sales@{vendor_name.lower().replace(' ', '').replace('pteltd', '').replace('ltd', '')}.com>",
        "To: Procurement Team <rfq@enterprise.com>",
        f"Subject: RE: Packaging Consumables Bid - {vendor_name} Quote",
        f"Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S')} +0530",
        "",
        "Hi Procurement Team,",
        "Find our export-grade quote below in USD ($) ex-factory Singapore hub for order volumes 50-500.",
        "Freight to India extra flat $350. Minimum order quantity (MOQ) applies per line. Note: 3 items are currently OUT OF STOCK and unquoted.",
        "",
        "--- QUOTE SUMMARY (USD) ---",
    ]

    for idx, item in enumerate(skus):
        if idx in omitted_indices:
            email_lines.append(f"{item['code']} - {item['name']}: OUT OF STOCK / UNABLE TO QUOTE (BOQ Qty: {item['annual_volume']})")
            continue

        variance = random.uniform(-0.08, 0.02)
        rate_inr = item["base_rate"] * (1 + variance)
        rate_usd = round(rate_inr / USD_INR_RATE, 3)
        moq = random.choice([50, 100])
        email_lines.append(f"{item['code']} ({item['name']}) [BOQ: {item['annual_volume']} {item['uom']}]: ${rate_usd} / {item['uom']} (MOQ: {moq})")

    email_lines.extend([
        "",
        "--- COMMERCIAL CONDITIONS ---",
        "Terms: Payment 50% advance, 50% on BL copy. Lead time 12 days.",
        "Freight: International ocean freight to Nhava Sheva / Chennai port flat $350.",
        "Currency: All quotes strictly in United States Dollar (USD).",
        "Best regards,",
        f"Commercial Lead | {vendor_name}"
    ])

    content_str = "\n".join(email_lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content_str)

    file_bytes = content_str.encode("utf-8")
    _DATASET_CACHE[os.path.basename(out_path)] = file_bytes
    return file_bytes


# ---------------------------------------------------------------------------
# ARCHIVING & DATASET BATCH CREATION
# ---------------------------------------------------------------------------
def archive_existing_dataset(target_dir: str) -> Optional[str]:
    """
    Archives any existing vendor bid files and RFI specifications into
    target_dir/archive/dataset_YYYYMMDD_HHMMSS/ before generating a fresh batch.
    """
    if not os.path.exists(target_dir):
        return None

    target_files = [
        "rfi_baseline_specification.xlsx",
        "rfi_procurement_prompt.txt",
        "vendor1_alpha_pack_custom_excel.xlsx",
        "vendor2_beta_box_clean_table.pdf",
        "vendor3_gamma_packaging_prose.docx",
        "vendor4_delta_angled_ratecard.png",
        "vendor4_delta_angled_ratecard_p1.png",
        "vendor4_delta_angled_ratecard_p2.png",
        "vendor5_epsilon_global_raw_email.txt",
    ]

    existing_to_archive = [f for f in target_files if os.path.exists(os.path.join(target_dir, f))]
    if not existing_to_archive:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    archive_dir = os.path.join(target_dir, "archive", f"dataset_{timestamp}")
    os.makedirs(archive_dir, exist_ok=True)

    for fname in existing_to_archive:
        src = os.path.join(target_dir, fname)
        dst = os.path.join(archive_dir, fname)
        try:
            shutil.move(src, dst)
        except Exception:
            pass

    return archive_dir


def generate_vendor_dataset(
    target_dir: str = "./vendor_dataset",
    feedback_prompt: str = "",
    existing_skus: Optional[List[Dict[str, Any]]] = None,
    existing_vendors: Optional[Dict[str, str]] = None
) -> Tuple[List[str], List[Dict[str, Any]], Dict[str, str]]:
    """
    Main trigger function.
    - Generates 6th file: Master RFI Specification document (Excel & Prompt).
    - If feedback_prompt is provided and existing_skus exists: mutates existing dataset incrementally.
    - Otherwise: generates fresh randomized vendor names and SKU data (volumes 50-500, UOMs Kg/Metre/Piece/Roll/Pack).
    - Archives prior files and updates in-memory cache.
    """
    global _LAST_GENERATED_SKUS, _LAST_GENERATED_VENDORS

    # 1. Determine whether to mutate existing data (feedback) or generate completely random data
    fb = feedback_prompt.strip()
    has_prior_data = (existing_skus is not None and len(existing_skus) > 0) or (_LAST_GENERATED_SKUS is not None)

    if fb and has_prior_data:
        # FEEDBACK CASE: Use existing data as base and apply feedback
        base_skus = existing_skus or _LAST_GENERATED_SKUS
        skus = apply_user_feedback(base_skus, fb)
        vendors = existing_vendors or _LAST_GENERATED_VENDORS or pick_random_vendors()
    else:
        # FRESH / RANDOM CASE: Generate random data and random vendor companies
        skus = generate_random_base_skus()
        vendors = pick_random_vendors()

    # 2. Archive existing dataset
    archive_existing_dataset(target_dir)
    os.makedirs(target_dir, exist_ok=True)

    # 3. Generate 6th File: Master RFI Specification (Excel + Prompt Text)
    f_rfi_excel = os.path.join(target_dir, "rfi_baseline_specification.xlsx")
    f_rfi_txt = os.path.join(target_dir, "rfi_procurement_prompt.txt")
    generate_rfi_excel(skus, f_rfi_excel)
    generate_rfi_prompt_text(skus, f_rfi_txt)

    # 4. Generate All 5 Vendor Bid Proposals
    f1 = os.path.join(target_dir, "vendor1_alpha_pack_custom_excel.xlsx")
    f2 = os.path.join(target_dir, "vendor2_beta_box_clean_table.pdf")
    f3 = os.path.join(target_dir, "vendor3_gamma_packaging_prose.docx")
    f4 = os.path.join(target_dir, "vendor4_delta_angled_ratecard.png")
    f5 = os.path.join(target_dir, "vendor5_epsilon_global_raw_email.txt")

    generate_vendor1_excel(skus, f1, vendor_name=vendors["vendor_1"])
    generate_vendor2_pdf(skus, f2, vendor_name=vendors["vendor_2"])
    generate_vendor3_docx(skus, f3, vendor_name=vendors["vendor_3"])
    generate_vendor4_angled_photo(skus, f4, vendor_name=vendors["vendor_4"], generate_two_parts=True)
    generate_vendor5_email(skus, f5, vendor_name=vendors["vendor_5"])

    # Update in-memory state
    _LAST_GENERATED_SKUS = [dict(s) for s in skus]
    _LAST_GENERATED_VENDORS = dict(vendors)

    file_list = [f_rfi_excel, f1, f2, f3, f4, f5]
    return file_list, skus, vendors


def get_cached_file(filename: str, target_dir: str = "./vendor_dataset") -> Optional[bytes]:
    """Retrieve raw bytes of a generated file from in-memory cache or disk."""
    base = os.path.basename(filename)
    if base in _DATASET_CACHE:
        return _DATASET_CACHE[base]
    
    fpath = os.path.join(target_dir, base)
    if os.path.exists(fpath):
        with open(fpath, "rb") as f:
            data = f.read()
            _DATASET_CACHE[base] = data
            return data
    return None


def create_dataset_zip(target_dir: str = "./vendor_dataset") -> bytes:
    """Create an in-memory ZIP archive containing all 6 generated RFI and vendor proposal files."""
    target_files = [
        ("rfi_baseline_specification.xlsx", "rfi_baseline_specification.xlsx"),
        ("rfi_procurement_prompt.txt", "rfi_procurement_prompt.txt"),
        ("vendor1_alpha_pack_custom_excel.xlsx", "vendor1_alpha_pack_custom_excel.xlsx"),
        ("vendor2_beta_box_clean_table.pdf", "vendor2_beta_box_clean_table.pdf"),
        ("vendor3_gamma_packaging_prose.docx", "vendor3_gamma_packaging_prose.docx"),
        ("vendor4_delta_angled_ratecard.png", "vendor4_delta_angled_ratecard.png"),
        ("vendor4_delta_angled_ratecard_p1.png", "vendor4_delta_angled_ratecard_p1.png"),
        ("vendor4_delta_angled_ratecard_p2.png", "vendor4_delta_angled_ratecard_p2.png"),
        ("vendor5_epsilon_global_raw_email.txt", "vendor5_epsilon_global_raw_email.txt"),
    ]

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for disk_name, arcname in target_files:
            file_bytes = get_cached_file(disk_name, target_dir=target_dir)
            if file_bytes:
                zip_file.writestr(arcname, file_bytes)

    return zip_buffer.getvalue()
