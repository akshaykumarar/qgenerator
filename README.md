# Autonomous RFx Normalization & Interrogation Engine

An enterprise B2B SaaS application for strategic procurement teams. Ingests unstructured, multi-format vendor proposals (Excel, PDF, Word, Angled Smartphone Photo, USD Email) for packaging consumables (~₹4.2 Crore annual portfolio), normalizes rates into standard INR and UOMs, provides line-level visual audit proof, and enables natural language split-award interrogation.

---

## 🌟 Key Features

1. **Autonomous 5-Vendor Multi-Format Generator**:
   - Generates realistic multi-format bid documents (Excel, Vector PDF, Word DOCX, Perspective-Distorted Phone Photo, and Raw USD Email).
   - Dynamic scenario / feedback prompt input (e.g. *"Increase carton prices by 15%"*, *"Apply 10% discount on tapes"*).
2. **Multimodal Extraction & Normalization Engine**:
   - **Vendor 1 (Excel)**: Non-standard column headers, MOQ, lead times, and GST tax terms.
   - **Vendor 2 (PDF)**: Tabular parsing and buried footnote discount clause (*"5% Volume Discount if PO > 5,000 units"*).
   - **Vendor 3 (Word)**: Embedded table extraction and prose SLA clauses (*"100% quality replacement warranty"*, *"Freight extra at ~3%"*).
   - **Vendor 4 (Angled Photo)**: 4-point homography unwarping and Vision OCR extraction.
   - **Vendor 5 (Email)**: Foreign currency normalization (USD → INR at ₹84.0/USD) and unquoted item detection (*27/30 items quoted*).
3. **Line-Level Visual Proof & Deal Auditability**:
   - Ground truth inspection drawer displaying exact verbatim snippets, page numbers, row coordinates, AI confidence scores, and raw rate card photo preview.
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

### 3. Launch Web Application
```bash
.venv/bin/streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run Automated Tests
```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
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
├── generator.py               # Standalone 5-Vendor Data Generator
├── .env.example               # Environment template with dynamic multi-provider config
├── .env                       # Local environment settings
├── requirements.txt           # Python dependency specifications
├── README.md                  # Project documentation & quickstart
├── architecture.md            # Architecture, Pydantic schemas, & design intent
├── AI_context.md              # AI agent context and decisions log
├── src/
│   ├── config/settings.py     # Pydantic BaseSettings with dynamic config-driven models
│   ├── models/schemas.py      # Pydantic data models for SKUs, Proof, Matrix, Copilot
│   ├── tools/
│   │   ├── gemini_client.py   # Native Google Gemini client
│   │   └── llm_client.py      # Unified Gemini / OpenAI / OpenRouter / Ollama client
│   ├── generator/
│   │   └── packaging_generator.py # 5-format document generator with dynamic feedback
│   ├── extractor/
│   │   ├── local_parsers.py   # Deterministic parsers for Excel, PDF, Docx, Photo, Email
│   │   └── multimodal_engine.py # Unified multimodal extraction pipeline
│   ├── analytics/
│   │   ├── matrix_builder.py  # Normalization matrix & deal totals builder
│   │   └── optimizer.py       # L1 and 2-vendor split-award optimization solvers
│   └── ui/
│       ├── styles.py          # Enterprise B2B Slate theme CSS tokens
│       └── components.py      # KPI cards, visual proof drawers, spend charts
└── tests/
    └── test_procurement_engine.py # Unit and integration test suite
```
