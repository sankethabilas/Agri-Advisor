# Agri-Advisor Backend and UI Setup

This guide explains which packages to install, how to start the FastAPI backend, how to start the Streamlit UI, and how the two processes communicate.

## 1. Requirements

- Windows PowerShell
- Python 3.10 or newer
- The repository folder: `C:\xampp\htdocs\Git_hub\Agri-Advisor`
- Internet access for weather, translation, and optional LLM services

## 2. Create the environment

From the repository root:

```powershell
cd C:\xampp\htdocs\Git_hub\Agri-Advisor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The main libraries installed by `requirements.txt` are:

| Library                 | Purpose                                         |
| ----------------------- | ----------------------------------------------- |
| `fastapi`               | Backend HTTP API                                |
| `uvicorn`               | Runs the FastAPI server                         |
| `streamlit`             | Frontend web UI                                 |
| `requests`              | UI-to-backend HTTP calls                        |
| `python-jose`           | JWT authentication                              |
| `chromadb`              | Knowledge-base vector storage                   |
| `sentence-transformers` | RAG embeddings; required for grounded retrieval |
| `spacy`                 | NLP processing                                  |
| `transformers`          | NLP/model support                               |
| `groq`                  | Optional LLM provider client                    |
| `python-dotenv`         | Loads environment variables                     |
| `pytest`                | Automated tests                                 |

If the RAG service reports `No module named 'sentence_transformers'`, activate `.venv` and rerun the install command. Confirm the active interpreter with `python -c "import sentence_transformers; print(sentence_transformers.__version__)"`.

## 3. Environment variables

Create a `.env` file in the repository root when using external services:

```dotenv
APP_ENV=development
JWT_SECRET_KEY=replace-with-a-long-random-development-secret
AUTH_DATABASE_PATH=data/users.sqlite3
OPENWEATHER_API_KEY=your-weather-key
GROQ_API_KEY=your-llm-key
CORS_ALLOWED_ORIGINS=http://localhost:8501
```

Do not commit `.env` or real API keys. The backend can start in degraded/offline mode when optional weather, LLM, or RAG services are unavailable, but the advisory may contain a service update instead of live information.

## 4. Start the backend

Open PowerShell 1:

```powershell
cd C:\xampp\htdocs\Git_hub\Agri-Advisor
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn orchestrator.main:app --reload --host 127.0.0.1 --port 8000
```

The backend is available at:

- API root: `http://127.0.0.1:8000/`
- Health check: `http://127.0.0.1:8000/api/health`
- Interactive API docs: `http://127.0.0.1:8000/docs`

Check it from another PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

The backend is one FastAPI process. Disease, weather, crop, RAG, authentication, and orchestration routes are exposed by `orchestrator.main`; separate agent servers are not required for the normal local flow.

## 5. Start the UI

Open PowerShell 2 and leave the backend running:

```powershell
cd C:\xampp\htdocs\Git_hub\Agri-Advisor
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
streamlit run ui/app.py --server.port 8501
```

Open `http://localhost:8501` in a browser.

The `PYTHONPATH` line matters when launching `ui/app.py` directly. It makes project packages such as `utils`, `ui`, `agents`, and `orchestrator` importable. Without it, Python can raise `ModuleNotFoundError: No module named 'utils'`.

## 6. How the UI connects to the backend

The UI uses `ui/api_client.py` and sends requests to `http://localhost:8000`:

1. Register: `POST /api/auth/register`
2. Login: `POST /api/auth/login`
3. Ask a question: `POST /api/orchestrator/process`
4. Submit feedback: `POST /api/feedback`

After login, the UI stores the JWT in Streamlit session state and sends it as:

```text
Authorization: Bearer <access-token>
```

The backend checks that the JWT user matches the `user_id` in the query payload. The UI keeps the returned `metadata.session_id` for follow-up questions.

## 7. Run tests

From the repository root with the virtual environment active:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -q
```

Run the focused API and resilience tests:

```powershell
python -m pytest -q tests/test_api_contract_t29.py tests/test_resilience_t25.py tests/test_responsible_ai_t26.py
```

## 8. Common problems

### `ModuleNotFoundError: No module named 'utils'`

Run the UI from the repository root and set `PYTHONPATH` as shown above. The app also now inserts the repository root before importing project-local modules.

### `Connection refused` from the UI

The backend is not running on port 8000. Start Uvicorn first, then refresh the Streamlit page.

### `sentence_transformers` is missing

Install the requirements inside the active virtual environment, then restart Uvicorn. The RAG agent is loaded during advisory processing and health checks.

### Port already in use

Use another backend port only if you also update `ui/config.py` (`API_BASE_URL`). The normal ports are backend `8000` and UI `8501`.
