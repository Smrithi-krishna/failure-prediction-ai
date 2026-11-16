import html
import json
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")


def call_api(path, method="GET", data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    request = Request(f"{API_URL}{path}", data=body, headers=headers, method=method)
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def confidence_badge(level: str) -> str:
    colors = {"high": "#198754", "medium": "#fd7e14", "low": "#dc3545"}
    label = str(level or "unknown")
    color = colors.get(label.lower(), "#6c757d")
    return (
        f'<span style="background-color:{color};color:white;border-radius:4px;'
        f'padding:3px 9px;font-size:0.78em;font-weight:600">{html.escape(label.title())}</span>'
    )


def status_badge(status: str) -> str:
    colors = {
        "found": "#198754", "complete": "#198754", "partial": "#fd7e14",
        "insufficient": "#6c757d", "pending": "#0d6efd", "failed": "#dc3545",
    }
    label = str(status or "unknown")
    color = colors.get(label.lower(), "#6c757d")
    return (
        f'<span style="background-color:{color};color:white;border-radius:4px;'
        f'padding:3px 9px;font-size:0.78em;font-weight:600">{html.escape(label.title())}</span>'
    )


def _label(key: str) -> str:
    return key.replace("_", " ").strip().title()


def _valid_url(value) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _render_list(items):
    if not items:
        st.caption("None provided")
    elif all(not isinstance(item, dict) for item in items):
        for item in items:
            st.markdown(f"- {item}")
    else:
        for item in items:
            if isinstance(item, dict):
                for key, value in item.items():
                    if value is None or value == "":
                        continue
                    if key in {"source", "source_url", "url"} and _valid_url(value):
                        st.markdown(f"[Source]({value})")
                    elif isinstance(value, (str, int, float, bool)):
                        st.markdown(f"**{_label(key)}:** {value}")
                    elif isinstance(value, list):
                        st.markdown(f"**{_label(key)}**")
                        _render_list(value)
            else:
                st.markdown(f"- {item}")


def show_analysis(analysis: dict, project_name=None, analysis_status="complete"):
    analysis = analysis if isinstance(analysis, dict) else {}
    market = analysis.get("market_analysis") or {}
    competition = analysis.get("competitor_analysis") or {}
    sources = []

    st.title(project_name or f"Project #{analysis.get('project_id', '')}".strip())
    st.caption("Project analysis overview")
    status_col, confidence_col, model_col = st.columns([1, 1, 2])
    with status_col:
        st.markdown("**Status**")
        st.markdown(status_badge(analysis_status), unsafe_allow_html=True)
    with confidence_col:
        st.markdown("**Overall confidence**")
        st.markdown(
            confidence_badge(analysis.get("overall_confidence")),
            unsafe_allow_html=True,
        )
    with model_col:
        st.markdown("**Model**")
        st.write(analysis.get("model") or "Not provided")

    summary = market.get("market_summary")
    if summary:
        with st.container(border=True):
            st.subheader("Executive Summary")
            st.write(summary)

    st.divider()
    left, right = st.columns([1.15, 0.85])
    with left:
        st.header("Market Analysis")
        if market.get("market_summary"):
            st.subheader("Market Overview")
            st.write(market["market_summary"])
        if market.get("target_market_description"):
            st.subheader("Target Customers")
            st.write(market["target_market_description"])

        size = market.get("market_size") or {}
        if any(size.get(key) is not None for key in ("value", "unit", "source", "confidence")):
            st.subheader("Market Size")
            if size.get("value") is not None:
                st.write(f"{size['value']} {size.get('unit') or ''}".strip())
            else:
                st.caption("No market-size estimate provided")
            if size.get("confidence"):
                st.markdown(confidence_badge(size["confidence"]), unsafe_allow_html=True)
            if size.get("source"):
                if _valid_url(size["source"]):
                    st.markdown(f"[View source]({size['source']})")
                    sources.append(("Market size", size["source"]))
                else:
                    st.caption(f"Source: {size['source']}")

        trends = market.get("growth_trends") or []
        if trends:
            st.subheader("Growth Trends")
            for trend in trends:
                with st.container(border=True):
                    if trend.get("trend"):
                        st.markdown(f"**{trend['trend']}**")
                    if trend.get("evidence"):
                        st.write(trend["evidence"])
                    if trend.get("confidence"):
                        st.markdown(confidence_badge(trend["confidence"]), unsafe_allow_html=True)
                    if trend.get("source_url") and _valid_url(trend["source_url"]):
                        st.markdown(f"[Evidence source]({trend['source_url']})")
                        sources.append((trend.get("trend") or "Growth trend", trend["source_url"]))

        opportunities = market.get("opportunities") or []
        if opportunities:
            st.subheader("Growth Opportunities")
            _render_list(opportunities)

        if market.get("data_date_range"):
            st.caption(f"Data period: {market['data_date_range']}")

    with right:
        st.header("Risks & Challenges")
        challenges = market.get("challenges") or []
        if not challenges:
            st.caption("No challenges were provided in this analysis.")
        for challenge in challenges:
            with st.container(border=True):
                if isinstance(challenge, dict):
                    title = challenge.get("challenge") or challenge.get("title")
                    if title:
                        st.markdown(f"**{title}**")
                    for key, value in challenge.items():
                        if key in {"challenge", "title"} or value is None or value == "":
                            continue
                        if key in {"source", "source_url", "url"} and _valid_url(value):
                            st.markdown(f"[Supporting source]({value})")
                            sources.append((title or "Challenge", value))
                        elif key.lower() in {"severity", "impact"}:
                            st.markdown(
                                f'<span style="background:#6c757d;color:white;border-radius:4px;'
                                f'padding:3px 9px;font-size:0.78em">{html.escape(_label(key))}: '
                                f'{html.escape(str(value))}</span>', unsafe_allow_html=True
                            )
                        elif isinstance(value, (str, int, float, bool)):
                            st.markdown(f"**{_label(key)}:** {value}")
                else:
                    st.write(challenge)

        st.header("Competitor Analysis")
        st.markdown(status_badge(competition.get("status")), unsafe_allow_html=True)
        if competition.get("status_reason"):
            st.write(competition["status_reason"])
        competitors = competition.get("competitors") or []
        if not competitors:
            st.info("Insufficient verified competitor information is available.")
        for competitor in competitors:
            with st.container(border=True):
                name = competitor.get("name") or "Competitor"
                if _valid_url(competitor.get("source_url")):
                    st.markdown(f"### [{name}]({competitor['source_url']})")
                    sources.append((name, competitor["source_url"]))
                else:
                    st.markdown(f"### {name}")
                for key in ("description", "positioning", "products_or_services", "strengths", "weaknesses", "gaps"):
                    value = competitor.get(key)
                    if value:
                        st.markdown(f"**{_label(key)}**")
                        _render_list(value if isinstance(value, list) else [value])
                if competitor.get("confidence"):
                    st.markdown(confidence_badge(competitor["confidence"]), unsafe_allow_html=True)
                if "verified_from_search" in competitor:
                    st.caption(
                        "Verified from search" if competitor["verified_from_search"]
                        else "Not verified from search"
                    )

        comparison = competition.get("comparison") or []
        if comparison:
            st.subheader("Competitive Comparison")
            if all(isinstance(row, dict) for row in comparison):
                st.dataframe(comparison, use_container_width=True, hide_index=True)
            else:
                _render_list(comparison)

        for key, heading in (
            ("competitive_advantages", "Competitive Strengths"),
            ("competitive_gaps", "Competitive Gaps"),
        ):
            values = competition.get(key) or []
            if values:
                st.subheader(heading)
                _render_list(values)

    st.divider()
    missing = analysis.get("missing_information") or []
    assumptions = analysis.get("assumptions") or []
    missing_col, assumptions_col = st.columns(2)
    with missing_col:
        st.subheader("Information Needed")
        if missing:
            st.warning("These project details are missing or uncertain.")
            _render_list(missing)
        else:
            st.write("None identified")
    with assumptions_col:
        st.subheader("Assumptions")
        if assumptions:
            st.caption("AI-generated assumptions — validate these before relying on them.")
            _render_list(assumptions)
        else:
            st.write("None identified")

    if sources:
        st.subheader("Sources & Evidence")
        for label, source in sources:
            st.markdown(f"- [{label}]({source})")

    with st.expander("Developer: Raw Analysis JSON", expanded=False):
        st.json(analysis)
