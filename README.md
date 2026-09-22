# Agri-Advisor: Multi-Agent AI System for Smart Farming

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red.svg)](https://streamlit.io/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorStore-purple.svg)](https://www.trychroma.com/)

Agri-Advisor is a conversational multi-agent AI advisory system engineered to bridge the 1:1,500 agriculture extension officer gap for Sri Lankan farmers. Smallholder farmers can describe crop issues in plain language (Sinhala, Tamil, or English) to instantly receive grounded, verified, and personalized agricultural advisories.

---

## 🌾 Project Overview & Architecture

Agri-Advisor follows a modular, microservice-based multi-agent architecture coordinated by a central Orchestrator:

1. **User Interface (`/ui`)**: Conversational web and mobile interface built with Streamlit supporting text/voice input in English, Sinhala, and Tamil.
2. **Orchestrator Agent (`/orchestrator`)**: The hub service handling NLP intent classification, Named Entity Recognition (NER), agent routing, session context, and LLM response synthesis.
3. **Specialist Agents (`/agents`)**:
   - **Disease Agent (`/agents/disease`)**: Performs symptom matching, disease identification, severity ranking, and multi-category treatment planning (chemical, organic, cultural).
   - **Weather Agent (`/agents/weather`)**: Fetches live conditions & 7-day forecasts from OpenWeatherMap, predicts disease/pest risk scores, and generates operational weather alerts.
   - **RAG / IR Agent (`/agents/rag`)**: Conducts semantic retrieval over verified Sri Lankan agricultural documents using ChromaDB and Sentence-Transformers (`all-MiniLM-L6-v2`) to prevent AI hallucinations.
   - **Crop Advisory Agent (`/agents/crop`)**: Generates 8-stage cultivation planning (varieties, planting schedules, 4-stage fertilizer plans, irrigation, harvesting, crop rotation).
4. **Knowledge Base (`/knowledge_base`)**: Curated agricultural reference documents from the Department of Agriculture (DOA) and IRRI.
5. **Tests (`/tests`)**: Pytest test suite covering unit tests, contract tests, and integration flows.
6. **Docs (`/docs`)**: Architecture designs, API contracts, UI specifications, risk models, and git workflow guides.

---

## 👥 Team & Responsibilities

| Member | Role | Primary Ownership |
| :--- | :--- | :--- |
| **Sanketh** (Lead) | Team Leader | Orchestrator Agent, NLP layer, LLM synthesis, Responsible AI, Integration, Deployment |
| **Danindu** | Developer | Knowledge Base, ChromaDB vector store, RAG Agent, Crop Advisory Agent |
| **Ishira** | Developer | Streamlit UI, Advisory response rendering, Multi-language support, Auth frontend |
| **Pathum** | Developer | Disease Agent, Weather Agent, Risk scoring, Security, Auth backend, Error handling |

---

## 📁 Repository Structure

```text
Agri-Advisor/
├── agents/
│   ├── crop/           # Crop Advisory Agent service
│   ├── disease/        # Disease Diagnosis Agent service
│   ├── rag/            # RAG / Information Retrieval Agent service
│   └── weather/        # Weather & Risk Forecasting Agent service
├── docs/               # Project documentation & workflows
│   └── git-workflow.md # Git branch & commit conventions
├── knowledge_base/     # Verified agricultural corpus & schemas
├── orchestrator/       # Central Orchestrator service & NLP
├── tests/              # Unit, integration, and API test suites
├── ui/                 # Streamlit conversational web interface
├── .gitignore          # Git exclusion rules
└── README.md           # Project guide & instructions
```

---

## 🚀 Getting Started & Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher
- Git
- Virtual environment tool (`venv`)

### 2. Clone the Repository
```bash
git clone https://github.com/sankethabilas/Agri-Advisor.git
cd Agri-Advisor
```

### 3. Set Up Virtual Environment
Create and activate an isolated Python virtual environment:

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API credentials:
```bash
cp .env.example .env
```
Key environment variables required:
- `GROQ_API_KEY` (or `OPENAI_API_KEY`)
- `OPENWEATHER_API_KEY`
- `JWT_SECRET_KEY`

---

## 🌿 Branching Strategy & Collaboration Rules

To ensure smooth parallel execution across all team members, we follow a strict branching model:

```
main (protected)
  └── development (integration branch)
        ├── sanketh
        ├── danindu
        ├── ishira
        └── pathum
```

### Branch Rules:
1. **`main`**: Protected branch. Merges only from `development` via reviewed Pull Request upon passing full system tests.
2. **`development`**: Main integration branch. All developers branch off `development`.
3. **Personal Branches**: `sanketh`, `danindu`, `ishira`, `pathum`.
   - Work exclusively in your assigned branch.
   - Pull `development` daily into your branch:
     ```bash
     git checkout development
     git pull origin development
     git checkout <your-branch>
     git merge development
     ```
4. **Never Commit Secrets**: Ensure `.env` and sensitive API keys are not committed.

---

## 📝 Commit Message Convention

All commits must follow the conventional commit format:
```text
<type>(<scope>): <description>
```

- **Types**: `feat` | `fix` | `test` | `docs` | `refactor` | `chore`
- **Scopes**: `orchestrator` | `disease` | `weather` | `rag` | `crop` | `ui` | `auth` | `kb` | `deploy`

For full examples and detailed PR guidelines, refer to [Git Workflow Guide](docs/git-workflow.md).

## Knowledge Base Indexing

The agricultural knowledge base is stored in:

`knowledge_base/documents.json`

To create or update the local ChromaDB vector index, run:

```bash
python scripts/index_knowledge_base.py