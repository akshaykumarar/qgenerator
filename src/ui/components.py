"""UI Components for Autonomous RFx Intelligent Sourcing & Normalization Assistant."""
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
from src.generator.packaging_generator import (
    DEFAULT_PACKAGING_SKUS,
    get_cached_file,
    create_dataset_zip,
)


def render_file_badges(dataset_dir: str = "./vendor_dataset") -> None:
    """Render file card badges with live in-memory download buttons for all 6 generated artifacts (RFI + 5 Vendors)."""
    files_meta = [
        {
            "name": "rfi_baseline_specification.xlsx",
            "vendor": "🎯 Master RFI Document",
            "format": "Excel (.xlsx)",
            "type": "excel",
            "desc": "Official RFI & BOQ (50-500 units, standard UOMs)",
            "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "label": "📥 Download RFI Excel"
        },
        {
            "name": "vendor1_alpha_pack_custom_excel.xlsx",
            "vendor": "Vendor 1: Alpha Pack",
            "format": "Excel (.xlsx)",
            "type": "excel",
            "desc": "Custom headers, MOQs & freight notes",
            "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "label": "📥 Download Excel"
        },
        {
            "name": "vendor2_beta_box_clean_table.pdf",
            "vendor": "Vendor 2: Beta Box",
            "format": "Vector PDF (.pdf)",
            "type": "pdf",
            "desc": "Tabular rate card & 5% volume discount footnote",
            "mime": "application/pdf",
            "label": "📥 Download PDF"
        },
        {
            "name": "vendor3_gamma_packaging_prose.docx",
            "vendor": "Vendor 3: Gamma Pack",
            "format": "Word (.docx)",
            "type": "word",
            "desc": "Prose SLA, 100% warranty, freight 3% & extra item",
            "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "label": "📥 Download Word"
        },
        {
            "name": "vendor4_delta_angled_ratecard.png",
            "vendor": "Vendor 4: Delta Print",
            "format": "Angled Photo (2-Part)",
            "type": "image",
            "desc": "Smartphone snap in 2 parts with perspective skew",
            "mime": "image/png",
            "label": "📥 Download Image"
        },
        {
            "name": "vendor5_epsilon_global_raw_email.txt",
            "vendor": "Vendor 5: Epsilon Global",
            "format": "Raw Email (.txt)",
            "type": "email",
            "desc": "USD rates ($) with flat ocean freight ($350)",
            "mime": "text/plain",
            "label": "📥 Download Email"
        },
    ]

    st.markdown('<div class="file-badge-grid">', unsafe_allow_html=True)
    cols = st.columns(len(files_meta))
    
    for idx, (col, meta) in enumerate(zip(cols, files_meta)):
        file_bytes = get_cached_file(meta["name"], target_dir=dataset_dir)
        exists = file_bytes is not None and len(file_bytes) > 0
        size_kb = round(len(file_bytes) / 1024, 1) if exists else 0
        status_text = f"✓ Ready ({size_kb} KB)" if exists else "⚠️ Missing"
        status_color = "#00A88F" if exists else "#D97706"

        with col:
            st.markdown(f"""
            <div class="file-badge-card {meta['type']}">
                <div class="file-badge-info" style="width: 100%;">
                    <h5>{meta['vendor']}</h5>
                    <p><b>{meta['format']}</b> | <span style="color:{status_color};font-weight:600;">{status_text}</span></p>
                    <p style="color:#64748B;font-size:0.7rem;margin-top:2px;">{meta['desc']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if exists:
                st.download_button(
                    label=meta["label"],
                    data=file_bytes,
                    file_name=meta["name"],
                    mime=meta["mime"],
                    key=f"dl_btn_{idx}_{meta['name']}",
                    use_container_width=True
                )
    st.markdown('</div>', unsafe_allow_html=True)


def render_dataset_download_actions(dataset_dir: str = "./vendor_dataset") -> None:
    """Render full ZIP bundle download button and archive summary for all 6 generated files."""
    zip_bytes = create_dataset_zip(target_dir=dataset_dir)
    archive_dir = os.path.join(dataset_dir, "archive")
    archive_count = len(os.listdir(archive_dir)) if os.path.exists(archive_dir) else 0

    c1, c2 = st.columns([2, 1])
    with c1:
        if zip_bytes and len(zip_bytes) > 0:
            st.download_button(
                label="📦 Download Complete 6-File RFx & Vendor Dataset (ZIP Bundle)",
                data=zip_bytes,
                file_name="RFx_and_5_Vendor_Dataset.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True,
                help="Download all 6 multi-format files (RFI Excel/Prompt, Vendor 1 Excel, Vendor 2 PDF, Vendor 3 Word, Vendor 4 Dual Photos, Vendor 5 USD Email) in a single zip archive."
            )
    with c2:
        if archive_count > 0:
            st.caption(f"📁 **Auto-Archive Active**: {archive_count} prior datasets archived in cache.")


def _format_currency(val: float) -> str:
    """Helper to format currency cleanly across Cr, Lakhs, or Thousands."""
    if val >= 1e7:
        return f"₹ {val / 1e7:.2f} Cr"
    elif val >= 1e5:
        return f"₹ {val / 1e5:.2f} Lakhs"
    elif val >= 1e3:
        return f"₹ {val / 1e3:.1f} K"
    else:
        return f"₹ {val:,.2f}"


def render_kpi_cards(deal_totals: Dict[str, Any], vendor_responses: Dict[str, VendorBidResponse]) -> None:
    """Render executive KPI cards for total deal value, savings, coverage, and footnote alerts."""
    col1, col2, col3, col4 = st.columns(4)

    baseline_val = deal_totals.get("total_baseline_inr", 0)
    optimal_val = deal_totals.get("total_optimal_l1_inr", 0)
    savings_val = deal_totals.get("total_savings_inr", 0)
    savings_pct = deal_totals.get("total_savings_pct", 0)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">RFx Portfolio Baseline</div>
            <div class="metric-value">{_format_currency(baseline_val)}</div>
            <div class="metric-sub" style="color:#64748B;">30 Packaging Consumables (50-500 Qty)</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card accent">
            <div class="metric-label">Optimal Split-Award Deal</div>
            <div class="metric-value" style="color:#00A88F;">{_format_currency(optimal_val)}</div>
            <div class="metric-sub">Net Savings: {_format_currency(savings_val)} ({savings_pct:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        v5_quoted = vendor_responses.get("vendor_5", None)
        v5_quoted_count = v5_quoted.total_items_quoted if v5_quoted else 27
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Bid Completeness</div>
            <div class="metric-value">4 / 5 <span style="font-size:1rem;color:#64748B;">100%</span></div>
            <div class="metric-sub" style="color:#D97706;">Vendor 5: {v5_quoted_count}/30 lines (USD Quote)</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card warning">
            <div class="metric-label">Buried Footnote Impact</div>
            <div class="metric-value" style="color:#D97706;">5% Volume Disc</div>
            <div class="metric-sub">Vendor 2 (&gt;1,500 Units) = Landed TCO Benefit</div>
        </div>
        """, unsafe_allow_html=True)


def render_line_level_proof_drawer(
    selected_sku: str,
    vendor_responses: Dict[str, VendorBidResponse],
    dataset_dir: str = "./vendor_dataset"
) -> None:
    """Render interactive line-level visual proof & ground truth inspection drawer."""
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
            Category: <b>{sku_info['category']}</b> | UOM: <b>{sku_info['uom']}</b> | Internal Baseline: <b>₹ {sku_info['base_rate']:.2f}</b> | BOQ Volume: <b>{sku_info['annual_volume']:,} {sku_info['uom']}</b>
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
                    img_p1 = get_cached_file("vendor4_delta_angled_ratecard_p1.png", target_dir=dataset_dir)
                    img_p2 = get_cached_file("vendor4_delta_angled_ratecard_p2.png", target_dir=dataset_dir)
                    img_main = get_cached_file("vendor4_delta_angled_ratecard.png", target_dir=dataset_dir)
                    
                    with st.expander("📷 View Angled Rate Card Snapshots (2 Parts)"):
                        if img_p1 and img_p2:
                            c_img1, c_img2 = st.columns(2)
                            with c_img1:
                                st.image(img_p1, caption="Part 1: Cartons & Tapes", use_container_width=True)
                            with c_img2:
                                st.image(img_p2, caption="Part 2: Films & Specialty", use_container_width=True)
                        elif img_main:
                            st.image(img_main, caption="Vendor 4 Perspective Rate Card Image", use_container_width=True)
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
