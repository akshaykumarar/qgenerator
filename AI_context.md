# AI Context: Autonomous RFx Normalization & Interrogation Engine

## Project Identity & Mission
The Intelligent Procurement Assistant is an enterprise B2B SaaS web application designed for strategic sourcing teams. It ingests unstructured, multi-format vendor bid documents (Excel, PDF, Word, Angled Smartphone Photo, USD Email) for a 30-SKU packaging consumables catalog (~₹4.2 Crore annual portfolio), normalizes rates into INR, reconciles non-standard UOMs, detects buried commercial footnotes, provides line-level visual audit proof, and enables natural language split-award interrogation.

## Key Components & Paths
- **Streamlit Web Application Entry Point**: [app.py](file:///Users/akshaykumar/code/qgenerator/app.py)
- **Configuration & Provider Settings**: [src/config/settings.py](file:///Users/akshaykumar/code/qgenerator/src/config/settings.py)
- **Pydantic Data Models**: [src/models/schemas.py](file:///Users/akshaykumar/code/qgenerator/src/models/schemas.py)
- **Multi-Provider LLM Client** (Gemini, OpenAI, OpenRouter, Ollama): [src/tools/llm_client.py](file:///Users/akshaykumar/code/qgenerator/src/tools/llm_client.py)
- **Packaging Dataset Generator** (5 Formats): [src/generator/packaging_generator.py](file:///Users/akshaykumar/code/qgenerator/src/generator/packaging_generator.py) (Includes in-memory zero-latency cache `_DATASET_CACHE`, auto-archiving to `vendor_dataset/archive/dataset_YYYYMMDD_HHMMSS/`, and single-click ZIP bundle generator `create_dataset_zip`).
- **Git Protection**: `.gitignore` ensures `vendor_dataset/`, `archive/`, `*.zip`, `.env`, and virtual environment artifacts never enter version control.
- **Multimodal Extraction Engine & Local Parsers**: [src/extractor/multimodal_engine.py](file:///Users/akshaykumar/code/qgenerator/src/extractor/multimodal_engine.py), [src/extractor/local_parsers.py](file:///Users/akshaykumar/code/qgenerator/src/extractor/local_parsers.py)
- **Matrix Builder & Split-Award Optimizer**: [src/analytics/matrix_builder.py](file:///Users/akshaykumar/code/qgenerator/src/analytics/matrix_builder.py), [src/analytics/optimizer.py](file:///Users/akshaykumar/code/qgenerator/src/analytics/optimizer.py)
- **UI Design System & Visual Proof Components**: [src/ui/styles.py](file:///Users/akshaykumar/code/qgenerator/src/ui/styles.py), [src/ui/components.py](file:///Users/akshaykumar/code/qgenerator/src/ui/components.py)

## Dynamic Config-Driven Multi-Provider Support
1. **Google Gemini**: Configured dynamically via `GEMINI_MODELS` in `.env` (defaults: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-1.5-pro`)
2. **OpenAI**: Configured dynamically via `OPENAI_MODELS` in `.env` (defaults: `gpt-4o`, `gpt-4o-mini`, `o3-mini`, `gpt-4-turbo`)
3. **OpenRouter**: Configured dynamically via `OPENROUTER_MODELS` in `.env` (defaults: `anthropic/claude-3.5-sonnet`, `deepseek/deepseek-r1`, `meta-llama/llama-3.3-70b-instruct`)
4. **Ollama (Local)**: Configured dynamically via `OLLAMA_MODELS` in `.env` (defaults: `llama3.2`, `mistral`, `qwen2.5:7b`, `deepseek-r1:8b`) via `http://localhost:11434/v1`
5. **Custom Model Input**: Fully supported in both `.env` (`AI_MODEL=any-custom-id`) and UI free-form input mode.

## Testing & Validation
All unit and integration tests are in [tests/test_procurement_engine.py](file:///Users/akshaykumar/code/qgenerator/tests/test_procurement_engine.py), logged in [artifacts/logs/test_run.log](file:///Users/akshaykumar/code/qgenerator/artifacts/logs/test_run.log).
