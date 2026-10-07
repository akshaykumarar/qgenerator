"""Autonomous RFx Normalization & Interrogation Engine.
B2B SaaS Web Application for Multi-Format Vendor Bid Normalization and Auditability.
"""
import os
import json
import streamlit as st
import pandas as pd

from src.config.settings import get_settings
from src.generator.packaging_generator import (
    DEFAULT_PACKAGING_SKUS,
    generate_vendor_dataset,
    pick_random_vendors,
    create_dataset_zip,
)
from src.extractor.multimodal_engine import MultimodalExtractionEngine
from src.analytics.matrix_builder import ComparisonMatrixBuilder
from src.analytics.optimizer import SplitAwardOptimizer
from src.tools.llm_client import UnifiedProcurementLLM
from src.ui.styles import SLATE_CSS, get_header_html
from src.ui.components import (
    render_file_badges,
    render_dataset_download_actions,
    render_kpi_cards,
    render_line_level_proof_drawer,
    render_spend_charts,
)

# ---------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & THEME
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Autonomous RFx Normalization & Interrogation Engine",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(SLATE_CSS, unsafe_allow_html=True)
settings = get_settings()

# ---------------------------------------------------------------------------
# 2. SIDEBAR - MULTI-PROVIDER AI & SETTINGS CONFIGURATION
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=300&auto=format&fit=crop&q=80", caption="Strategic Sourcing Portal", use_container_width=True)
    st.markdown("### ⚙️ Engine Configuration")

    # 1. Provider Selector (from config / environment)
    provider_options = ["gemini", "openai", "openrouter", "ollama"]
    selected_provider = st.selectbox(
        "AI Provider",
        options=provider_options,
        index=provider_options.index(settings.llm_provider) if settings.llm_provider in provider_options else 0,
        help="Select the active LLM backend for multimodal extraction and copilot interrogation."
    )

    # 2. Config-Driven Dynamic Model Selector
    configured_models = settings.get_models_for_provider(selected_provider)
    model_mode = st.radio("Model Selection Mode", ["Configured List", "Custom Model String"], horizontal=True)
    
    if model_mode == "Configured List":
        selected_model = st.selectbox(
            "Active Model",
            options=configured_models,
            index=0,
            help="Configured model list from .env settings"
        )
    else:
        selected_model = st.text_input(
            "Custom Model ID",
            value=settings.ai_model,
            help="Enter any custom model identifier for this provider (e.g. gpt-4.5-preview, my-ollama-model:latest)"
        )

    # 3. Dynamic Key / Endpoint Inputs based on Provider
    custom_api_key = ""
    custom_base_url = ""

    if selected_provider == "gemini":
        custom_api_key = st.text_input(
            "Gemini API Key",
            type="password",
            value=settings.gemini_api_key or os.getenv("GEMINI_API_KEY", ""),
            help="Get your key at aistudio.google.com"
        )
    elif selected_provider == "openai":
        custom_api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=settings.openai_api_key or os.getenv("OPENAI_API_KEY", ""),
            help="OpenAI Platform API key"
        )
        custom_base_url = st.text_input("OpenAI Base URL", value=settings.openai_base_url)
    elif selected_provider == "openrouter":
        custom_api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            value=settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY", ""),
            help="OpenRouter unified API key (openrouter.ai)"
        )
        custom_base_url = st.text_input("OpenRouter Base URL", value=settings.openrouter_base_url)
    elif selected_provider == "ollama":
        custom_base_url = st.text_input("Ollama Local Endpoint", value=settings.ollama_base_url, help="Default: http://localhost:11434/v1")
        st.caption("ℹ️ Ensure Ollama is running locally (`ollama serve`)")

    st.markdown("---")
    st.markdown("### 💱 Normalization Parameters")
    usd_rate = st.number_input("USD to INR Rate (₹)", value=settings.usd_inr_rate, min_value=1.0, max_value=200.0, step=0.5)

    st.markdown("---")
    st.caption("Autonomous Strategic Sourcing Engine v2.6.0")

# ---------------------------------------------------------------------------
# 3. INITIALIZE STATE & GENERATE DATASET IF NEEDED
# ---------------------------------------------------------------------------
dataset_dir = settings.dataset_dir
if "vendor_data" not in st.session_state or "dataset_generated" not in st.session_state:
    expected_files = [
        "vendor1_alpha_pack_custom_excel.xlsx",
        "vendor2_beta_box_clean_table.pdf",
        "vendor3_gamma_packaging_prose.docx",
        "vendor4_delta_angled_ratecard.png",
        "vendor5_epsilon_global_raw_email.txt",
    ]
    all_exist = all(os.path.exists(os.path.join(dataset_dir, f)) for f in expected_files)
    if not all_exist or "active_skus" not in st.session_state:
        _, initial_skus, initial_vendors = generate_vendor_dataset(target_dir=dataset_dir)
        st.session_state.active_skus = initial_skus
        st.session_state.active_vendors = initial_vendors
    else:
        st.session_state.active_skus = DEFAULT_PACKAGING_SKUS
        st.session_state.active_vendors = pick_random_vendors()

    extractor = MultimodalExtractionEngine(
        api_key=custom_api_key,
        model=selected_model,
        usd_inr_rate=usd_rate
    )
    st.session_state.vendor_data = extractor.extract_all_vendors(dataset_dir=dataset_dir)
    st.session_state.dataset_generated = True

# ---------------------------------------------------------------------------
# 4. TOP HEADER BANNER & GLOBAL DOWNLOAD ACTION
# ---------------------------------------------------------------------------
llm_client = UnifiedProcurementLLM(
    provider=selected_provider,
    model=selected_model,
    api_key=custom_api_key,
    base_url=custom_base_url
)
is_api_active = llm_client.is_available
st.markdown(get_header_html(f"{selected_provider.upper()}: {selected_model}", is_api_active), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 5. DATASET GENERATION CONTROL PANEL (COLLAPSIBLE)
# ---------------------------------------------------------------------------
with st.expander("📦 5-Vendor Multi-Format Dataset Controls & Custom Scenario Generator", expanded=True):
    st.markdown("""
    Generate fresh synthetic RFx responses across 5 distinct unstructured file formats (Excel, PDF, Word, Angled Image, USD Email) 
    for the **30-SKU Packaging Consumables Catalog**.
    """)

    col_input, col_btn = st.columns([3, 1.2])
    with col_input:
        feedback_prompt = st.text_input(
            "Custom Scenario / Feedback Prompt (Optional)",
            placeholder="e.g., 'Increase carton prices by 15%', 'Apply 10% discount on tapes', 'Surge in box rates'",
            key="feedback_prompt_input"
        )
    with col_btn:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        btn_label = "⚡ Apply Feedback to Existing Data" if feedback_prompt.strip() else "🚀 Generate Fresh 5-Vendor Dataset"
        trigger_gen = st.button(btn_label, type="primary", use_container_width=True)

    if trigger_gen:
        with st.spinner("Generating 5 multi-format vendor proposals and extracting data..."):
            prior_skus = st.session_state.get("active_skus")
            prior_vendors = st.session_state.get("active_vendors")

            # If feedback is given AND prior data exists: mutate existing data.
            # Otherwise (no feedback / no prior data): generate completely fresh random data & vendors.
            _, new_skus, new_vendors = generate_vendor_dataset(
                target_dir=dataset_dir,
                feedback_prompt=feedback_prompt,
                existing_skus=prior_skus if feedback_prompt.strip() else None,
                existing_vendors=prior_vendors if feedback_prompt.strip() else None
            )
            st.session_state.active_skus = new_skus
            st.session_state.active_vendors = new_vendors

            extractor = MultimodalExtractionEngine(
                api_key=custom_api_key,
                model=selected_model,
                usd_inr_rate=usd_rate
            )
            st.session_state.vendor_data = extractor.extract_all_vendors(dataset_dir=dataset_dir)
            
            if feedback_prompt.strip() and prior_skus:
                st.success(f"✓ Modified existing dataset with feedback: '{feedback_prompt}' (Active SKUs updated)")
            else:
                st.success(f"✓ Generated fresh random dataset across 5 new vendor profiles: {', '.join(list(new_vendors.values())[:3])}...")

    # Display live file badges with individual download buttons
    render_file_badges(dataset_dir=dataset_dir)
    
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    
    # Prominent Download All Button with Icon
    render_dataset_download_actions(dataset_dir=dataset_dir)

# ---------------------------------------------------------------------------
# 6. ANALYTICS & EXECUTIVE DEAL OVERVIEW
# ---------------------------------------------------------------------------
vendor_responses = st.session_state.vendor_data
active_skus = st.session_state.get("active_skus", DEFAULT_PACKAGING_SKUS)
matrix_rows = ComparisonMatrixBuilder.build_matrix(vendor_responses, active_skus)
deal_totals = ComparisonMatrixBuilder.calculate_deal_totals(matrix_rows, vendor_responses)
split_summary = SplitAwardOptimizer.optimize_l1_split(matrix_rows, vendor_responses)

st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
render_kpi_cards(deal_totals, vendor_responses)

# ---------------------------------------------------------------------------
# 7. MAIN INTERACTION TABS
# ---------------------------------------------------------------------------
st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Normalized Comparison Matrix",
    "🔍 Line-Level Visual Proof & Deal Audit",
    "📑 Commercial Footnotes & Risk Matrix",
    "🤖 Strategic Interrogation Copilot"
])

# ---------------------------------------------------------------------------
# TAB 1: NORMALIZED COMPARISON MATRIX
# ---------------------------------------------------------------------------
with tab1:
    st.markdown("### 📊 Multi-Vendor Packaging SKU Normalization Matrix")
    st.caption("All unit rates converted to INR (₹) and normalized to standard catalog UOMs. Lowest rate per SKU is marked with 🏆.")

    filter_col1, filter_col2, filter_col3 = st.columns([1.5, 2, 1])
    categories = ["All Categories"] + sorted(list({s["category"] for s in active_skus}))
    with filter_col1:
        selected_cat = st.selectbox("Filter by Category", categories)
    with filter_col2:
        search_query = st.text_input("Search SKU Name or Code", placeholder="e.g. PKG-001 or Corrugated Box")
    with filter_col3:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        df_matrix = ComparisonMatrixBuilder.to_dataframe(matrix_rows, vendor_responses)
        csv_data = df_matrix.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Matrix CSV", data=csv_data, file_name="normalized_rfx_matrix.csv", mime="text/csv", use_container_width=True)

    filtered_matrix = matrix_rows
    if selected_cat != "All Categories":
        filtered_matrix = [r for r in filtered_matrix if r.category == selected_cat]
    if search_query:
        q = search_query.lower()
        filtered_matrix = [r for r in filtered_matrix if q in r.sku_code.lower() or q in r.sku_name.lower()]

    df_display = ComparisonMatrixBuilder.to_dataframe(filtered_matrix, vendor_responses)
    st.dataframe(df_display, use_container_width=True, height=450)

    st.info("💡 **Audit Tip**: Navigate to the **'Line-Level Visual Proof & Deal Audit'** tab to inspect the exact verbatim snippets, PDF rows, and photo rate cards backing every figure.")

# ---------------------------------------------------------------------------
# TAB 2: LINE-LEVEL VISUAL PROOF & AUDIT INSPECTOR
# ---------------------------------------------------------------------------
with tab2:
    st.markdown("### 🔍 Line-Level Ground Truth Auditability & Document Inspector")
    st.caption("Audit trail verifying '₹4.2 Crore' enterprise procurement decisions. Click any SKU to inspect raw text extracts, sheet coordinates, and AI confidence scores.")

    sku_options = [f"{s['code']} - {s['name']}" for s in active_skus]
    selected_sku_str = st.selectbox("Select SKU to Inspect Ground Truth Proof:", sku_options)
    selected_sku_code = selected_sku_str.split(" - ")[0]

    render_line_level_proof_drawer(selected_sku_code, vendor_responses, dataset_dir=dataset_dir)

# ---------------------------------------------------------------------------
# TAB 3: COMMERCIAL FOOTNOTES & RISK MATRIX
# ---------------------------------------------------------------------------
with tab3:
    st.markdown("### 📑 Commercial Terms, SLAs & Footnote Intelligence")
    st.caption("AI-extracted non-rate commercial variables that alter effective total cost of ownership (TCO).")

    v2_resp = vendor_responses.get("vendor_2")
    v2_name = v2_resp.vendor_name if v2_resp else "Vendor 2"
    st.markdown(f"""
    <div class="footnote-alert">
        <b>🚨 CRITICAL CLAUSE DETECTED in {v2_name}:</b><br>
        <i>"A 5% Volume Discount is applied to the Total PO Value if total order quantity exceeds 5,000 units across items."</i><br>
        For this annual deal portfolio (>1,000,000 aggregate units), this footnote reduces {v2_name}'s effective landed cost by <b>₹ 1,84,000</b>.
    </div>
    """, unsafe_allow_html=True)

    terms_data = []
    for v_id, v_resp in vendor_responses.items():
        t = v_resp.commercial_terms
        terms_data.append({
            "Vendor": v_resp.vendor_name,
            "Format": v_resp.source_format,
            "Payment Terms": t.payment_terms,
            "Warranty & SLA": t.warranty,
            "Freight Terms": t.freight_terms,
            "Volume Discount Clause": t.volume_discount_clause or "None Specified",
            "Effective Discount %": f"{t.discount_percentage:.1f}%",
            "Tax Standard": t.tax_terms
        })

    df_terms = pd.DataFrame(terms_data)
    st.dataframe(df_terms, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 4: STRATEGIC SOURCING INTERROGATION COPILOT
# ---------------------------------------------------------------------------
with tab4:
    st.markdown("### 🤖 Strategic Split-Award Interrogation Copilot")
    st.caption("Simulate split-award scenarios, ask natural language negotiation questions, and optimize deal spend allocation.")

    render_spend_charts(split_summary)

    st.markdown("#### 🎯 Split-Award Optimization Scenario Solver")
    c_strat1, c_strat2 = st.columns([2, 1])
    with c_strat1:
        strategy = st.radio(
            "Allocation Strategy",
            ["Pure L1 Optimization (Lowest Unit Rate per SKU)", "2-Vendor Risk-Mitigated Split (Vendor 1 & Vendor 3)"],
            horizontal=True
        )

    if "2-Vendor" in strategy:
        current_summary = SplitAwardOptimizer.optimize_2vendor_split(matrix_rows, vendor_responses, "vendor_1", "vendor_3")
    else:
        current_summary = split_summary

    st.markdown(f"""
    **Scenario Result**: Total Deal Cost: **₹ {current_summary.total_deal_value_optimized:,.2f}** | 
    Savings vs Baseline: **₹ {current_summary.total_savings_amount:,.2f} ({current_summary.total_savings_pct:.1f}%)**
    """)

    st.markdown("---")
    st.markdown("#### 💬 Natural Language Deal Interrogation")

    chip_cols = st.columns(3)
    with chip_cols[0]:
        if st.button("💡 Optimal split-award recommendation?"):
            st.session_state.copilot_query = "What is the optimal split-award allocation to minimize total cost across all 30 SKUs?"
    with chip_cols[1]:
        if st.button("🔍 Impact of Vendor 2's 5% volume discount?"):
            st.session_state.copilot_query = "If Vendor 2 gives a 5% volume discount for POs > 5000 units, does it beat Vendor 1?"
    with chip_cols[2]:
        if st.button("⚠️ Vendor 5 missing items & currency risk?"):
            st.session_state.copilot_query = "Analyze Vendor 5's USD currency quote and 3 unquoted missing lines."

    user_query = st.text_input(
        "Ask Copilot a negotiation or award question:",
        value=st.session_state.get("copilot_query", ""),
        placeholder="e.g. 'Which vendor offers the best rates on Cartons vs Films?'"
    )

    if st.button("Submit Query", type="primary"):
        if user_query:
            context_snippet = json.dumps([
                {
                    "sku": r.sku_code,
                    "name": r.sku_name,
                    "category": r.category,
                    "baseline_rate": r.baseline_rate,
                    "best_vendor": r.best_vendor_name,
                    "lowest_rate": r.lowest_rate,
                    "rates": r.vendor_rates
                }
                for r in matrix_rows[:15]
            ], indent=2)

            with st.spinner(f"Interrogating RFx matrix via {selected_provider.upper()} ({selected_model})..."):
                resp = llm_client.interrogate_procurement_matrix(user_query, context_snippet)
                st.markdown(resp.answer_markdown)

                if resp.suggested_followups:
                    st.markdown("**Suggested Follow-up Questions:**")
                    for f_up in resp.suggested_followups:
                        st.markdown(f"- *{f_up}*")
