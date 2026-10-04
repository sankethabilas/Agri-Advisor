# How to Run Agri-Advisor

See the root guide at [HOW_TO_RUN.md](file:///c:/Users/USER/Desktop/agri-advisor/Agri-Advisor/HOW_TO_RUN.md) or follow the quick reference below.

---

## Quick Reference

### 1. Prerequisites & Environment Setup

```powershell
# In Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
Copy-Item .env.example .env
```

### 2. Knowledge Base Indexing

```powershell
python scripts/index_knowledge_base.py
```

### 3. Verify Environment

```powershell
python scripts/verify_environment.py --skip-apis
```

### 4. Start Backend (Terminal 1)

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn orchestrator.main:app --reload --host 127.0.0.1 --port 8000
```
- API Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/health`

### 5. Start Frontend (Terminal 2)

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
streamlit run ui/app.py --server.port 8501
```
- UI: `http://localhost:8501`

### 6. Run Test Suite

```powershell
python -m pytest -v
```

For full troubleshooting and details, refer to [HOW_TO_RUN.md](file:///c:/Users/USER/Desktop/agri-advisor/Agri-Advisor/HOW_TO_RUN.md) and [backend_and_ui_setup.md](file:///c:/Users/USER/Desktop/agri-advisor/Agri-Advisor/docs/backend_and_ui_setup.md).
