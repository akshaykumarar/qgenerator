"""Unified Multimodal Extraction and Normalization Engine."""
import os
import time
from typing import Dict, List, Optional
from src.config.settings import get_settings
from src.models.schemas import VendorBidResponse, StandardSKU
from src.tools.gemini_client import GeminiProcurementClient
from src.generator.packaging_generator import DEFAULT_PACKAGING_SKUS
from src.extractor.local_parsers import (
    parse_vendor1_excel,
    parse_vendor2_pdf,
    parse_vendor3_docx,
    parse_vendor4_photo,
    parse_vendor5_email,
)


class MultimodalExtractionEngine:
    """Orchestrates extraction across Excel, PDF, DOCX, Images, and Emails."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, usd_inr_rate: Optional[float] = None):
        """Initialize extraction engine."""
        settings = get_settings()
        self.usd_inr_rate = usd_inr_rate or settings.usd_inr_rate
        self.gemini_client = GeminiProcurementClient(api_key=api_key, model=model)

    def extract_all_vendors(self, dataset_dir: str = "./vendor_dataset") -> Dict[str, VendorBidResponse]:
        """
        Parse all 5 vendor files in dataset directory into normalized VendorBidResponse structures.
        """
        results: Dict[str, VendorBidResponse] = {}
        
        file_map = {
            "vendor_1": ("vendor1_alpha_pack_custom_excel.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", parse_vendor1_excel),
            "vendor_2": ("vendor2_beta_box_clean_table.pdf", "application/pdf", parse_vendor2_pdf),
            "vendor_3": ("vendor3_gamma_packaging_prose.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", parse_vendor3_docx),
            "vendor_4": ("vendor4_delta_angled_ratecard.png", "image/png", parse_vendor4_photo),
            "vendor_5": ("vendor5_epsilon_global_raw_email.txt", "text/plain", lambda p: parse_vendor5_email(p, usd_inr_rate=self.usd_inr_rate)),
        }

        for vendor_id, (fname, mime_type, local_parser) in file_map.items():
            fpath = os.path.join(dataset_dir, fname)
            t_start = time.time()
            
            if not os.path.exists(fpath):
                continue

            try:
                # 1. High-fidelity parsing with full structural proof
                bid_res = local_parser(fpath)
                bid_res.extraction_time_ms = round((time.time() - t_start) * 1000, 2)
                results[vendor_id] = bid_res
            except Exception as e:
                # Fallback on parsing error
                bid_res = VendorBidResponse(
                    vendor_id=vendor_id,
                    vendor_name=f"Vendor {vendor_id}",
                    source_filename=fname,
                    source_format="Unknown",
                    total_items_quoted=0,
                    parsing_status=f"Error: {str(e)}",
                    extraction_time_ms=round((time.time() - t_start) * 1000, 2)
                )
                results[vendor_id] = bid_res

        return results
