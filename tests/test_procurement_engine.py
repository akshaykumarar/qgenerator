"""Unit and integration test suite for Autonomous RFx Engine with RFI Specification & Vendor Noise."""
import os
import io
import zipfile
import pytest
from src.config.settings import AppSettings, get_settings
from src.generator.packaging_generator import (
    DEFAULT_PACKAGING_SKUS,
    generate_vendor_dataset,
    apply_user_feedback,
    get_cached_file,
    create_dataset_zip,
    archive_existing_dataset,
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


def test_sku_catalog_order_volumes_and_uoms():
    """Verify catalog order volumes are constrained to 50-500 pieces/kg/metres and diverse UOMs exist."""
    for sku in DEFAULT_PACKAGING_SKUS:
        assert 50 <= sku["annual_volume"] <= 500, f"SKU {sku['code']} volume {sku['annual_volume']} outside 50-500 range"
        assert sku["uom"] in ["Piece", "Kg", "Metre", "Roll", "Pack", "Set"], f"Unexpected UOM {sku['uom']}"

    uom_set = {s["uom"] for s in DEFAULT_PACKAGING_SKUS}
    assert "Piece" in uom_set
    assert "Kg" in uom_set
    assert "Metre" in uom_set


def test_dataset_generation_caching_and_archiving(tmp_path):
    """Verify 6-file dataset generation creates RFI + 5 vendor proposals, caches bytes, and archives old sets."""
    target_dir = str(tmp_path / "vendor_dataset")
    
    # 1. First run generates fresh random files & vendor names
    files1, skus1, vendors1 = generate_vendor_dataset(target_dir=target_dir)
    assert len(files1) == 6
    assert len(vendors1) == 5
    for f in files1:
        assert os.path.exists(f)
        assert os.path.getsize(f) > 0

    # Test RFI specification file
    rfi_excel_bytes = get_cached_file("rfi_baseline_specification.xlsx", target_dir=target_dir)
    assert rfi_excel_bytes is not None and len(rfi_excel_bytes) > 0

    # Test in-memory cache retrieval for vendor excel
    excel_bytes = get_cached_file("vendor1_alpha_pack_custom_excel.xlsx", target_dir=target_dir)
    assert excel_bytes is not None and len(excel_bytes) > 0

    # Test 2-part photo files in cache
    p1_bytes = get_cached_file("vendor4_delta_angled_ratecard_p1.png", target_dir=target_dir)
    p2_bytes = get_cached_file("vendor4_delta_angled_ratecard_p2.png", target_dir=target_dir)
    assert p1_bytes is not None and len(p1_bytes) > 0
    assert p2_bytes is not None and len(p2_bytes) > 0

    # Test ZIP bundle creation (Download All)
    zip_bytes = create_dataset_zip(target_dir=target_dir)
    assert zip_bytes is not None and len(zip_bytes) > 0
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names = z.namelist()
        assert any(n == "rfi_baseline_specification.xlsx" for n in names)
        assert any(n.endswith(".xlsx") for n in names)
        assert any(n.endswith(".pdf") for n in names)
        assert any(n.endswith(".docx") for n in names)
        assert any(n.endswith(".png") for n in names)
        assert any(n.endswith(".txt") for n in names)

    # 2. Second run moves old files to archive
    files2, skus2, vendors2 = generate_vendor_dataset(target_dir=target_dir)
    assert len(files2) == 6
    archive_dir = os.path.join(target_dir, "archive")
    assert os.path.exists(archive_dir)
    archived_runs = os.listdir(archive_dir)
    assert len(archived_runs) >= 1


def test_feedback_vs_random_generation(tmp_path):
    """Verify that feedback mutates existing data, while fresh runs randomize."""
    target_dir = str(tmp_path / "vendor_dataset")
    
    # Run 1: Fresh random run
    _, initial_skus, initial_vendors = generate_vendor_dataset(target_dir=target_dir)
    box_rate_orig = next(s["base_rate"] for s in initial_skus if s["code"] == "PKG-001")

    # Run 2: Feedback run on existing data
    _, feedback_skus, feedback_vendors = generate_vendor_dataset(
        target_dir=target_dir,
        feedback_prompt="15% price increase on cartons",
        existing_skus=initial_skus,
        existing_vendors=initial_vendors
    )
    box_rate_feedback = next(s["base_rate"] for s in feedback_skus if s["code"] == "PKG-001")
    
    # Feedback should have increased box rate over the existing box rate
    assert box_rate_feedback > box_rate_orig
    # Vendor names should be preserved during feedback on existing data
    assert feedback_vendors == initial_vendors

    # Run 3: Fresh run without feedback (should generate random new vendors)
    _, fresh_skus, fresh_vendors = generate_vendor_dataset(target_dir=target_dir)
    assert len(fresh_skus) == 30
    assert len(fresh_vendors) == 5


def test_extraction_and_normalization(tmp_path):
    """Verify parsing and normalization across Excel, PDF, Word, Angled Image, and Email."""
    target_dir = str(tmp_path / "vendor_dataset")
    generate_vendor_dataset(target_dir=target_dir)

    engine = MultimodalExtractionEngine(usd_inr_rate=84.0)
    results = engine.extract_all_vendors(dataset_dir=target_dir)

    assert len(results) == 5
    assert "vendor_1" in results
    assert "vendor_2" in results
    assert "vendor_3" in results
    assert "vendor_4" in results
    assert "vendor_5" in results

    # Check Vendor 1 (Excel)
    v1 = results["vendor_1"]
    assert v1.total_items_quoted >= 30
    assert "PKG-001" in v1.line_items
    assert "Freight" in v1.commercial_terms.freight_terms

    # Check Vendor 2 (PDF footnote)
    v2 = results["vendor_2"]
    assert v2.commercial_terms.discount_percentage == 5.0

    # Check Vendor 3 (Word warranty and freight)
    v3 = results["vendor_3"]
    assert "100%" in v3.commercial_terms.warranty
    assert "3%" in v3.commercial_terms.freight_terms

    # Check Vendor 4 (Angled photo multi-part)
    v4 = results["vendor_4"]
    assert v4.total_items_quoted == 30

    # Check Vendor 5 (USD Email missing lines & freight)
    v5 = results["vendor_5"]
    assert v5.total_items_quoted == 27
    assert "350" in v5.commercial_terms.freight_terms
    quoted_item = next(it for it in v5.line_items.values() if it.is_quoted)
    assert quoted_item.raw_currency == "USD"
    assert quoted_item.normalized_rate == round(quoted_item.raw_rate * 84.0, 2)


def test_comparison_matrix_and_optimization(tmp_path):
    """Verify comparison matrix builder and split-award optimization math."""
    target_dir = str(tmp_path / "vendor_dataset")
    _, skus, _ = generate_vendor_dataset(target_dir=target_dir)

    engine = MultimodalExtractionEngine(usd_inr_rate=84.0)
    vendor_responses = engine.extract_all_vendors(dataset_dir=target_dir)

    matrix = ComparisonMatrixBuilder.build_matrix(vendor_responses, skus)
    assert len(matrix) == 30

    deal_totals = ComparisonMatrixBuilder.calculate_deal_totals(matrix, vendor_responses)
    assert deal_totals["total_baseline_inr"] > 0
    assert deal_totals["total_optimal_l1_inr"] > 0
    assert deal_totals["total_savings_inr"] > 0

    # Test L1 Optimization
    split_l1 = SplitAwardOptimizer.optimize_l1_split(matrix, vendor_responses)
    assert len(split_l1.allocations) == 30
    assert split_l1.total_deal_value_optimized < split_l1.total_deal_value_baseline
    assert split_l1.total_savings_amount > 0


def test_copilot_interrogation():
    """Verify offline fallback and interrogation logic."""
    client = UnifiedProcurementLLM(provider="gemini", model="gemini-2.5-flash")
    resp = client.interrogate_procurement_matrix("What is the optimal split award?", matrix_context="[]")
    assert resp.answer_markdown
    assert len(resp.suggested_followups) > 0
