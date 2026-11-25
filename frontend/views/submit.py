import json
from urllib.error import HTTPError, URLError

import streamlit as st

from frontend.utils import call_api, show_analysis

UNKNOWN = "Not known yet"


def _error_detail(error: HTTPError) -> str:
    try:
        return json.loads(error.read().decode("utf-8")).get("detail", "Request failed")
    except (ValueError, UnicodeDecodeError, AttributeError):
        return "Request failed"


def page_submit():
    st.title("Submit Your Project")
    st.write("Fill in what you know. Mark anything unknown using the checkboxes.")

    # ---------------- Section 1 ----------------
    st.header("Section 1 — Project Basics")
    project_name = st.text_input("Project name *")
    project_type = st.selectbox(
        "Project type",
        ["Startup", "Business plan", "Hackathon", "College project", "Innovation concept", UNKNOWN],
    )
    description_unknown = st.checkbox("Description not known yet")
    description = UNKNOWN if description_unknown else st.text_area("Description (minimum 50 characters)")
    problem_unknown = st.checkbox("Problem being solved not known yet")
    problem = UNKNOWN if problem_unknown else st.text_area("Problem being solved")
    solution_unknown = st.checkbox("Proposed solution not known yet")
    solution = UNKNOWN if solution_unknown else st.text_area("Proposed solution")

    # ---------------- Section 2 ----------------
    st.header("Section 2 — Market & Customers")
    industry_choice = st.selectbox(
        "Industry / sector",
        ["Technology", "Healthcare", "Education", "Finance", "Agriculture",
         "E-commerce / Retail", "Manufacturing", "Transportation / Logistics",
         "Energy", "Entertainment / Media", "Other", UNKNOWN],
    )
    industry = st.text_input("Specify the industry") if industry_choice == "Other" else industry_choice
    target_customers = st.selectbox(
        "Target customers", ["B2B", "B2C", "B2G", "Internal / Academic", UNKNOWN]
    )
    audience_unknown = st.checkbox("Target audience not known yet")
    audience = UNKNOWN if audience_unknown else st.text_area("Target audience description")
    geographic_scope = st.selectbox(
        "Geographic scope", ["Global", "Country", "Region / State", "City", UNKNOWN]
    )
    location = (
        st.text_input("Location")
        if geographic_scope in {"Country", "Region / State", "City"}
        else None
    )

    # ---------------- Section 3 ----------------
    st.header("Section 3 — Business & Resources")
    business_model = st.selectbox(
        "Business model",
        ["Subscription", "One-time sale", "Marketplace", "Free with ads",
         "Freemium", "Not decided", UNKNOWN],
    )
    budget_status = st.selectbox("Budget", ["Amount", "None", UNKNOWN])
    budget, currency = None, None
    if budget_status == "Amount":
        amount_col, currency_col = st.columns([2, 1])
        with amount_col:
            budget = st.number_input("Budget amount", min_value=0.0, step=100.0)
        with currency_col:
            currency = st.selectbox(
                "Currency", ["Select currency", "USD", "INR", "EUR", "GBP", "Other"]
            )
        if currency == "Select currency":
            currency = None
        elif currency == "Other":
            currency = st.text_input("Enter currency code") or None

    runway_status = st.selectbox("Runway / timeline", ["Enter months", UNKNOWN])
    runway_months = (
        st.number_input("Months", min_value=0, step=1)
        if runway_status == "Enter months"
        else None
    )

    # ---------------- Section 4 ----------------
    st.header("Section 4 — Competitors")
    competitor_choice = st.selectbox(
        "Known competitors", ["Enter competitors", "No known competitors", UNKNOWN]
    )
    competitor_text = (
        st.text_area("One per line: Name | website URL")
        if competitor_choice == "Enter competitors"
        else None
    )

    submitted = st.button("Save and analyze", type="primary")
    if not submitted:
        return

    # ---------------- Parse competitors ----------------
    known_competitors = []
    if competitor_choice == "Enter competitors":
        for line in (competitor_text or "").splitlines():
            name, separator, url = line.partition("|")
            name, url = name.strip(), url.strip()
            if name:
                known_competitors.append(f"{name} ({url})" if separator and url else name)

    # ---------------- Validation ----------------
    errors = []
    if not project_name.strip():
        errors.append("Project name is required")
    if not description_unknown and len(description.strip()) < 50:
        errors.append("Description must be at least 50 characters")
    if not problem_unknown and not problem.strip():
        errors.append("Problem being solved must not be blank")
    if not solution_unknown and not solution.strip():
        errors.append("Proposed solution must not be blank")
    if not audience_unknown and not audience.strip():
        errors.append("Target audience must not be blank")
    if industry_choice == "Other" and not industry.strip():
        errors.append("Specify the industry")
    if location is not None and not location.strip():
        errors.append("Enter the location")
    if budget_status == "Amount" and (budget is None or budget <= 0):
        errors.append("Enter a budget greater than 0, or choose None / Not known yet")
    if budget_status == "Amount" and not currency:
        errors.append("Select or enter a currency for the budget")
    if competitor_choice == "Enter competitors" and not known_competitors:
        errors.append("Enter at least one competitor, or choose another competitor option")
    if errors:
        st.error("Please fix: " + ", ".join(errors))
        return

    submission = {
        "project_name": project_name.strip(), "project_type": project_type,
        "description": description, "problem_being_solved": problem,
        "proposed_solution": solution, "industry": industry,
        "target_customers": target_customers,
        "target_audience_description": audience,
        "geographic_scope": geographic_scope,
        "location": location.strip() if location else None,
        "business_model": business_model, "budget": budget,
        "budget_currency": currency, "budget_status": budget_status,
        "runway_months": int(runway_months) if runway_months is not None else None,
        "runway_status": runway_status, "known_competitors": known_competitors,
        "competitors_status": (
            "unknown" if competitor_choice == UNKNOWN
            else "none" if competitor_choice == "No known competitors"
            else "provided"
        ),
    }

    # ---------------- Save project ----------------
    try:
        with st.spinner("Saving project..."):
            saved = call_api("/projects", "POST", submission)
        project_id = saved.get("id") or saved.get("project_id")
        if project_id is None:
            st.error("Project was saved, but the response did not include a project ID.")
            return
        st.session_state["current_project_id"] = project_id
        st.session_state["current_project_name"] = project_name.strip()
        st.success(f"Project #{project_id} saved.")
    except HTTPError as error:
        st.error(f"Backend error {error.code}: {_error_detail(error)}")
        return
    except TimeoutError:
        st.error("The request timed out. The backend may still be processing.")
        return
    except URLError:
        st.error("Could not reach the backend.")
        return
    except json.JSONDecodeError:
        st.error("The backend returned an invalid JSON response while saving the project.")
        return

    # ---------------- Market analysis ----------------
    try:
        with st.spinner("Generating analysis — this may take a few minutes..."):
            result = call_api(f"/projects/{project_id}/market-analysis", "POST")
        analysis = result.get("analysis", result)
        show_analysis(analysis, project_name=project_name.strip())
        st.info("Next: open the Risk Assessment page to generate risk, SWOT and feasibility.")
    except HTTPError as error:
        st.error(
            f"Project #{project_id} was saved, but analysis could not be generated. "
            f"Backend error {error.code}: {_error_detail(error)} "
            "You can try again later from My Projects."
        )
    except TimeoutError:
        st.error(
            f"Project #{project_id} was saved, but analysis could not be generated "
            "because the request timed out. You can try again later from My Projects."
        )
    except URLError:
        st.error(
            f"Project #{project_id} was saved, but the backend could not generate "
            "the analysis. You can try again later from My Projects."
        )
    except json.JSONDecodeError:
        st.error(
            f"Project #{project_id} was saved, but the backend returned an invalid "
            "analysis response. You can try again later from My Projects."
        )
    except (KeyError, TypeError):
        st.error(
            f"Project #{project_id} was saved, but the backend response did not "
            "include usable analysis data. You can try again later from My Projects."
        )
