"""UI Components for Autonomous RFx Intelligent Procurement Assistant."""
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any

from src.models.schemas import (
    VendorBidResponse,
    RFxComparisonRow,
    SplitAwardSummary,
    LineProof,
)
from src.generator.packaging_generator import DEFAULT_PACKAGING_SKUS


def render_file_badges(dataset_dir: str = "./vendor_dataset") -> None:
    """Render file card badges for all generated vendor bid artifacts."""
    files_meta = [
        {"name": "vendor1_alpha_pack_custom_excel.xlsx", "vendor": "Vendor 1: Alpha Pack Solutions", "format": "Excel (.xlsx)", "type": "excel", "desc": "Custom column headers & GST footnotes"},
        {"name": "vendor2_beta_box_clean_table.pdf", "vendor": "Vendor 2: Beta Box & Container Ltd", "format": "Vector PDF (.pdf)", "type": "pdf", "desc": "Tabular rate card & 5% volume footnote"},
        {"name": "vendor3_gamma_packaging_prose.docx", "vendor": "Vendor 3: Gamma Packaging Works", "format": "Word (.docx)", "type": "word", "desc": "Embedded table & 100% warranty prose SLA"},
        {"name": "vendor4_delta_angled_ratecard.png", "vendor": "Vendor 4: Delta Print & Pack", "format": "Angled Photo (.png)", "type": "image", "desc": "Smartphone snap with perspective skew"},
        {"name": "vendor5_epsilon_global_raw_email.txt", "vendor": "Vendor 5: Epsilon Global Pte", "format": "Raw Email (.txt)", "type": "email", "desc": "USD currency rates (27/30 lines quoted)"},
    ]

    st.markdown('<div class="file-badge-grid">', unsafe_allow_html=True)
    cols = st.columns(len(files_meta))
    
    for idx, (col, meta) in enumerate(zip(cols, files_meta)):
        fpath = os.path.join(dataset_dir, meta["name"])
        exists = os.path.exists(fpath)
        size_kb = round(os.path.getsize(fpath) / 1024, 1) if exists else 0
        status_text = f"✓ Ready ({size_kb} KB)" if exists else "⚠️ Missing (Click Generate)"
        status_color = "#00A88F" if exists else "#D97706"

        with col:
            st.markdown(f"""
            <div class="file-badge-card {meta['type']}">
                <div class="file-badge-info">
                    <h5>{meta['vendor']}</h5>
                    <p><b>{meta['format']}</b> | <span style="color:{status_color};font-weight:600;">{status_text}</span></p>
                    <p style="color:#64748B;font-size:0.7rem;margin-top:2px;">{meta['desc']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_kpi_cards(deal_totals: Dict[str, Any], vendor_responses: Dict[str, VendorBidResponse]) -> None:
    """Render executive KPI cards for total deal value, savings, coverage, and footnote alerts."""
    col1, col2, col3, col4 = st.columns(4)

    baseline_cr = deal_totals.get("total_baseline_inr", 0) / 1e7
    optimal_cr = deal_totals.get("total_optimal_l1_inr", 0) / 1e7
    savings_lakh = deal_totals.get("total_savings_inr", 0) / 1e5
    savings_pct = deal_totals.get("total_savings_pct", 0)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">RFx Portfolio Baseline</div>
            <div class="metric-value">₹ {baseline_cr:.2f} Cr</div>
            <div class="metric-sub" style="color:#64748B;">30 Packaging Consumables</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card accent">
            <div class="metric-label">Optimal Split-Award Deal</div>
            <div class="metric-value" style="color:#00A88F;">₹ {optimal_cr:.2f} Cr</div>
            <div class="metric-sub">Net Savings: ₹ {savings_lakh:.1f}L ({savings_pct:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        # Vendor with max quoted items
        v5_quoted = vendor_responses.get("vendor_5", None)
        v5_quoted_count = v5_quoted.total_items_quoted if v5_quoted else 27
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Bid Completeness</div>
            <div class="metric-value">4 / 5 <span style="font-size:1rem;color:#64748B;">100%</span></div>
            <div class="metric-sub" style="color:#D97706;">Vendor 5: {v5_quoted_count}/30 lines (3 OOS)</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card warning">
            <div class="metric-label">Buried Footnote Impact</div>
            <div class="metric-value" style="color:#D97706;">5% Volume Disc</div>
            <div class="metric-sub">Beta Box (&gt;5k Units) = -₹1.8L Delta</div>
        </div>
        """, unsafe_allow_html=True)


def render_line_level_proof_drawer(
    selected_sku: str,
    vendor_responses: Dict[str, VendorBidResponse],
    dataset_dir: str = "./vendor_dataset"
) -> None:
    """Render interactive line-level visual proof & ground truth inspection drawer."""
    # Find SKU standard info
    sku_info = next((s for s in DEFAULT_PACKAGING_SKUS if s["code"] == selected_sku), None)
    if not sku_info:
        st.warning("Select a valid SKU code to inspect visual proof.")
        return

    st.markdown(f"""
    <div style="background:#002B49; color:#FFFFFF; padding:0.85rem 1.25rem; border-radius:8px 8px 0 0; margin-top:1rem;">
        <h4 style="margin:0; font-size:1.1rem; color:#FFFFFF;">
            🔍 Ground Truth Audit Trace: <span style="color:#00E5C0;">{selected_sku}</span> — {sku_info['name']}
        </h4>
        <p style="margin:0.25rem 0 0 0; font-size:0.8rem; color:#A0C4DE;">
            Category: <b>{sku_info['category']}</b> | UOM: <b>{sku_info['uom']}</b> | Internal Baseline: <b>₹ {sku_info['base_rate']:.2f}</b> | Annual Volume: <b>{sku_info['annual_volume']:,} units</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

    proof_cols = st.columns(len(vendor_responses))
    
    for col, (v_id, v_resp) in zip(proof_cols, vendor_responses.items()):
        item = v_resp.line_items.get(selected_sku)
        with col:
            if item and item.is_quoted:
                confidence_pct = int(item.proof.confidence_score * 100)
                badge_bg = "#E6FFFA" if confidence_pct >= 95 else "#FEF3C7"
                badge_fg = "#00A88F" if confidence_pct >= 95 else "#D97706"

                st.markdown(f"""
                <div class="proof-box">
                    <div class="proof-title">
                        <span>{v_resp.vendor_name}</span>
                        <span style="background:{badge_bg}; color:{badge_fg}; font-size:0.7rem; padding:2px 6px; border-radius:4px; font-weight:700;">
                            {confidence_pct}% AI Confidence
                        </span>
                    </div>
                    <div style="margin-top:0.4rem; font-size:0.82rem;">
                        <b>Rate:</b> <span style="font-size:1.05rem; font-weight:700; color:#002B49;">₹ {item.normalized_rate:.2f}</span>
                        <span style="font-size:0.75rem; color:#64748B;">({item.raw_currency} {item.raw_rate:.2f} / {item.raw_uom})</span>
                    </div>
                    <div style="font-size:0.75rem; color:#475569; margin-top:4px;">
                        <b>Source:</b> {item.proof.source_format} ({item.proof.page_or_row})
                    </div>
                    <div class="proof-snippet">
                        {item.proof.raw_snippet}
                    </div>
                    <div style="font-size:0.72rem; color:#00A88F; margin-top:2px;">
                        <i>ℹ️ {item.proof.normalization_notes}</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if v_id == "vendor_4":
                    img_path = os.path.join(dataset_dir, "vendor4_delta_angled_ratecard.png")
                    if os.path.exists(img_path):
                        with st.expander("📷 View Angled Rate Card Snapshot"):
                            st.image(img_path, caption="Vendor 4 Perspective Rate Card Image", use_container_width=True)
            else:
                st.markdown(f"""
                <div class="proof-box" style="border-left-color:#D9383A; background:#FFF5F5;">
                    <div class="proof-title" style="color:#C53030;">
                        <span>{v_resp.vendor_name}</span>
                        <span style="background:#FED7D7; color:#C53030; font-size:0.7rem; padding:2px 6px; border-radius:4px; font-weight:700;">
                            Unquoted / OOS
                        </span>
                    </div>
                    <p style="font-size:0.8rem; color:#742A2A; margin:0.5rem 0;">
                        Vendor explicitly omitted or marked this SKU as <b>OUT OF STOCK</b> in raw bid email.
                    </p>
                    <div class="proof-snippet" style="color:#9B2C2C; border-color:#FEB2B2;">
                        "PKG-003: OUT OF STOCK / UNABLE TO QUOTE"
                    </div>
                </div>
                """, unsafe_allow_html=True)


def render_spend_charts(split_summary: SplitAwardSummary) -> None:
    """Render interactive Plotly spend distribution charts for split-award allocation."""
    c1, c2 = st.columns(2)

    with c1:
        # Donut chart of Spend Distribution
        labels = list(split_summary.vendor_spend_distribution.keys())
        values = list(split_summary.vendor_spend_distribution.values())

        fig_spend = px.pie(
            names=labels,
            values=values,
            hole=0.45,
            title="Awarded Spend Distribution by Vendor (₹)",
            color_discrete_sequence=["#002B49", "#00A88F", "#185ABD", "#8E44AD", "#D97706"]
        )
        fig_spend.update_traces(textinfo="percent+label", pull=[0.05]*len(labels))
        fig_spend.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=320)
        st.plotly_chart(fig_spend, use_container_width=True)

    with c2:
        # Bar chart of Lines Awarded per Vendor
        line_labels = list(split_summary.vendor_line_distribution.keys())
        line_vals = list(split_summary.vendor_line_distribution.values())

        fig_lines = go.Figure(data=[
            go.Bar(
                x=line_labels,
                y=line_vals,
                text=line_vals,
                textposition='auto',
                marker_color=["#002B49", "#00A88F", "#185ABD", "#8E44AD", "#D97706"][:len(line_labels)]
            )
        ])
        fig_lines.update_layout(
            title="Number of SKUs Awarded (L1 Allocation)",
            xaxis_title="Vendor",
            yaxis_title="SKU Count",
            margin=dict(t=40, b=10, l=10, r=10),
            height=320
        )
        st.plotly_chart(fig_lines, use_container_width=True)
