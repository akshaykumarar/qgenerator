# Architecture & Technical Design: Autonomous RFx Intelligence Engine

## 1. System Architecture Overview

```mermaid
flowchart TD
    subgraph Data Generation ["Synchronous RFx Specification & 5-Vendor Generator"]
        RFI[6th Master RFI Specification: Excel & Prompt\nVolumes: 50-500 | UOMs: Kg, Metre, Piece, Roll, Pack]
        G[Multi-Format Noise Injector] --> |Auto-Archive Prior Runs| ARC[vendor_dataset/archive/timestamp/]
        G --> |In-Memory Python Cache| MEM[_DATASET_CACHE Bytes]
        RFI --> G
        G --> D1[Vendor 1: Custom Excel .xlsx\nMOQs, BOQ variances, freight notes]
        G --> D2[Vendor 2: Vector PDF .pdf\n5% Volume Footnote, BOQ table]
        G --> D3[Vendor 3: Word .docx\n100% SLA warranty, 3% freight, Extra Item]
        G --> D4[Vendor 4: 2-Part Angled Photos .png\nDual rate cards with homography skew]
        G --> D5[Vendor 5: Raw USD Email .txt\nUSD $ quotes, flat $350 freight, 3 unquoted OOS]
        MEM --> DL[ZIP & Individual File Downloads]
    end

    subgraph Multimodal Extraction ["Multimodal Normalization & Ingestion"]
        D1 --> E1[Excel Parser / Gemini Vision]
        D2 --> E2[PDF Tabular & Footnote Extractor]
        D3 --> E3[Word Prose SLA & Table Extractor]
        D4 --> E4[Homography Unwarp & OCR Vision]
        D5 --> E5[USD FX Normalizer & OOS Flagging]
    end

    subgraph Analytical Core ["Analytics & Split-Award Optimization"]
        E1 & E2 & E3 & E4 & E5 --> M[Normalized Comparison Matrix]
        M --> L1[L1 Lowest Quote Selector]
        M --> F[Footnote & Volume Discount Evaluator]
        M --> OPT[Split-Award Allocation Optimizer]
    end

    subgraph AI Interrogation & UI ["B2B SaaS Experience & Copilot"]
        M & OPT --> UI1[Side-by-Side Matrix UI]
        M & OPT --> UI2[Line-Level Visual Proof Drawer]
        M & OPT --> UI3[Footnote & SLA Intelligence Matrix]
        M & OPT --> COPILOT[Unified Multi-Provider Copilot\n(Gemini / OpenAI / OpenRouter / Ollama)]
    end
```

## 2. Master RFI Specification & Multimodal Bid Standards
1. **Master RFI Baseline Specification (6th File)**: Generates `rfi_baseline_specification.xlsx` & `rfi_procurement_prompt.txt` with target order volumes in the **50 to 500** unit range, standard UOMs (`Kg`, `Metre`, `Piece`, `Roll`, `Pack`), and technical bidding instructions.
2. **Vendor 1 (Excel)**: Normalizes non-standard headers (`Item Ref`, `Packaging Specification`, `Rate per Unit (INR)`), sheet notes (`Excludes 18% GST`), MOQ constraints, and BOQ volume offerings.
3. **Vendor 2 (PDF)**: Tabular parsing + buried footnote discount clause (`5% Volume Discount applied to Total PO Value if order quantity exceeds 1,500 units`).
4. **Vendor 3 (Word)**: Extracts structured items from Word tables + prose commercial clauses (`100% quality replacement warranty`, `Freight extra at ~3%`), plus handles unrequested extra accessory items (`PKG-SUP-01`).
5. **Vendor 4 (2-Part Angled Photos)**: Dual-part smartphone photos (`Part 1` and `Part 2`) with perspective correction via 4-point homography transform matrix + Vision OCR coordinate bounding.
6. **Vendor 5 (Email)**: Converts foreign currency quotes from USD ($) to INR (₹) at standard conversion rate (₹84.0/USD), flags out-of-stock unquoted items, and parses ocean freight clauses ($350).

## 3. Data Model Architecture (Pydantic V2)
- `StandardSKU`: Master catalog packaging item with 50-500 order volume, diverse UOMs, and internal baseline.
- `LineProof`: Line-level ground truth trace (snippet, page/row, confidence score, bounding box, normalization math).
- `VendorLineItem`: Individual quoted line item linked to its audit `LineProof`, with MOQ and lead time attributes.
- `CommercialTerms`: Extracted SLAs, warranties, freight rules, and footnote volume discounts.
- `VendorBidResponse`: Complete parsed vendor proposal with parsing status and extraction latency.
- `RFxComparisonRow`: Matrix row comparing all 5 vendors side-by-side with L1 lowest rate badge and price spread.
- `SplitAwardSummary`: Sourcing optimization recommendation with vendor spend and line allocation distributions.

## 4. Multi-Provider LLM Interrogation Architecture
The system supports pluggable LLM backends via [UnifiedProcurementLLM](file:///Users/akshaykumar/code/qgenerator/src/tools/llm_client.py):
- **Google Gemini**: Dynamic model list loaded from configuration (`GEMINI_MODELS` / `AI_MODEL`).
- **OpenAI**: Dynamic model list loaded from configuration (`OPENAI_MODELS` / `AI_MODEL`).
- **OpenRouter**: Dynamic model list loaded from configuration (`OPENROUTER_MODELS` / `AI_MODEL`).
- **Ollama**: Dynamic model list loaded from configuration (`OLLAMA_MODELS` / `AI_MODEL`) via OpenAI-compatible endpoint.
- **Custom Model String Input**: Supported dynamically without hardcoded enum restrictions.
- **Offline Fallback**: High-speed deterministic rule-based procurement advisor when running without active API credentials.

## 5. Hostinger Web Deployment Architecture
- **Hostinger Standard Git Web Deployment**: Direct root entrypoints ([index.html](file:///Users/akshaykumar/code/qgenerator/index.html), [index.php](file:///Users/akshaykumar/code/qgenerator/index.php), [.htaccess](file:///Users/akshaykumar/code/qgenerator/.htaccess)) deliver a lightweight, responsive client-side interface with an interactive 30-SKU normalization matrix, split-award optimizer with live Chart.js visualizations, line-level proof inspection drawers, and client-side multi-provider AI copilot.
- **Streamlit Local Runtime**: [app.py](file:///Users/akshaykumar/code/qgenerator/app.py) & [.streamlit/config.toml](file:///Users/akshaykumar/code/qgenerator/.streamlit/config.toml) provide local Python execution and interactive visualization.


