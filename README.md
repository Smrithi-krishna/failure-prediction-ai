# Failure Prediction AI - VentureAnalyzer

Failure Prediction AI is a project analyzer. It collects a structured project profile, saves it to PostgreSQL, and uses Gemini to generate a market and competitor analysis. The Streamlit dashboard presents the analysis and lets teammates revisit saved projects.

The current app focuses on market context, opportunities, challenges, missing information, assumptions, and confidence. It does not calculate a numerical risk score. Live competitor search is not configured, so competitor results are marked insufficient and user-entered competitors are not treated as verified.

## How the app works

1. A user fills out the project form in Streamlit and submits it.
2. Streamlit sends the project fields to FastAPI at `POST /projects`.
3. FastAPI validates the request with Pydantic and stores the project in PostgreSQL.
4. Streamlit requests `POST /projects/{project_id}/market-analysis`.
5. The API loads the saved project, builds the existing analysis prompt, and calls Gemini using JSON response mode.
6. FastAPI validates the generated response, stores the analysis in PostgreSQL, and returns it to Streamlit for display.
7. Later, the **My Projects** page loads saved projects and retrieves the latest analysis with `GET /projects/{project_id}/market-analysis`.

Gemini currently uses `gemini-3.5-flash-lite`, API version `v1beta`, and a 12-second SDK timeout. Analysis generation can fail if the upstream service is unavailable or slow; failed analyses can be manually retried from **My Projects**.

## Project layout

```text
failure-prediction-ai/
|-- main.py                      # FastAPI app, startup, health checks, router registration
|-- database.py                  # PostgreSQL engine and sessions
|-- models.py                    # SQLAlchemy tables
|-- schemas.py                   # Pydantic request and response schemas
|-- routers/
|   |-- projects.py              # Project submission and retrieval
|   `-- analysis.py              # Analysis generation and retrieval
|-- services/
|   `-- gemini_service.py        # Gemini client and production prompt
|-- frontend/
|   |-- app.py                   # Streamlit navigation
|   |-- utils.py                 # API client and shared analysis display
|   `-- views/
|       |-- submit.py            # Project form and analysis generation flow
|       |-- projects.py          # Saved projects and analysis retrieval
|       `-- status.py            # Backend and database status
|-- requirements.txt
|-- .env.example
`-- test_foundation.py
```

## Prerequisites

- Windows with PowerShell
- Python 3.10 or newer
- PostgreSQL running locally or reachable from your machine
- A Gemini API key with access to `gemini-3.5-flash-lite`

## Set up a local environment

Open PowerShell in the repository folder and create the virtual environment:

```powershell
py -3 -m venv .venv
```

Install the project dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set:

```dotenv
DATABASE_URL=postgresql+psycopg2://<username>:<password>@localhost:5432/<database>
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_API_KEY=<your-gemini-api-key>
```

Replace the placeholders with your PostgreSQL credentials and API key. If your password contains URL-reserved characters, URL-encode it in `DATABASE_URL`. Keep `.env` private; it is ignored by Git. Do not paste credentials into source files or commit them.

Create the PostgreSQL database and user before starting the API. On startup, the API creates its application tables and adds missing non-primary-key columns where needed. It does not reset the database.

## Run the application

Open two PowerShell terminals from the repository root.

**Terminal 1 - FastAPI backend:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive API documentation is at `http://127.0.0.1:8000/docs`.

**Terminal 2 - Streamlit frontend:**

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py
```

Streamlit prints the local URL when it starts, typically `http://localhost:8501`. The frontend uses `http://127.0.0.1:8000` by default. To use another backend address, set `API_URL` in the environment before starting Streamlit.

## Using the app

- **Submit Project:** enter the project details you know, mark unknowns where offered, and submit. The app saves the project first, then asks Gemini to generate its analysis.
- **My Projects:** browse saved project records, view their latest analysis, or manually request analysis again.
- **System Status:** check the backend and PostgreSQL health endpoints.

The form preserves separate statuses for unknown budget, runway, and competitor information. Competitor names and URLs entered by the user are retained with the project, but they are not independently verified by the current backend.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Basic backend response |
| `GET` | `/health` | Backend health |
| `GET` | `/health/db` | PostgreSQL connectivity |
| `GET` | `/ready` | Database readiness |
| `POST` | `/projects` | Validate and save a project |
| `GET` | `/projects` | List saved projects |
| `GET` | `/projects/{project_id}` | Retrieve one project |
| `POST` | `/projects/{project_id}/market-analysis` | Generate and save an analysis |
| `GET` | `/projects/{project_id}/market-analysis` | Retrieve the latest saved analysis |

## Tests and checks

Run the basic test suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

The optional PostgreSQL integration test requires a separate `TEST_DATABASE_URL`. It creates a temporary test project in that database and removes it afterward. Do not point `TEST_DATABASE_URL` at a database containing user data.

## Troubleshooting

- **Backend fails at startup:** confirm PostgreSQL is running and `DATABASE_URL` is correct.
- **`/health` works but `/health/db` fails:** check PostgreSQL availability and credentials.
- **Gemini returns 502 or 504:** check that the API key is valid and the upstream Gemini service is available. The project remains saved if analysis generation fails; retry manually from **My Projects**.
- **Streamlit cannot reach FastAPI:** start the backend and confirm `API_URL` points to it.

