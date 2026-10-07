"""Pydantic data schemas for packaging SKUs, vendor bids, audit traces, and split-awards."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class StandardSKU(BaseModel):
    """Catalog packaging SKU standard definition."""
    code: str = Field(description="Unique SKU identifier (e.g. PKG-001)")
    name: str = Field(description="SKU standard description")
    uom: str = Field(description="Standard Unit of Measure (Piece, Roll, Pack, Kg, etc.)")
    base_rate: float = Field(description="Internal baseline rate in INR")
    category: str = Field(description="Packaging category (Cartons, Tapes, Films, etc.)")
    annual_volume: int = Field(default=10000, description="Estimated annual demand quantity")


class LineProof(BaseModel):
    """Line-level visual proof and auditability metadata."""
    source_file: str = Field(description="Filename of the vendor source document")
    source_format: str = Field(description="Format (Excel, PDF, Word, Angled Image, Email)")
    raw_snippet: str = Field(description="Exact verbatim extracted text snippet or table cell content")
    page_or_row: str = Field(default="N/A", description="Page number, sheet row, or paragraph reference")
    confidence_score: float = Field(default=0.98, ge=0.0, le=1.0, description="Extraction confidence score")
    normalization_notes: str = Field(default="", description="Explanation of conversions applied (e.g. USD to INR @ 84.0)")
    bounding_box: Optional[Dict[str, float]] = Field(default=None, description="Normalized coordinates [x1, y1, x2, y2] if available")


class VendorLineItem(BaseModel):
    """Extracted and normalized line item quote from a vendor."""
    sku_code: str = Field(description="Mapped standard SKU Code")
    vendor_sku_code: Optional[str] = Field(default=None, description="SKU code verbatim from vendor document")
    description: str = Field(description="Verbatim or cleaned description from vendor")
    raw_rate: float = Field(description="Extracted rate before currency conversion")
    raw_currency: str = Field(default="INR", description="Extracted currency (INR, USD, EUR)")
    raw_uom: str = Field(default="Piece", description="Extracted Unit of Measure")
    normalized_rate: float = Field(description="Final normalized rate in INR")
    normalized_uom: str = Field(description="Standardized UOM matching catalog")
    moq: Optional[int] = Field(default=None, description="Minimum Order Quantity if specified")
    lead_time_days: Optional[int] = Field(default=None, description="Delivery lead time in days")
    is_quoted: bool = Field(default=True, description="False if vendor marked as Out of Stock / Unquoted")
    proof: LineProof = Field(description="Audit trail and ground truth extraction proof")


class CommercialTerms(BaseModel):
    """Vendor commercial terms, warranties, delivery, and buried footnote discounts."""
    payment_terms: str = Field(default="Standard Net 30", description="Payment terms extracted")
    warranty: str = Field(default="Standard OEM", description="Warranty terms")
    freight_terms: str = Field(default="Included", description="Freight / shipping conditions")
    volume_discount_clause: Optional[str] = Field(default=None, description="Volume discount rules (e.g. 5% on > 5,000 units)")
    discount_percentage: float = Field(default=0.0, description="Applicable volume discount percentage")
    tax_terms: str = Field(default="Exclusive of GST", description="Tax terms (GST, etc.)")
    raw_notes: List[str] = Field(default_factory=list, description="Raw commercial clauses extracted from document")


class VendorBidResponse(BaseModel):
    """Complete parsed and normalized bid response from a vendor."""
    vendor_id: str = Field(description="Unique vendor identifier (vendor_1, vendor_2, ...)")
    vendor_name: str = Field(description="Vendor company name")
    source_filename: str = Field(description="Source artifact name")
    source_format: str = Field(description="File format type")
    total_items_quoted: int = Field(description="Number of valid quoted items")
    total_items_requested: int = Field(default=30, description="Total RFx items in scope")
    currency: str = Field(default="INR", description="Document currency")
    commercial_terms: CommercialTerms = Field(default_factory=CommercialTerms)
    line_items: Dict[str, VendorLineItem] = Field(default_factory=dict, description="Keyed by SKU Code")
    parsing_status: str = Field(default="Success", description="Status (Success, Warning, Error)")
    extraction_time_ms: float = Field(default=0.0, description="Processing duration in milliseconds")


class RFxComparisonRow(BaseModel):
    """Unified row in the RFx comparison matrix."""
    sku_code: str
    sku_name: str
    category: str
    uom: str
    annual_volume: int
    baseline_rate: float
    vendor_rates: Dict[str, Optional[float]] = Field(default_factory=dict, description="Vendor ID -> Normalized INR rate")
    lowest_rate: Optional[float] = None
    best_vendor_id: Optional[str] = None
    best_vendor_name: Optional[str] = None
    delta_vs_baseline_pct: Optional[float] = None
    spread_pct: Optional[float] = None


class SplitAwardItem(BaseModel):
    """Allocation recommendation for a single SKU in a split-award."""
    sku_code: str
    sku_name: str
    category: str
    annual_volume: int
    awarded_vendor_id: str
    awarded_vendor_name: str
    awarded_rate: float
    baseline_rate: float
    total_cost: float
    baseline_cost: float
    savings_amount: float
    savings_pct: float
    reasoning: str


class SplitAwardSummary(BaseModel):
    """Overall split-award optimization summary."""
    total_deal_value_baseline: float
    total_deal_value_optimized: float
    total_savings_amount: float
    total_savings_pct: float
    vendor_spend_distribution: Dict[str, float] = Field(default_factory=dict)
    vendor_line_distribution: Dict[str, int] = Field(default_factory=dict)
    allocations: List[SplitAwardItem] = Field(default_factory=list)


class CopilotQueryResponse(BaseModel):
    """Response structure for natural language interrogation copilot."""
    query: str
    answer_markdown: str
    highlighted_skus: List[str] = Field(default_factory=list)
    suggested_followups: List[str] = Field(default_factory=list)
    simulation_data: Optional[Dict] = None
