"""Packaging SKU Catalog and 5-Vendor Multi-Format Document Generator."""
import os
import random
from typing import List, Dict, Any
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
# DEFAULT PACKAGING SKU CATALOG (30 Items, Real-world Packaging Consumables)
# ---------------------------------------------------------------------------
DEFAULT_PACKAGING_SKUS: List[Dict[str, Any]] = [
    {"code": "PKG-001", "name": "3-Ply Corrugated Box (10x8x6 in)", "uom": "Piece", "base_rate": 18.50, "category": "Cartons", "annual_volume": 120000},
    {"code": "PKG-002", "name": "5-Ply Heavy Duty Master Box (18x14x12 in)", "uom": "Piece", "base_rate": 45.00, "category": "Cartons", "annual_volume": 80000},
    {"code": "PKG-003", "name": "7-Ply Industrial Shipping Box (24x20x18 in)", "uom": "Piece", "base_rate": 92.00, "category": "Cartons", "annual_volume": 35000},
    {"code": "PKG-004", "name": "Kraft Paper Tape (48mm x 50m)", "uom": "Roll", "base_rate": 65.00, "category": "Tapes", "annual_volume": 45000},
    {"code": "PKG-005", "name": "BOPP Clear Packing Tape 48M (48mm x 100m)", "uom": "Roll", "base_rate": 38.00, "category": "Tapes", "annual_volume": 150000},
    {"code": "PKG-006", "name": "Cross-Weave Filament Tape (24mm x 50m)", "uom": "Roll", "base_rate": 120.00, "category": "Tapes", "annual_volume": 20000},
    {"code": "PKG-007", "name": "LLDPE Hand Stretch Wrap Film (23Mic x 500mm)", "uom": "Roll", "base_rate": 320.00, "category": "Films", "annual_volume": 18000},
    {"code": "PKG-008", "name": "Machine Grade Stretch Film (500mm x 1500m)", "uom": "Roll", "base_rate": 1450.00, "category": "Films", "annual_volume": 5000},
    {"code": "PKG-009", "name": "Air Bubble Wrap Roll (1m x 100m, 10mm bubble)", "uom": "Roll", "base_rate": 680.00, "category": "Cushioning", "annual_volume": 12000},
    {"code": "PKG-010", "name": "Anti-Static Bubble Roll Pink (1m x 50m)", "uom": "Roll", "base_rate": 850.00, "category": "Cushioning", "annual_volume": 6000},
    {"code": "PKG-011", "name": "EPE Foam Sheet Roll 2mm (1m x 100m)", "uom": "Roll", "base_rate": 540.00, "category": "Cushioning", "annual_volume": 8500},
    {"code": "PKG-012", "name": "Kraft Honeycomb Paper Wrap (500mm x 250m)", "uom": "Roll", "base_rate": 1100.00, "category": "Cushioning", "annual_volume": 4000},
    {"code": "PKG-013", "name": "Standard Euro Wooden Pallet (1200x800mm HT)", "uom": "Piece", "base_rate": 850.00, "category": "Pallets", "annual_volume": 15000},
    {"code": "PKG-014", "name": "HDPE Plastic Heavy Duty Pallet (1200x1000mm)", "uom": "Piece", "base_rate": 2400.00, "category": "Pallets", "annual_volume": 3000},
    {"code": "PKG-015", "name": "PET Strapping Roll 15mm x 0.8mm x 1000m", "uom": "Roll", "base_rate": 1850.00, "category": "Strapping", "annual_volume": 7500},
    {"code": "PKG-016", "name": "PP Strapping Roll 12mm x 2000m (Yellow)", "uom": "Roll", "base_rate": 950.00, "category": "Strapping", "annual_volume": 12000},
    {"code": "PKG-017", "name": "Heavy Duty Steel Strapping 19mm x 25kg", "uom": "Coil", "base_rate": 3100.00, "category": "Strapping", "annual_volume": 2500},
    {"code": "PKG-018", "name": "Corrugated Edge Protectors (50x50x3x1000mm)", "uom": "Piece", "base_rate": 14.00, "category": "Protectors", "annual_volume": 90000},
    {"code": "PKG-019", "name": "Heavy Duty Plastic Corner Guards (Pack 100)", "uom": "Pack", "base_rate": 220.00, "category": "Protectors", "annual_volume": 10000},
    {"code": "PKG-020", "name": "LDPE Transparent Poly Bags 200G (12x16 in)", "uom": "Kg", "base_rate": 165.00, "category": "Bags", "annual_volume": 25000},
    {"code": "PKG-021", "name": "Zip Lock Reclosable Bags (8x10 in, Pack 500)", "uom": "Pack", "base_rate": 480.00, "category": "Bags", "annual_volume": 8000},
    {"code": "PKG-022", "name": "VCI Anti-Rust Poly Envelopes (18x24 in)", "uom": "Piece", "base_rate": 28.00, "category": "Bags", "annual_volume": 40000},
    {"code": "PKG-023", "name": "Thermal Barcode Labels 4x6 in (1000/roll)", "uom": "Roll", "base_rate": 290.00, "category": "Labels", "annual_volume": 35000},
    {"code": "PKG-024", "name": "Fragile Advisory Stickers (Roll of 500)", "uom": "Roll", "base_rate": 180.00, "category": "Labels", "annual_volume": 20000},
    {"code": "PKG-025", "name": "Silica Gel Desiccant Pouches 50g (Pack 100)", "uom": "Pack", "base_rate": 350.00, "category": "Protection", "annual_volume": 15000},
    {"code": "PKG-026", "name": "Inflatable Air Cushion Bags (Roll of 1500)", "uom": "Roll", "base_rate": 1600.00, "category": "Cushioning", "annual_volume": 6000},
    {"code": "PKG-027", "name": "Corrugated Grid Divider Inserts (12-Cell)", "uom": "Set", "base_rate": 25.00, "category": "Cartons", "annual_volume": 60000},
    {"code": "PKG-028", "name": "Self-Adhesive Packing List Envelopes A5", "uom": "Pack", "base_rate": 210.00, "category": "Labels", "annual_volume": 18000},
    {"code": "PKG-029", "name": "Bubble Lined Kraft Mailers #4 (10x15 in)", "uom": "Piece", "base_rate": 16.50, "category": "Bags", "annual_volume": 85000},
    {"code": "PKG-030", "name": "Biodegradable Loose Fill Peanuts (10 cu ft)", "uom": "Bag", "base_rate": 780.00, "category": "Cushioning", "annual_volume": 4500},
]


def apply_user_feedback(skus: List[Dict[str, Any]], feedback_text: str = "") -> List[Dict[str, Any]]:
    """
    Parses optional feedback text to dynamically adjust SKU prices, currencies,
    or additional metadata before generating documents.
    """
    modified_skus = [dict(s) for s in skus]
    fb = feedback_text.lower().strip()

    # Dynamic multiplier based on natural language feedback
    multiplier = 1.0
    if "price increase" in fb or "inflation" in fb or "increase" in fb:
        # Extract percentage if present e.g. "15%"
        if "10%" in fb:
            multiplier = 1.10
        elif "15%" in fb:
            multiplier = 1.15
        elif "20%" in fb:
            multiplier = 1.20
        elif "25%" in fb:
            multiplier = 1.25
        else:
            multiplier = 1.15
    elif "discount" in fb or "cheaper" in fb or "reduce" in fb or "decrease" in fb:
        if "10%" in fb:
            multiplier = 0.90
        elif "15%" in fb:
            multiplier = 0.85
        elif "20%" in fb:
            multiplier = 0.80
        else:
            multiplier = 0.88

    carton_boost = 1.0
    if "carton" in fb and ("increase" in fb or "higher" in fb):
        carton_boost = 1.18

    for s in modified_skus:
        noise = random.uniform(-0.04, 0.04)
        cat_mult = carton_boost if s.get("category") == "Cartons" else 1.0
        s["base_rate"] = round(s["base_rate"] * (1 + noise) * multiplier * cat_mult, 2)

    return modified_skus


def generate_vendor1_excel(skus: List[Dict[str, Any]], out_path: str) -> None:
    """Vendor 1: Alpha Pack Solutions - Custom Excel Layout with custom headers & GST notes."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Commercial Proposal 2026"

    ws.append(["ALPHA PACK SOLUTIONS PVT LTD - QUOTATION"])
    ws.append(["Ref: APS/RFX-2026/099", "", "", "Date: October 2026"])
    ws.append(["Client: Enterprise Procurement Cell", "", "", "Currency: INR (₹)"])
    ws.append([])  # Blank row

    headers = ["Item Ref", "Packaging Specification", "MOQ", "Rate per Unit (INR)", "Unit", "Lead Time (Days)"]
    ws.append(headers)

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")

    for col_idx, cell in enumerate(ws[5], start=1):
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    # Column widths
    ws.column_dimensions["A"].width = 15
    ws.column_dimensions["B"].width = 45
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 22
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = 18

    thin_border = Border(
        left=Side(style='thin', color='E0E0E0'),
        right=Side(style='thin', color='E0E0E0'),
        top=Side(style='thin', color='E0E0E0'),
        bottom=Side(style='thin', color='E0E0E0')
    )

    for item in skus:
        # Alpha pack gives slight discount on Cartons and higher on Films
        variance = random.uniform(-0.03, 0.02)
        rate = round(item["base_rate"] * (1 + variance), 2)
        moq = random.choice([100, 500, 1000, 50])
        lead = random.choice([3, 5, 7, 10])
        row_data = [item["code"], item["name"], moq, rate, item["uom"], lead]
        ws.append(row_data)

        curr_row = ws.max_row
        for col_idx in range(1, 7):
            ws.cell(row=curr_row, column=col_idx).border = thin_border

    ws.append([])
    note_row = ws.max_row + 1
    ws.cell(row=note_row, column=1, value="* Note: Rates exclude 18% GST. Delivery terms: Ex-Works Warehouse. Payment: Net 30 days.").font = Font(italic=True, color="555555")
    wb.save(out_path)


def generate_vendor2_pdf(skus: List[Dict[str, Any]], out_path: str) -> None:
    """Vendor 2: Beta Box & Container Ltd - PDF with Buried Footnote Discount Clause."""
    doc = SimpleDocTemplate(out_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#002B49'), spaceAfter=4)
    meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#4A5568'))
    footnote_style = ParagraphStyle('Footnote', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#C53030'), fontName="Helvetica-Bold")

    story.append(Paragraph("<b>BETA BOX & CONTAINER LTD.</b>", title_style))
    story.append(Paragraph("Official Quotation # BBC-PR-2026-884 | Date: 05-Oct-2026 | GSTIN: 27AAAAA0000A1Z5", meta_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#002B49'), spaceAfter=8))

    table_data = [["SKU Code", "Item Description", "Category", "UOM", "Rate (INR)"]]
    for item in skus:
        variance = random.uniform(-0.02, 0.05)
        rate = round(item["base_rate"] * (1 + variance), 2)
        table_data.append([item["code"], item["name"][:36], item["category"], item["uom"], f"₹ {rate:,.2f}"])

    t = Table(table_data, colWidths=[65, 230, 80, 65, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002B49')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('ALIGN', (4,1), (4,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>COMMERCIAL TERMS & FOOTNOTE CONDITIONS:</b>", ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#002B49'))))
    story.append(Spacer(1, 4))
    story.append(Paragraph("1. <b>CRITICAL DISCOUNT CLAUSE:</b> A 5% Volume Discount is applied to the Total PO Value if total order quantity exceeds 5,000 units across items.", footnote_style))
    story.append(Paragraph("2. Payment Terms: Net 45 days. Freight included for all full-truckload deliveries.", meta_style))
    story.append(Paragraph("3. Price Validity: 90 days from quote date.", meta_style))

    doc.build(story)


def generate_vendor3_docx(skus: List[Dict[str, Any]], out_path: str) -> None:
    """Vendor 3: Gamma Packaging Works - Word Doc with Embedded Table & Prose Warranty/Freight."""
    doc = Document()
    doc.add_heading("Gamma Packaging Works - Commercial Bid Response", level=1)

    doc.add_paragraph("Dear Procurement Committee,\nWe are pleased to submit our itemized rates for annual packaging supplies below.")

    p = doc.add_paragraph()
    p.add_run("Commercial Terms & Service Level Agreement: ").bold = True
    p.add_run("Rates are strictly valid for 60 calendar days. All items include a 100% quality replacement warranty. Freight is chargeable extra at actuals (~3% of PO value).")

    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = "Part Number", "Description", "Unit", "Rate (₹)"

    for item in skus:
        variance = random.uniform(-0.06, 0.01)  # Gamma is often aggressive on rates
        rate = round(item["base_rate"] * (1 + variance), 2)
        row = table.add_row().cells
        row[0].text, row[1].text, row[2].text, row[3].text = item["code"], item["name"], item["uom"], f"{rate:.2f}"

    doc.add_paragraph("\nSpecial Conditions:\n- Minimum order value per release: ₹25,000.\n- Delivery timeline: 4 business days post PO release.\n- Replacement Guarantee: 100% replacement for transit damages within 48 hours.")
    doc.save(out_path)


def generate_vendor4_angled_photo(skus: List[Dict[str, Any]], out_path: str) -> None:
    """Vendor 4: Delta Print & Pack - Angled Smartphone Photo of Printed Physical Rate Card."""
    img_w, img_h = 1100, 1450
    base_img = Image.new('RGB', (img_w, img_h), color=(252, 251, 248))
    draw = ImageDraw.Draw(base_img)

    # Header Box
    draw.rectangle([(35, 30), (img_w - 35, 115)], fill=(35, 75, 115))
    draw.text((55, 45), "DELTA PRINT & PACK - PRINTED RATE CARD 2026", fill=(255, 255, 255))
    draw.text((55, 80), "Physical Copy - Confidential Enterprise RFx Bid", fill=(210, 230, 250))

    y = 145
    draw.text((55, y), "Code | Item Description | UOM | Rate (INR)", fill=(0, 0, 0))
    draw.line([(55, y + 22), (img_w - 55, y + 22)], fill=(0, 0, 0), width=2)
    y += 30

    for item in skus:
        variance = random.uniform(-0.04, 0.04)
        rate = round(item["base_rate"] * (1 + variance), 2)
        line = f"{item['code']} | {item['name'][:28]:<28} | {item['uom']:<6} | Rs. {rate:.2f}"
        draw.text((55, y), line, fill=(25, 25, 25))
        draw.line([(55, y + 22), (img_w - 55, y + 22)], fill=(225, 225, 225), width=1)
        y += 28
        if y > img_h - 100:
            break

    draw.text((55, y + 18), "TERMS: Payment 30 Days | Freight Extra 2% | Stamp: [DELTA PRINT & PACK VERIFIED]", fill=(90, 90, 90))

    # Perspective Transformation simulating angled smartphone snap
    src_pts = [(0, 0), (img_w, 0), (img_w, img_h), (0, img_h)]
    dst_pts = [
        (int(img_w * 0.06), int(img_h * 0.03)),
        (int(img_w * 0.94), int(img_h * 0.02)),
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
    angled_img = enhancer.enhance(0.92)
    angled_img.save(out_path, "PNG")


def generate_vendor5_email(skus: List[Dict[str, Any]], out_path: str) -> None:
    """Vendor 5: Epsilon Global - Raw Email Quoted in USD with Currency & Omitted Line Items."""
    USD_INR_RATE = 84.0
    # Omit 3 items to test missing line item handling (27/30 lines quoted)
    omitted_indices = {2, 13, 29}

    email_lines = [
        "From: David Miller <david.m@epsilonglobalpack.com>",
        "To: Procurement Team <rfq@enterprise.com>",
        "Subject: RE: Packaging Consumables Bid - Epsilon Quote (Singapore Hub)",
        "Date: Tue, 06 Oct 2026 14:22:10 +0530",
        "",
        "Hi Procurement Team,",
        "Find our export-grade quote below in USD ($) ex-factory Singapore hub.",
        "Freight to India extra flat $350. Note: 3 items are currently OUT OF STOCK and unquoted.",
        "",
        "--- QUOTE SUMMARY (USD) ---",
    ]

    for idx, item in enumerate(skus):
        if idx in omitted_indices:
            email_lines.append(f"{item['code']} - {item['name']}: OUT OF STOCK / UNABLE TO QUOTE")
            continue

        variance = random.uniform(-0.08, 0.02)
        rate_inr = item["base_rate"] * (1 + variance)
        rate_usd = round(rate_inr / USD_INR_RATE, 3)
        email_lines.append(f"{item['code']} ({item['name']}): ${rate_usd} / {item['uom']}")

    email_lines.extend([
        "",
        "--- COMMERCIAL CONDITIONS ---",
        "Terms: Payment 50% advance, 50% on BL copy. Lead time 12 days.",
        "Currency: All quotes strictly in United States Dollar (USD).",
        "Best regards,",
        "David Miller | Commercial Lead",
        "Epsilon Global Packaging Pte Ltd"
    ])

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(email_lines))


def generate_vendor_dataset(target_dir: str = "./vendor_dataset", feedback_prompt: str = "") -> List[str]:
    """
    Main trigger function to generate fresh multi-format bid data for all 5 vendors.
    """
    os.makedirs(target_dir, exist_ok=True)
    skus = apply_user_feedback(DEFAULT_PACKAGING_SKUS, feedback_prompt)

    f1 = os.path.join(target_dir, "vendor1_alpha_pack_custom_excel.xlsx")
    f2 = os.path.join(target_dir, "vendor2_beta_box_clean_table.pdf")
    f3 = os.path.join(target_dir, "vendor3_gamma_packaging_prose.docx")
    f4 = os.path.join(target_dir, "vendor4_delta_angled_ratecard.png")
    f5 = os.path.join(target_dir, "vendor5_epsilon_global_raw_email.txt")

    generate_vendor1_excel(skus, f1)
    generate_vendor2_pdf(skus, f2)
    generate_vendor3_docx(skus, f3)
    generate_vendor4_angled_photo(skus, f4)
    generate_vendor5_email(skus, f5)

    return [f1, f2, f3, f4, f5]
