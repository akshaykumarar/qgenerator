"""Split-Award Optimization and Allocation Engine for RFx Strategic Sourcing."""
from typing import Dict, List, Optional
from src.models.schemas import (
    RFxComparisonRow,
    VendorBidResponse,
    SplitAwardItem,
    SplitAwardSummary,
)


class SplitAwardOptimizer:
    """Calculates optimal vendor award splits and savings against baseline."""

    @staticmethod
    def optimize_l1_split(
        matrix: List[RFxComparisonRow],
        vendor_responses: Dict[str, VendorBidResponse]
    ) -> SplitAwardSummary:
        """
        Pure Line-by-Line L1 Optimization: Award each SKU to the lowest verified vendor quote.
        """
        allocations: List[SplitAwardItem] = []
        vendor_spend: Dict[str, float] = {v.vendor_name: 0.0 for v in vendor_responses.values()}
        vendor_lines: Dict[str, int] = {v.vendor_name: 0 for v in vendor_responses.values()}

        total_baseline = 0.0
        total_optimized = 0.0

        for r in matrix:
            vol = r.annual_volume
            baseline_cost = r.baseline_rate * vol
            total_baseline += baseline_cost

            # Best vendor rate
            if r.lowest_rate is not None and r.best_vendor_name:
                awarded_name = r.best_vendor_name
                awarded_vid = r.best_vendor_id or "unknown"
                awarded_rate = r.lowest_rate
                reasoning = f"L1 Lowest Verified Quote (₹{awarded_rate:.2f} vs Baseline ₹{r.baseline_rate:.2f})"
            else:
                awarded_name = "Baseline Default"
                awarded_vid = "internal"
                awarded_rate = r.baseline_rate
                reasoning = "No valid quotes available; retained at baseline"

            line_cost = awarded_rate * vol
            total_optimized += line_cost
            savings = baseline_cost - line_cost
            savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0.0

            if awarded_name in vendor_spend:
                vendor_spend[awarded_name] += line_cost
                vendor_lines[awarded_name] += 1

            allocations.append(SplitAwardItem(
                sku_code=r.sku_code,
                sku_name=r.sku_name,
                category=r.category,
                annual_volume=vol,
                awarded_vendor_id=awarded_vid,
                awarded_vendor_name=awarded_name,
                awarded_rate=awarded_rate,
                baseline_rate=r.baseline_rate,
                total_cost=round(line_cost, 2),
                baseline_cost=round(baseline_cost, 2),
                savings_amount=round(savings, 2),
                savings_pct=round(savings_pct, 2),
                reasoning=reasoning
            ))

        total_savings = total_baseline - total_optimized
        total_savings_pct = (total_savings / total_baseline * 100) if total_baseline > 0 else 0.0

        return SplitAwardSummary(
            total_deal_value_baseline=round(total_baseline, 2),
            total_deal_value_optimized=round(total_optimized, 2),
            total_savings_amount=round(total_savings, 2),
            total_savings_pct=round(total_savings_pct, 2),
            vendor_spend_distribution={k: round(v, 2) for k, v in vendor_spend.items() if v > 0},
            vendor_line_distribution={k: v for k, v in vendor_lines.items() if v > 0},
            allocations=allocations
        )

    @staticmethod
    def optimize_2vendor_split(
        matrix: List[RFxComparisonRow],
        vendor_responses: Dict[str, VendorBidResponse],
        primary_vendor_id: str = "vendor_1",
        secondary_vendor_id: str = "vendor_3"
    ) -> SplitAwardSummary:
        """
        Constrained 2-Vendor Strategic Split Award (e.g. Vendor 1 & Vendor 3).
        """
        allocations: List[SplitAwardItem] = []
        v1 = vendor_responses.get(primary_vendor_id)
        v2 = vendor_responses.get(secondary_vendor_id)
        
        v1_name = v1.vendor_name if v1 else primary_vendor_id
        v2_name = v2.vendor_name if v2 else secondary_vendor_id

        vendor_spend: Dict[str, float] = {v1_name: 0.0, v2_name: 0.0}
        vendor_lines: Dict[str, int] = {v1_name: 0, v2_name: 0}

        total_baseline = 0.0
        total_optimized = 0.0

        for r in matrix:
            vol = r.annual_volume
            baseline_cost = r.baseline_rate * vol
            total_baseline += baseline_cost

            r1 = r.vendor_rates.get(primary_vendor_id)
            r2 = r.vendor_rates.get(secondary_vendor_id)

            if r1 is not None and r2 is not None:
                if r1 <= r2:
                    awarded_vid = primary_vendor_id
                    awarded_name = v1_name
                    awarded_rate = r1
                else:
                    awarded_vid = secondary_vendor_id
                    awarded_name = v2_name
                    awarded_rate = r2
            elif r1 is not None:
                awarded_vid = primary_vendor_id
                awarded_name = v1_name
                awarded_rate = r1
            elif r2 is not None:
                awarded_vid = secondary_vendor_id
                awarded_name = v2_name
                awarded_rate = r2
            else:
                awarded_vid = primary_vendor_id
                awarded_name = v1_name
                awarded_rate = r.baseline_rate

            line_cost = awarded_rate * vol
            total_optimized += line_cost
            savings = baseline_cost - line_cost
            savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0.0

            vendor_spend[awarded_name] += line_cost
            vendor_lines[awarded_name] += 1

            allocations.append(SplitAwardItem(
                sku_code=r.sku_code,
                sku_name=r.sku_name,
                category=r.category,
                annual_volume=vol,
                awarded_vendor_id=awarded_vid,
                awarded_vendor_name=awarded_name,
                awarded_rate=awarded_rate,
                baseline_rate=r.baseline_rate,
                total_cost=round(line_cost, 2),
                baseline_cost=round(baseline_cost, 2),
                savings_amount=round(savings, 2),
                savings_pct=round(savings_pct, 2),
                reasoning=f"2-Vendor Strategy: Chosen between {v1_name} and {v2_name}"
            ))

        total_savings = total_baseline - total_optimized
        total_savings_pct = (total_savings / total_baseline * 100) if total_baseline > 0 else 0.0

        return SplitAwardSummary(
            total_deal_value_baseline=round(total_baseline, 2),
            total_deal_value_optimized=round(total_optimized, 2),
            total_savings_amount=round(total_savings, 2),
            total_savings_pct=round(total_savings_pct, 2),
            vendor_spend_distribution={k: round(v, 2) for k, v in vendor_spend.items()},
            vendor_line_distribution=vendor_lines,
            allocations=allocations
        )
