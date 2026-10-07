"""Unit and integration test suite for Autonomous RFx Engine."""
import os
import pytest
from src.config.settings import AppSettings, get_settings
from src.generator.packaging_generator import (
    DEFAULT_PACKAGING_SKUS,
    generate_vendor_dataset,
    apply_user_feedback,
)
from src.extractor.multimodal_engine import MultimodalExtractionEngine
from src.analytics.matrix_builder import ComparisonMatrixBuilder
from src.analytics.optimizer import SplitAwardOptimizer
from src.tools.llm_client import UnifiedProcurementLLM


def test_settings_multi_provider_dynamic():
    """Verify settings support dynamic config options for Gemini, OpenAI, OpenRouter, and Ollama."""
    settings = get_settings()
    gemini_models = settings.get_models_for_provider("gemini")
    openai_models = settings.get_models_for_provider("openai")
    openrouter_models = settings.get_models_for_provider("openrouter")
    ollama_models = settings.get_models_for_provider("ollama")

    assert len(gemini_models) > 0
    assert len(openai_models) > 0
    assert len(openrouter_models) > 0
    assert len(ollama_models) > 0
    assert settings.usd_inr_rate == 84.0


def test_dataset_generation(tmp_path):
    """Verify 5-vendor dataset generation creates all 5 distinct multi-format files."""
    target_dir = str(tmp_path / "vendor_dataset")
    files = generate_vendor_dataset(target_dir=target_dir)
    assert len(files) == 5
    for f in files:
        assert os.path.exists(f)
        assert os.path.getsize(f) > 0


def test_user_feedback_dynamic_pricing():
    """Verify natural language feedback changes SKU base rates."""
    skus_original = DEFAULT_PACKAGING_SKUS
    skus_inflated = apply_user_feedback(skus_original, "15% price increase")
    
    avg_orig = sum(s["base_rate"] for s in skus_original) / len(skus_original)
    avg_inf = sum(s["base_rate"] for s in skus_inflated) / len(skus_inflated)
    assert avg_inf > avg_orig


def test_extraction_and_normalization(tmp_path):
    """Verify parsing and normalization across Excel, PDF, Word, Angled Image, and Email."""
    target_dir = str(tmp_path / "vendor_dataset")
    generate_vendor_dataset(target_dir=target_dir)

    engine = MultimodalExtractionEngine(usd_inr_rate=84.0)
    results = engine.extract_all_vendors(dataset_dir=target_dir)

    assert len(results) == 5
    assert "vendor_1" in results  # Excel
    assert "vendor_2" in results  # PDF
    assert "vendor_3" in results  # Word
    assert "vendor_4" in results  # Image
    assert "vendor_5" in results  # Email

    # Check Vendor 1 (Excel)
    v1 = results["vendor_1"]
    assert v1.total_items_quoted == 30
    assert "PKG-001" in v1.line_items

    # Check Vendor 2 (PDF footnote)
    v2 = results["vendor_2"]
    assert v2.commercial_terms.discount_percentage == 5.0

    # Check Vendor 3 (Word warranty and freight)
    v3 = results["vendor_3"]
    assert "100%" in v3.commercial_terms.warranty
    assert "3%" in v3.commercial_terms.freight_terms

    # Check Vendor 5 (USD Email missing lines)
    v5 = results["vendor_5"]
    assert v5.total_items_quoted == 27  # 3 items out of stock
    # Verify USD to INR normalization
    quoted_item = next(it for it in v5.line_items.values() if it.is_quoted)
    assert quoted_item.raw_currency == "USD"
    assert quoted_item.normalized_rate == round(quoted_item.raw_rate * 84.0, 2)


def test_comparison_matrix_and_optimization(tmp_path):
    """Verify comparison matrix builder and split-award optimization math."""
    target_dir = str(tmp_path / "vendor_dataset")
    generate_vendor_dataset(target_dir=target_dir)

    engine = MultimodalExtractionEngine(usd_inr_rate=84.0)
    vendor_responses = engine.extract_all_vendors(dataset_dir=target_dir)

    matrix = ComparisonMatrixBuilder.build_matrix(vendor_responses, DEFAULT_PACKAGING_SKUS)
    assert len(matrix) == 30

    deal_totals = ComparisonMatrixBuilder.calculate_deal_totals(matrix, vendor_responses)
    assert deal_totals["total_baseline_inr"] > 40000000  # ₹4+ Crore baseline portfolio!
    assert deal_totals["total_optimal_l1_inr"] > 0
    assert deal_totals["total_savings_inr"] > 0

    # Test L1 Optimization
    split_l1 = SplitAwardOptimizer.optimize_l1_split(matrix, vendor_responses)
    assert len(split_l1.allocations) == 30
    assert split_l1.total_deal_value_optimized < split_l1.total_deal_value_baseline
    assert split_l1.total_savings_amount > 0

    # Test 2-Vendor Split
    split_2v = SplitAwardOptimizer.optimize_2vendor_split(matrix, vendor_responses, "vendor_1", "vendor_3")
    assert len(split_2v.allocations) == 30


def test_copilot_interrogation():
    """Verify offline fallback and interrogation logic."""
    client = UnifiedProcurementLLM(provider="gemini", model="gemini-2.5-flash")
    resp = client.interrogate_procurement_matrix("What is the optimal split award?", matrix_context="[]")
    assert resp.answer_markdown
    assert len(resp.suggested_followups) > 0
