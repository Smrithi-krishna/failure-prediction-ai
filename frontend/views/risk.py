import json
from urllib.error import HTTPError, URLError

import streamlit as st

from frontend.utils import call_api

# Endpoints from the Swagger page (Milestone 2).
# COMBINED_PATH matches routers/assessments.py. Set it to None to use the three separate endpoints below.
COMBINED_PATH = "/projects/{id}/assessment"
RISK_PATH = "/api/projects/{id}/risk-assessment"
SWOT_PATH = "/api/projects/{id}/swot"
FEASIBILITY_PATH = "/api/projects/{id}/feasibility"

LEVEL_COLORS = {"low": "#16a34a", "medium": "#f59e0b", "high": "#dc2626", "unknown": "#6b7280"}
VERDICT_LABELS = {
    "feasible": ("Feasible", "#16a34a"),
    "feasible_with_conditions": ("Feasible with conditions", "#f59e0b"),
    "not_feasible": ("Not feasible", "#dc2626"),
    "insufficient_information": ("Insufficient information", "#6b7280"),
}
SWOT_BOXES = [
    ("strengths", "Strengths", "#dcfce7", "#166534"),
    ("weaknesses", "Weaknesses", "#fee2e2", "#991b1b"),
    ("opportunities", "Opportunities", "#dbeafe", "#1e40af"),
    ("threats", "Threats", "#fef3c7", "#92400e"),
]


def _detail(error: HTTPError) -> str:
    try:
        detail = json.loads(error.read().decode("utf-8")).get("detail", "Request failed")
        return detail if isinstance(detail, str) else json.dumps(detail)
    except (ValueError, UnicodeDecodeError, AttributeError):
        return "Request failed"


def _call(path, method, project_id):
    return call_api(path.format(id=project_id), method)


def _normalize(risk, swot, feas, combined=None):
    """Return the AssessmentResult shape from schemas.py."""
    if combined is not None:
        return combined.get("result", combined)
    return {
        "risk": risk or {},
        "swot": swot or {},
        "feasibility": feas or {},
        "missing_information": (risk or {}).get("missing_information", [])
        + (feas or {}).get("missing_information", []),
        "assumptions": (risk or {}).get("assumptions", []) + (feas or {}).get("assumptions", []),
    }


def _fetch(project_id, method):
    """method is 'POST' (generate) or 'GET' (latest)."""
    if COMBINED_PATH:
        response = _call(COMBINED_PATH, method, project_id)
        if method == "POST" and not (isinstance(response, dict) and "result" in response):
            response = _call(COMBINED_PATH, "GET", project_id)
        return _normalize(None, None, None, response)
    return _normalize(
        _call(RISK_PATH, method, project_id),
        _call(SWOT_PATH, method, project_id),
        _call(FEASIBILITY_PATH, method, project_id),
    )


def _card(title, body_html, bg="#f8fafc", fg="#0f172a"):
    st.markdown(
        f"<div style='background:{bg};color:{fg};padding:14px 16px;border-radius:10px;"
        f"height:100%'><b>{title}</b><ul style='margin:6px 0 0 18px;padding:0'>{body_html}</ul></div>",
        unsafe_allow_html=True,
    )


def _items(values):
    values = values or []
    if not values:
        return "<li>No data</li>"
    return "".join(f"<li>{v}</li>" for v in values)


def show_assessment(result: dict):
    risk = result.get("risk", {})
    swot = result.get("swot", {})
    feas = result.get("feasibility", {})

    # ---- Risk ----
    st.subheader("Risk Assessment")
    score = risk.get("score")
    level = (risk.get("level") or "unknown").lower()
    color = LEVEL_COLORS.get(level, LEVEL_COLORS["unknown"])
    col1, col2 = st.columns([1, 2])
    with col1:
        score_text = "N/A" if score is None else f"{score:.0f}"
        st.markdown(
            f"<div style='text-align:center;padding:18px;border:2px solid {color};border-radius:12px'>"
            f"<div style='font-size:14px'>Overall Risk Score</div>"
            f"<div style='font-size:52px;font-weight:700;color:{color}'>{score_text}</div>"
            f"<div style='font-weight:700;color:{color}'>{level.upper()} RISK</div></div>",
            unsafe_allow_html=True,
        )
        if score is not None:
            st.progress(min(max(score / 100, 0.0), 1.0))
    with col2:
        if risk.get("explanation"):
            st.write(risk["explanation"])
        st.markdown("**Key risk factors**")
        for factor in risk.get("factors", []) or ["No risk factors returned"]:
            st.markdown(f"- {factor}")

    # ---- SWOT ----
    st.subheader("SWOT Analysis")
    row1 = st.columns(2)
    row2 = st.columns(2)
    for (key, label, bg, fg), col in zip(SWOT_BOXES, row1 + row2):
        with col:
            _card(label, _items(swot.get(key)), bg, fg)
            st.write("")

    # ---- Feasibility ----
    st.subheader("Project Feasibility")
    verdict_label, verdict_color = VERDICT_LABELS.get(
        feas.get("verdict"), ("Not available", "#6b7280")
    )
    fcol1, fcol2 = st.columns([1, 2])
    with fcol1:
        fscore = feas.get("score")
        st.markdown(
            f"<div style='text-align:center;padding:18px;border:2px solid {verdict_color};border-radius:12px'>"
            f"<div style='font-size:14px'>Feasibility Score</div>"
            f"<div style='font-size:52px;font-weight:700;color:{verdict_color}'>"
            f"{'N/A' if fscore is None else f'{fscore:.0f}%'}</div>"
            f"<div style='font-weight:700;color:{verdict_color}'>{verdict_label}</div></div>",
            unsafe_allow_html=True,
        )
        if fscore is not None:
            st.progress(min(max(fscore / 100, 0.0), 1.0))
    with fcol2:
        if feas.get("explanation"):
            st.write(feas["explanation"])
        st.markdown("**Constraints**")
        for constraint in feas.get("constraints", []) or ["No constraints returned"]:
            st.markdown(f"- {constraint}")

    # ---- Missing info / assumptions ----
    left, right = st.columns(2)
    with left:
        with st.expander("Missing information", expanded=bool(result.get("missing_information"))):
            for item in result.get("missing_information", []) or ["None"]:
                st.markdown(f"- {item}")
    with right:
        with st.expander("Assumptions"):
            for item in result.get("assumptions", []) or ["None"]:
                st.markdown(f"- {item}")


def page_risk():
    st.title("Risk, SWOT & Feasibility")

    default_id = st.session_state.get("current_project_id") or 1
    project_id = st.number_input("Project ID", min_value=1, step=1, value=int(default_id))
    if st.session_state.get("current_project_name"):
        st.caption(f"Last submitted: {st.session_state['current_project_name']}")

    col_a, col_b = st.columns(2)
    generate = col_a.button("Generate assessment", type="primary")
    load_latest = col_b.button("Load latest saved")
    if not (generate or load_latest):
        return

    method = "POST" if generate else "GET"
    spinner_text = "Generating assessment — this may take a few minutes..." if generate else "Loading..."
    try:
        with st.spinner(spinner_text):
            result = _fetch(int(project_id), method)
    except HTTPError as error:
        if error.code == 404 and not generate:
            st.warning("No saved assessment for this project yet. Click Generate assessment.")
        else:
            st.error(f"Backend error {error.code}: {_detail(error)}")
        return
    except TimeoutError:
        st.error("The request timed out. The backend may still be processing; try Load latest saved.")
        return
    except URLError:
        st.error("Could not reach the backend.")
        return
    except json.JSONDecodeError:
        st.error("The backend returned an invalid JSON response.")
        return

    show_assessment(result)
