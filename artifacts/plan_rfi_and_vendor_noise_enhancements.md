# Implementation Plan: RFI Generator & Realistic Multi-Format Vendor Bid Noise

## Task Overview
Enhance the Autonomous RFx Generation & Ingestion Engine to generate a dedicated 6th file (RFI specification Excel/prompt document), align order volumes to 50-500 units with diverse UOMs (Kg, Metre, Piece, Roll, Pack), inject realistic market noise across vendor responses (MOQ, BOQ quantity variances, freight costs, duplicates, ambiguities, extra items, missing items, USD pricing on at least one vendor), and support 2-part image generation for physical photo rate cards.

---

## 1. Requirements & Scope Analysis

### 1.1 RFI Document (6th File)
- Create `rfi_baseline_specification.xlsx` (and accompanying prompt/summary) containing:
  - Scope of work, BOQ lines, required specifications, target quantities (50-500), standard UOMs (`Kg`, `Metre`, `Piece`, `Roll`, `Pack`), target delivery timelines, and standard commercial terms.
  - Acts as the synchronous master requirement document against which vendors quote.

### 1.2 Catalog Quantities & Units of Measure (UOM)
- Adjust catalog order volumes: range **50 to 500** units/pieces/kg/metres.
- UOM diversity: include `Kg` (e.g. poly bags, strapping coils, desiccant), `Metre` (e.g. filament tape, kraft tape, stretch film roll lengths), `Piece` (e.g. corrugated boxes, edge protectors, pallets), `Roll`, `Pack`, `Set`.

### 1.3 Vendor Noise, Imperfections & Realistic Asynchrony
- **Vendor 1 (Excel)**:
  - Custom sheet layout, MOQ constraints, BOQ quantity adjustments for select lines, freight term clauses (Ex-Works / Freight extra), occasional duplicate or variant row.
- **Vendor 2 (PDF)**:
  - Tabular vector layout, 5% volume discount footnote clause, freight included above threshold, MOQ values, minor description ambiguities.
- **Vendor 3 (Word)**:
  - Prose warranty SLA (100% replacement), freight cost clause (~3% of PO value), MOQ and minimum release orders (₹25,000), extra ancillary accessory item (e.g. tape dispenser or corner protector clips).
- **Vendor 4 (Angled Photo Rate Card)**:
  - Multi-part photo generation option (Part 1 and Part 2 images: `vendor4_delta_angled_ratecard_p1.png`, `vendor4_delta_angled_ratecard_p2.png`), splitting items across 2 smartphone rate card snaps.
- **Vendor 5 (Email)**:
  - Quoted in USD ($), converted to INR at configurable exchange rate (₹84.0/USD), omitted / out-of-stock items (2-4 items unquoted), flat freight charge ($350).

### 1.4 System & UI Integration
- In-memory cache `_DATASET_CACHE` and ZIP archive `create_dataset_zip` updated to include all 6 generated files (RFI specification + 5 vendor quotes / multi-part images).
- Streamlit UI file badge grid updated to display the RFI document alongside the 5 vendor proposals.
- Deterministic and multimodal parsers updated to support 2-part image sets, extra items, and UOM consistency.
- Update tests in `tests/test_procurement_engine.py` and log results in `artifacts/logs/test_run.log`.
- Update `README.md`, `architecture.md`, and `AI_context.md`.

---

## 2. Technical Architecture & Phased Execution

### Phase 1: Catalog & SKU Schema Updates
- Update `DEFAULT_PACKAGING_SKUS` in `src/generator/packaging_generator.py` to use order volumes between 50 and 500, with UOMs including `Piece`, `Kg`, `Metre`, `Roll`, `Pack`, `Set`.
- Ensure base pricing and volume randomizers reflect 50-500 scale.

### Phase 2: RFI Specification Document Generation
- Implement `generate_rfi_excel(skus, out_path, ...)` in `src/generator/packaging_generator.py`.
- Generates formatted Excel workbook `rfi_baseline_specification.xlsx` with standard styling, BOQ line numbers, requested quantities, technical specifications, and delivery guidelines.

### Phase 3: Vendor Bid Generators Enhancement
- Update Vendor 1 (Excel): add MOQ, BOQ variance, freight notes, occasional duplicate/extra item.
- Update Vendor 2 (PDF): embed freight, MOQ, BOQ volume columns.
- Update Vendor 3 (Word): add extra item, MOQ conditions, freight charges.
- Update Vendor 4 (Angled Photos): implement 2-part rate card generator (`p1` and `p2`), rendering distinct SKU subsets onto separate angled photo snapshots.
- Update Vendor 5 (Email): ensure USD quotes with freight and omitted lines.
- Update `generate_vendor_dataset()` and `create_dataset_zip()` to package all 6 files.

### Phase 4: Local Parsers & Extraction Engine
- Update `src/extractor/local_parsers.py` to seamlessly parse 2-part images for Vendor 4, extract BOQ quantities and MOQs, and handle extra or duplicate items without crashing.

### Phase 5: UI & Component Updates
- Update `src/ui/components.py` and `app.py` to render the 6-file badge grid (RFI + 5 Vendors) and updated deal metrics.

### Phase 6: Testing, Test Logs & Documentation Updates
- Run pytest suite, outputting logs to `artifacts/logs/test_run.log`.
- Update `README.md`, `architecture.md`, and `AI_context.md`.
