import json
from datetime import datetime
from urllib.error import HTTPError, URLError

import streamlit as st

from frontend.utils import call_api, show_analysis


def page_projects():
    st.title("My Projects")
    st.write("All submitted projects. Click a project to view its latest analysis.")
    try:
        projects = call_api("/projects")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        st.error("Could not load projects.")
        return

    if not projects:
        st.info("No projects submitted yet.")
    else:
        rows = []
        for project in projects:
            submitted = project.get("created_at", "")
            try:
                submitted = datetime.fromisoformat(
                    submitted.replace("Z", "+00:00")
                ).date().isoformat()
            except (ValueError, AttributeError):
                pass
            rows.append({
                "ID": project.get("id"), "Project name": project.get("project_name"),
                "Type": project.get("project_type"), "Industry": project.get("industry"),
                "Submitted": submitted,
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

    selected_id = st.number_input(
        "Enter project ID to view analysis", min_value=1, step=1
    )
    view_col, retry_col = st.columns(2)
    with view_col:
        view_analysis = st.button("View analysis")
    with retry_col:
        retry_analysis = st.button("Generate analysis")

    if view_analysis:
        try:
            result = call_api(f"/projects/{int(selected_id)}/market-analysis")
            if result.get("analysis"):
                selected_project = next(
                    (item for item in projects if item.get("id") == int(selected_id)),
                    {},
                ) if projects else {}
                show_analysis(
                    result["analysis"],
                    project_name=selected_project.get("project_name"),
                    analysis_status=result.get("status", "complete"),
                )
            else:
                st.info("No completed analysis is available. Use Generate analysis to try again.")
        except HTTPError as error:
            if error.code == 404:
                st.error("No analysis found for this project.")
            else:
                st.error("Could not load analysis.")
        except (URLError, TimeoutError, json.JSONDecodeError, KeyError):
            st.error("Could not load analysis.")

    if retry_analysis:
        try:
            result = call_api(
                f"/projects/{int(selected_id)}/market-analysis", "POST"
            )
            selected_project = next(
                (item for item in projects if item.get("id") == int(selected_id)),
                {},
            ) if projects else {}
            show_analysis(
                result["analysis"],
                project_name=selected_project.get("project_name"),
            )
        except HTTPError as error:
            try:
                detail = json.loads(error.read().decode("utf-8")).get("detail", "Request failed")
            except (ValueError, UnicodeDecodeError):
                detail = "Request failed"
            st.error(f"Analysis could not be generated. {detail}")
        except TimeoutError:
            st.error("Analysis could not be generated because the request timed out. Try again later.")
        except (URLError, json.JSONDecodeError, KeyError):
            st.error("Analysis could not be generated. Try again later.")
