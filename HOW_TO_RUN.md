# How to Run Agri-Advisor

This document provides complete, step-by-step instructions for setting up, configuring, running, and testing the **Agri-Advisor** multi-agent smart farming advisory system on your local machine.

---

## 📋 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Setup & Virtual Environment](#2-project-setup--virtual-environment)
3. [Environment Variables Configuration](#3-environment-variables-configuration)
4. [Knowledge Base Indexing (ChromaDB)](#4-knowledge-base-indexing-chromadb)
5. [Verify Environment Setup](#5-verify-environment-setup)
6. [Starting the Application](#6-starting-the-application)
   - [Step 1: Start Backend (FastAPI)](#step-1-start-the-fastapi-backend)
   - [Step 2: Start Frontend (Streamlit)](#step-2-start-the-streamlit-ui)
7. [Using the Application](#7-using-the-application)
8. [Running Automated Tests](#8-running-automated-tests)
9. [Troubleshooting & Common Issues](#9-troubleshooting--common-issues)

---

## 1. Prerequisites

Before starting, ensure you have the following installed on your system:

- **Python**: Version `3.10` or higher (verify with `python --version` or `python3 --version`)
- **Git**: For cloning the repository and branch management
- **Operating System**: Windows (PowerShell), macOS, or Linux
- **Internet Access**: Required for weather data (OpenWeatherMap), external LLM calls (Groq/OpenAI), and language translation. *(Offline rule-based fallback is available if internet is degraded)*

---

## 2. Project Setup & Virtual Environment

### Step 2.1: Clone or Navigate to the Repository

```bash
git clone https://github.com/sankethabilas/Agri-Advisor.git
cd Agri-Advisor
```

### Step 2.2: Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell restricts scripts execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2.3: Upgrade Pip and Install Dependencies

With the virtual environment activated:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2.4: Download spaCy Language Model

```bash
python -m spacy download en_core_web_sm
```

---

## 3. Environment Variables Configuration

Create a `.env` file in the root directory by copying `.env.example`:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

### Key Configuration Variables in `.env`:

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `APP_ENV` | Environment mode (`development` or `production`) | `development` |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key for live weather & risk forecasts | `your-openweather-key` |
| `OPENWEATHER_CITY` | Default city/region for weather data | `Colombo` |
| `GROQ_API_KEY` | Groq API key for high-speed LLM inference | `your-groq-key` |
| `GROQ_MODEL` | Groq model identifier | `llama-3.1-8b-instant` |
| `OPENAI_API_KEY` | Optional fallback OpenAI API key | *(optional)* |
| `JWT_SECRET_KEY` | Secret key for JWT user authentication | `your-secure-random-secret` |
| `JWT_EXPIRY_MINUTES` | Token expiration duration | `30` |
| `AUTH_DATABASE_PATH` | Path to SQLite user store | `data/users.sqlite3` |
| `CORS_ALLOWED_ORIGINS` | Permitted frontend origins | `http://localhost:8501,https://localhost:8501` |

> [!NOTE]
> The backend supports graceful offline/degraded mode. If API keys are absent, fallback heuristic responses will be served.

---

## 4. Knowledge Base Indexing (ChromaDB)

Agri-Advisor uses ChromaDB vector store with Sentence-Transformers (`all-MiniLM-L6-v2`) to retrieve grounded agricultural knowledge (preventing hallucinations).

Generate or update the vector embeddings index by running:

```bash
python scripts/index_knowledge_base.py
```

---

## 5. Verify Environment Setup

Run the built-in diagnostic tool to verify all libraries, models, and APIs are ready:

```bash
python scripts/verify_environment.py
```

*To check only local packages and models without making live API calls:*
```bash
python scripts/verify_environment.py --skip-apis
```

---

## 6. Starting the Application

The application consists of two services:
1. **Backend Orchestrator API (FastAPI)** running on `http://127.0.0.1:8000`
2. **Frontend UI (Streamlit)** running on `http://localhost:8501`

### Step 1: Start the FastAPI Backend

Open your **first terminal window**:

**Windows (PowerShell):**
```powershell
cd Agri-Advisor
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn orchestrator.main:app --reload --host 127.0.0.1 --port 8000
```

**macOS / Linux:**
```bash
cd Agri-Advisor
source .venv/bin/activate
export PYTHONPATH=$(pwd)
python -m uvicorn orchestrator.main:app --reload --host 127.0.0.1 --port 8000
```

#### Backend Endpoints:
- **API Root**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### Step 2: Start the Streamlit UI

Open a **second terminal window** (keep the backend terminal running):

**Windows (PowerShell):**
```powershell
cd Agri-Advisor
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
streamlit run ui/app.py --server.port 8501
```

**macOS / Linux:**
```bash
cd Agri-Advisor
source .venv/bin/activate
export PYTHONPATH=$(pwd)
streamlit run ui/app.py --server.port 8501
```

The web interface will automatically open in your browser at:
👉 **[http://localhost:8501](http://localhost:8501)**

---

## 7. Using the Application

1. **Authentication**:
   - Navigate to the **Register** tab to create a new farmer profile.
   - Switch to **Login** to sign in and obtain a secure session token.
2. **Consultation / Chat**:
   - Ask crop management, disease diagnosis, or weather advisory queries in **English**, **Sinhala (සිංහල)**, or **Tamil (தமிழ்)**.
   - Example query: *"My paddy leaves have brown spots and drying tips. What disease is this and how can I treat it?"*
3. **Multi-turn Advisory**:
   - Ask follow-up questions; session context and prior entity recommendations are automatically preserved.
4. **Feedback**:
   - Submit ratings and comments on generated recommendations to support continuous system evaluation.

---

## 8. Running Automated Tests

Run the complete test suite to verify orchestrator, specialist agents, security, and API contracts:

```bash
# Run all tests
python -m pytest -v

# Run fast summary mode
python -m pytest -q

# Run specific integration and contract tests
python -m pytest -v tests/test_api_contract_t29.py tests/test_e2e_integration_t22.py tests/test_resilience_t25.py
```

---

## 9. Troubleshooting & Common Issues

### 1. `ModuleNotFoundError: No module named 'utils'` (or `orchestrator`, `agents`)
- **Cause**: Python does not have the repository root in its module search path.
- **Fix**: Set `PYTHONPATH` before launching:
  - PowerShell: `$env:PYTHONPATH = (Get-Location).Path`
  - Linux/macOS: `export PYTHONPATH=$(pwd)`

### 2. `No module named 'sentence_transformers'` or `spacy`
- **Cause**: Packages installed globally or virtual environment not activated.
- **Fix**: Activate `.venv` (`.\.venv\Scripts\Activate.ps1` or `source .venv/bin/activate`) and run:
  ```bash
  pip install -r requirements.txt
  python -m spacy download en_core_web_sm
  ```

### 3. `Connection refused` in Streamlit UI
- **Cause**: Backend server is not running or crashed on startup.
- **Fix**: Check your backend terminal. Ensure Uvicorn is actively listening on `http://127.0.0.1:8000`. Test via browser or `curl http://127.0.0.1:8000/api/health`.

### 4. `Port 8000` or `Port 8501` already in use
- **Cause**: Another process is occupying the default port.
- **Fix**:
  - Kill the occupying process, or
  - For backend: run on another port (e.g. `--port 8001`) and update `API_BASE_URL` in `ui/config.py`.
  - For UI: specify another port (e.g. `--server.port 8502`).

### 5. OpenWeather or Groq Rate Limits / Missing Keys
- **Behavior**: The application falls back gracefully to localized heuristic and rule-based advisories.
- **Fix**: Provide valid API keys in `.env` and restart the backend server.
