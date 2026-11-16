import streamlit as st

from frontend.utils import API_URL, call_api


def page_status():
    st.title("System Status")
    for label, path in [("Backend", "/health"), ("Database", "/health/db")]:
        try:
            response = call_api(path)
            online = response.get("status") == "ok"
        except Exception:
            online = False
        icon = "🟢" if online else "🔴"
        state = "Online" if online else "Offline"
        st.write(f"{icon} **{label}:** {state}")

    if st.button(" Refresh"):
        st.rerun()
    st.caption(f"Backend: {API_URL}")
