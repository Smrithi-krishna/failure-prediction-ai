import streamlit as st

from frontend.views.projects import page_projects
from frontend.views.risk import page_risk
from frontend.views.status import page_status
from frontend.views.submit import page_submit

st.set_page_config(
    page_title="VentureAnalyzer AI",
    page_icon="📊",
    layout="wide",
)

# ── Top navigation bar ────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="
        background-color: #1a1a2e;
        padding: 14px 32px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 24px;
    ">
        <div>
            <span style="
                color: white;
                font-size: 1.6rem;
                font-weight: 700;
                letter-spacing: 0.5px;
            ">📊 VentureAnalyzer AI</span>
            <span style="
                color: #adb5bd;
                font-size: 0.85rem;
                margin-left: 14px;
            ">Startup & Project Risk Analyzer</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Navigation buttons ────────────────────────────────────────────────────────
col1, col2, col3, col4, _ = st.columns([1, 1, 1, 1, 5])

with col1:
    if st.button("📝  Submit Project", use_container_width=True):
        st.session_state["page"] = "Submit Project"

with col2:
    if st.button("🛡️  Risk Assessment", use_container_width=True):
        st.session_state["page"] = "Risk Assessment"

with col3:
    if st.button("📁  My Projects", use_container_width=True):
        st.session_state["page"] = "My Projects"

with col4:
    if st.button("🔧  System Status", use_container_width=True):
        st.session_state["page"] = "System Status"

st.divider()

# ── Page routing ──────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "Submit Project"

page = st.session_state["page"]

if page == "Submit Project":
    page_submit()
elif page == "Risk Assessment":
    page_risk()
elif page == "My Projects":
    page_projects()
else:
    page_status()

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#6c757d; font-size:0.8rem;'>"
    "Powered by Gemini</p>",
    unsafe_allow_html=True,
)
