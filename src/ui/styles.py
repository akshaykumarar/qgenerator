"""Enterprise B2B Slate theme styles and CSS tokens for Intelligent Procurement."""

SLATE_CSS = """
<style>
/* -------------------------------------------------------------
   Enterprise B2B Theme: Design System Tokens
   Primary Navy: #002B49
   Accent Teal:  #00A88F
   Alert Amber:  #D97706 / #FFC107
   Light BG:     #F8F9FA
------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* Main Container Adjustments */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 96%;
}

/* Header Banner */
.portal-header {
    background: linear-gradient(135deg, #002B49 0%, #004370 100%);
    color: #FFFFFF;
    padding: 1.25rem 1.75rem;
    border-radius: 10px;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 12px rgba(0, 43, 73, 0.12);
    border-left: 6px solid #00A88F;
}

.portal-title {
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 0;
    color: #FFFFFF !important;
}

.portal-subtitle {
    font-size: 0.875rem;
    color: #A0C4DE;
    margin: 0.25rem 0 0 0;
}

/* Status Pill */
.status-badge-active {
    background-color: rgba(0, 168, 143, 0.18);
    color: #00E5C0;
    border: 1px solid #00A88F;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
}

.status-dot {
    width: 8px;
    height: 8px;
    background-color: #00E5C0;
    border-radius: 50%;
    animation: pulse 1.8s infinite;
}

@keyframes pulse {
    0% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 8px #00E5C0; }
    100% { transform: scale(0.95); opacity: 0.8; }
}

/* KPI Metric Cards */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 1.1rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    border-top: 3px solid #002B49;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(0, 43, 73, 0.08);
}

.metric-card.accent {
    border-top-color: #00A88F;
}

.metric-card.warning {
    border-top-color: #D97706;
}

.metric-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    margin-bottom: 0.4rem;
}

.metric-value {
    font-size: 1.55rem;
    font-weight: 800;
    color: #002B49;
    letter-spacing: -0.02em;
}

.metric-sub {
    font-size: 0.8rem;
    color: #00A88F;
    font-weight: 600;
    margin-top: 0.3rem;
}

/* File Badges */
.file-badge-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.75rem;
    margin-top: 0.75rem;
}

.file-badge-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    border-left: 4px solid #002B49;
}

.file-badge-card.excel { border-left-color: #107C41; }
.file-badge-card.pdf   { border-left-color: #D9383A; }
.file-badge-card.word  { border-left-color: #185ABD; }
.file-badge-card.image { border-left-color: #8E44AD; }
.file-badge-card.email { border-left-color: #E67E22; }

.file-badge-info h5 {
    margin: 0;
    font-size: 0.82rem;
    font-weight: 700;
    color: #1E293B;
}

.file-badge-info p {
    margin: 0.15rem 0 0 0;
    font-size: 0.72rem;
    color: #64748B;
}

/* Audit Proof Box */
.proof-box {
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #00A88F;
    border-radius: 6px;
    padding: 1rem;
    margin: 0.75rem 0;
}

.proof-title {
    font-weight: 700;
    font-size: 0.85rem;
    color: #002B49;
    display: flex;
    justify-content: space-between;
}

.proof-snippet {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.8rem;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    padding: 0.5rem;
    border-radius: 4px;
    margin: 0.5rem 0;
    color: #0F172A;
}

/* Custom Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    height: 42px;
    white-space: pre-wrap;
    background-color: #FFFFFF;
    border-radius: 6px 6px 0px 0px;
    padding-top: 10px;
    padding-bottom: 10px;
    font-weight: 600;
    color: #475569;
    border: 1px solid #E2E8F0;
}

.stTabs [aria-selected="true"] {
    background-color: #002B49 !important;
    color: #FFFFFF !important;
    border-bottom: 2px solid #00A88F !important;
}

/* Primary buttons */
.stButton > button {
    border-radius: 6px;
    font-weight: 600;
    letter-spacing: -0.01em;
    transition: all 0.2s ease;
}

.stButton > button[kind="primary"] {
    background-color: #00A88F;
    color: #FFFFFF;
    border: none;
}

.stButton > button[kind="primary"]:hover {
    background-color: #008773;
    box-shadow: 0 4px 10px rgba(0, 168, 143, 0.3);
}

/* Footnote callout */
.footnote-alert {
    background-color: #FEF3C7;
    border-left: 4px solid #D97706;
    color: #92400E;
    padding: 0.75rem 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    font-size: 0.85rem;
}
</style>
"""


def get_header_html(model_name: str, api_active: bool) -> str:
    """Generate header banner HTML with status badge."""
    status_text = "AI Pipeline: Active" if api_active else "Local Extraction Mode"
    badge_class = "status-badge-active"

    return f"""
    <div class="portal-header">
        <div>
            <h1 class="portal-title">Autonomous RFx Normalization & Interrogation Engine</h1>
            <p class="portal-subtitle">Enterprise Strategic Procurement Copilot | Multi-Vendor Packaging SKU Intelligence (₹4.2 Cr Portfolio)</p>
        </div>
        <div>
            <span class="{badge_class}">
                <span class="status-dot"></span>
                <span>{status_text}</span>
                <span style="font-size:0.7rem; opacity:0.85; margin-left:4px;">({model_name})</span>
            </span>
        </div>
    </div>
    """
