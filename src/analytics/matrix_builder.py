"""Side-by-side comparison matrix builder and deal audit analytics."""
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from src.models.schemas import (
    RFxComparisonRow,
    VendorBidResponse,
    VendorLineItem,
)
from src.generator.packaging_generator import DEFAULT_PACKAGING_SKUS


class ComparisonMatrixBuilder:
    """Builds unified side-by-side matrices and deal metrics."""

    @staticmethod
    def build_matrix(
        vendor_responses: Dict[str, VendorBidResponse],
        skus: Optional[List[Dict[str, Any]]] = None
    ) -> List[RFxComparisonRow]:
        """
        Construct SKU-by-SKU normalized comparison rows.
        """
        sku_catalog = skus or DEFAULT_PACKAGING_SKUS
        rows: List[RFxComparisonRow] = []

        for item in sku_catalog:
            code = item["code"]
            name = item["name"]
            cat = item["category"]
            uom = item["uom"]
            base_rate = item["base_rate"]
            vol = item.get("annual_volume", 10000)

            vendor_rates: Dict[str, Optional[float]] = {}
            valid_rates: List[Tuple[str, float]] = []

            for v_id, v_resp in vendor_responses.items():
                line_item = v_resp.line_items.get(code)
                if line_item and line_item.is_quoted and line_item.normalized_rate > 0:
                    vendor_rates[v_id] = line_item.normalized_rate
                    valid_rates.append((v_id, line_item.normalized_rate))
                else:
                    vendor_rates[v_id] = None

            if valid_rates:
                # Sort to find L1 lowest rate
                valid_rates.sort(key=lambda x: x[1])
                best_vid, lowest_r = valid_rates[0]
                highest_r = max(r for _, r in valid_rates)
                delta_pct = round(((lowest_r - base_rate) / base_rate) * 100, 2)
                spread_pct = round(((highest_r - lowest_r) / lowest_r) * 100, 2) if lowest_r > 0 else 0.0
                best_vname = vendor_responses[best_vid].vendor_name if best_vid in vendor_responses else best_vid
            else:
                lowest_r = None
                best_vid = None
                best_vname = None
                delta_pct = None
                spread_pct = None

            row = RFxComparisonRow(
                sku_code=code,
                sku_name=name,
                category=cat,
                uom=uom,
                annual_volume=vol,
                baseline_rate=base_rate,
                vendor_rates=vendor_rates,
                lowest_rate=lowest_r,
                best_vendor_id=best_vid,
                best_vendor_name=best_vname,
                delta_vs_baseline_pct=delta_pct,
                spread_pct=spread_pct
            )
            rows.append(row)

        return rows

    @staticmethod
    def calculate_deal_totals(
        matrix: List[RFxComparisonRow],
        vendor_responses: Dict[str, VendorBidResponse]
    ) -> Dict[str, Any]:
        """
        Calculate macro deal metrics, baseline ₹4 Crore deal value, single vendor totals,
        and optimal L1 split savings.
        """
        total_baseline = sum(r.baseline_rate * r.annual_volume for r in matrix)
        total_optimal_l1 = 0.0
        vendor_single_totals: Dict[str, float] = {v_id: 0.0 for v_id in vendor_responses}
        vendor_coverage: Dict[str, int] = {v_id: 0 for v_id in vendor_responses}

        for r in matrix:
            vol = r.annual_volume
            if r.lowest_rate is not None:
                total_optimal_l1 += r.lowest_rate * vol

            for v_id, rate in r.vendor_rates.items():
                if rate is not None:
                    vendor_single_totals[v_id] += rate * vol
                    vendor_coverage[v_id] += 1
                else:
                    # If unquoted, penalize with baseline + 10% for single-vendor comparison
                    vendor_single_totals[v_id] += r.baseline_rate * 1.10 * vol

        # Factor in footnote discounts
        # Vendor 2 has 5% volume discount if total units > 5000 (annual units > 1M, easily qualifies)
        if "vendor_2" in vendor_responses and vendor_responses["vendor_2"].commercial_terms.discount_percentage > 0:
            disc = vendor_responses["vendor_2"].commercial_terms.discount_percentage / 100.0
            vendor_single_totals["vendor_2"] = round(vendor_single_totals["vendor_2"] * (1 - disc), 2)

        # Vendor 3 has 3% freight extra
        if "vendor_3" in vendor_responses:
            vendor_single_totals["vendor_3"] = round(vendor_single_totals["vendor_3"] * 1.03, 2)

        total_savings = total_baseline - total_optimal_l1
        savings_pct = (total_savings / total_baseline * 100) if total_baseline > 0 else 0.0

        return {
            "total_baseline_inr": round(total_baseline, 2),
            "total_optimal_l1_inr": round(total_optimal_l1, 2),
            "total_savings_inr": round(total_savings, 2),
            "total_savings_pct": round(savings_pct, 2),
            "vendor_single_totals": vendor_single_totals,
            "vendor_coverage": vendor_coverage,
        }

    @staticmethod
    def to_dataframe(matrix: List[RFxComparisonRow], vendor_responses: Dict[str, VendorBidResponse]) -> pd.DataFrame:
        """Convert comparison rows into a formatted display DataFrame."""
        records = []
        for r in matrix:
            rec = {
                "SKU Code": r.sku_code,
                "Description": r.sku_name,
                "Category": r.category,
                "UOM": r.uom,
                "Volume": f"{r.annual_volume:,}",
                "Baseline (₹)": f"₹ {r.baseline_rate:.2f}",
            }
            for v_id, v_resp in vendor_responses.items():
                col_name = f"{v_resp.vendor_name}"
                rate = r.vendor_rates.get(v_id)
                if rate is not None:
                    is_lowest = (rate == r.lowest_rate)
                    badge = " 🏆" if is_lowest else ""
                    rec[col_name] = f"₹ {rate:.2f}{badge}"
                else:
                    rec[col_name] = "❌ Unquoted"

            rec["L1 Best Rate"] = f"₹ {r.lowest_rate:.2f}" if r.lowest_rate is not None else "N/A"
            rec["Best Vendor"] = r.best_vendor_name or "N/A"
            rec["Variance %"] = f"{r.delta_vs_baseline_pct:+.1f}%" if r.delta_vs_baseline_pct is not None else "N/A"
            records.append(rec)

        return pd.DataFrame(records)
