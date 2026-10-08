# Autonomous RFx Normalization & Interrogation Engine

An enterprise B2B SaaS application for strategic procurement teams. Ingests unstructured, multi-format vendor proposals (Excel, PDF, Word, 2-Part Angled Smartphone Photo, USD Email) generated synchronously from a **Master RFI Baseline Specification** (50-500 order volume range, diverse UOMs including Kg, Metre, Piece, Roll, Pack), normalizes rates into standard INR and UOMs, provides line-level visual audit proof, and enables natural language split-award interrogation.

---

## 🌟 Key Features

1. **Autonomous 6-File RFx & 5-Vendor Multi-Format Generator**:
   - **Master RFI Baseline Specification (6th File)**: Generates official enterprise RFI & BOQ (`rfi_baseline_specification.xlsx` & `rfi_procurement_prompt.txt`) establishing baseline item specifications, target quantities (50 - 500 units), standard UOMs (`Piece`, `Kg`, `Metre`, `Roll`, `Pack`), and bidding instructions.
   - **Synchronous Realistic Vendor Bids**: Generates 5 realistic vendor proposals responding to the RFI with realistic market noise:
     - **Vendor 1 (Excel)**: Custom headers, MOQs, BOQ quantity variances, freight terms, and volume tier duplicates.
     - **Vendor 2 (Vector PDF)**: Tabular rate card, BOQ quantities, MOQs, and buried footnote discount clause (*"5% Volume Discount if PO > 1,500 units"*).
     - **Vendor 3 (Word DOCX)**: Embedded table, prose SLA (*"100% quality replacement warranty"*), freight extra (~3%), and unrequested extra accessory line item.
     - **Vendor 4 (Angled Smartphone Photos)**: Physical rate card snapshots generated in **2 distinct parts** (`Part 1: Cartons & Tapes`, `Part 2: Films & Specialty`) with realistic perspective distortion.
     - **Vendor 5 (Raw USD Email)**: International export quote in USD ($) with flat ocean freight ($350) and out-of-stock unquoted lines (27/30 quoted).
   - **Zero-Latency In-Memory Caching & Instant Downloads**: Download any individual file directly or download the complete 6-file dataset as a ZIP bundle (`RFx_and_5_Vendor_Dataset.zip`).
   - **Auto-Archiving**: Automatically archives previous dataset runs into `vendor_dataset/archive/dataset_YYYYMMDD_HHMMSS/` upon generating a fresh set, while keeping datasets strictly out of git.

2. **Multimodal Extraction & Normalization Engine**:
   - Deterministic and vision-powered parsers extract structured line items, MOQs, freight terms, currency conversions, and commercial clauses.
   - Converts foreign currency quotes from USD ($) to INR (₹) at standard conversion rate (₹84.0/USD).

3. **Line-Level Visual Proof & Deal Auditability**:
   - Ground truth inspection drawer displaying exact verbatim snippets, page numbers, row coordinates, AI confidence scores, and raw 2-part rate card photo previews.

4. **Config-Driven Multi-Provider AI Sourcing Copilot**:
   - Pluggable support for **Google Gemini**, **OpenAI**, **OpenRouter**, and **Ollama** (Local).
   - Models are dynamically configured via `.env` options (`GEMINI_MODELS`, `OPENAI_MODELS`, `OPENROUTER_MODELS`, `OLLAMA_MODELS`, `AI_MODEL`) or custom model input strings without hardcoding.
   - Natural language negotiation questions, split-award scenario simulations, and deal savings calculations.

---

## 🚀 Quickstart Guide

### 1. Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Settings & Models
Copy `.env.example` to `.env` and set your preferred provider and API key:
```bash
cp .env.example .env
```

Edit `.env`:
```env
# Provider Selection: 'gemini' | 'openai' | 'openrouter' | 'ollama'
LLM_PROVIDER=gemini
AI_MODEL=gemini-2.5-flash

# Dynamic model lists per provider (comma-separated):
GEMINI_MODELS=gemini-2.5-flash,gemini-2.5-pro,gemini-1.5-pro,gemini-1.5-flash
OPENAI_MODELS=gpt-4o,gpt-4o-mini,o3-mini,gpt-4-turbo
OPENROUTER_MODELS=anthropic/claude-3.5-sonnet,deepseek/deepseek-r1,meta-llama/llama-3.3-70b-instruct
OLLAMA_MODELS=llama3.2,mistral,qwen2.5:7b,deepseek-r1:8b

# API Keys & Endpoints
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
OLLAMA_BASE_URL=http://localhost:11434/v1

# Parameters
USD_INR_RATE=84.0
DATASET_DIR=./vendor_dataset
```

### 3. Launch Web Application (Local Streamlit)
```bash
.venv/bin/streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Deploy to Hostinger
The repository is 100% Hostinger-compatible out of the box:
- **Hostinger Standard Git Deployment**: Hostinger automatically serves [index.html](file:///Users/akshaykumar/code/qgenerator/index.html) (with [index.php](file:///Users/akshaykumar/code/qgenerator/index.php) and [.htaccess](file:///Users/akshaykumar/code/qgenerator/.htaccess) fallbacks) directly at your domain (e.g. `qgenerator.elimenots.xyz`) with zero server configuration and zero 403 errors.

### 5. Run Automated Tests
```bash
.venv/bin/pytest -v
```

---

## ⚙️ Model Provider Reference

| Provider | Config Options in `.env` | Usage |
| :--- | :--- | :--- |
| **Google Gemini** | `GEMINI_MODELS`, `GEMINI_API_KEY` | Set API key and desired model |
| **OpenAI** | `OPENAI_MODELS`, `OPENAI_API_KEY` | Standard OpenAI endpoint or compatible gateway |
| **OpenRouter** | `OPENROUTER_MODELS`, `OPENROUTER_API_KEY` | Multi-model routing (Claude, DeepSeek, Llama) |
| **Ollama (Local)** | `OLLAMA_MODELS`, `OLLAMA_BASE_URL` | Local air-gapped LLM runner (`ollama serve`) |
| **Custom Model** | `AI_MODEL` or UI Free-form String | Any custom or fine-tuned model ID |
| **Offline Mode** | Fallback Deterministic Engine | Runs out-of-the-box with zero API key configuration |

---

## 📁 Repository Structure
```
qgenerator/
├── app.py                     # Main Streamlit SaaS Application
├── src/
│   ├── config/settings.py     # App settings & dynamic multi-provider model loader
│   ├── generator/packaging_generator.py # Master RFI & 5-Vendor Document Generator
│   ├── extractor/
│   │   ├── multimodal_engine.py # Multimodal routing engine
│   │   └── local_parsers.py     # Deterministic parsers with line-level proof
│   ├── analytics/
│   │   ├── matrix_builder.py    # Side-by-side normalizer & deal totals
│   │   └── optimizer.py         # Split-award L1 mathematical solver
│   ├── models/schemas.py        # Pydantic data schemas
│   ├── tools/llm_client.py      # Unified LLM provider client (Gemini/OpenAI/OpenRouter/Ollama)
│   └── ui/
│       ├── styles.py            # Custom CSS & banner styling
│       └── components.py        # File badges, proofs, KPI cards, charts
├── tests/
│   └── test_procurement_engine.py # Complete test suite
├── artifacts/
│   ├── plan_*.md                # Planning & implementation artifacts
│   └── logs/test_run.log        # Test execution logs
└── vendor_dataset/              # Generated RFI & vendor proposals (git-ignored)
```
