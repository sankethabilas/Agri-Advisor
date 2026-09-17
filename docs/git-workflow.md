# Git Workflow & Branch Strategy

This document outlines the Git branching model, commit conventions, pull request processes, and collaboration rules for the **Agri-Advisor** development team.

---

## 1. Branch Strategy & Hierarchy

The repository uses a 3-tier branching model to enable all 4 developers to work concurrently without overwriting code or blocking one another:

```
main (protected)
  └── development (integration branch)
        ├── sanketh (Orchestrator, NLP, Routing, Synthesis, Responsible AI, Caching)
        ├── danindu (Knowledge Base, ChromaDB, RAG Agent, Crop Advisory Agent)
        ├── ishira  (Streamlit UI, Rendering, Multi-language, Auth Frontend)
        └── pathum  (Disease Agent, Weather Agent, Security, Auth Backend, Fallbacks)
```

### 1.1 Branch Roles & Rules
1. **`main` (Production / Release Branch)**:
   - Protected branch.
   - Direct commits and direct pushes are strictly prohibited.
   - Only receives merges from `development` upon completion of system testing (Day 10 / T-40).
   - Code in `main` is always deployable and release-ready.

2. **`development` (Active Integration Branch)**:
   - The primary integration branch where feature branches merge.
   - Must always be in a runnable, passing state.
   - All feature and personal branches branch off `development`, **never** `main`.
   - Merging into `development` requires a tested Pull Request reviewed by a peer.

3. **Personal / Feature Branches (`sanketh`, `danindu`, `ishira`, `pathum`)**:
   - Each developer works strictly on their assigned branch.
   - Developers own their vertical slices.
   - Never push directly to another member's branch.

---

## 2. Daily Working Rules

1. **Pull Daily**:
   - At the start of each working day, pull latest changes from `development` into your personal branch:
     ```bash
     git checkout development
     git pull origin development
     git checkout <your-branch-name>
     git merge development
     ```
2. **Commit Frequently**:
   - Make atomic, meaningful commits per completed subtask (e.g., T-01.2, T-01.3).
   - Avoid giant end-of-day commits.
3. **Never Commit Secrets**:
   - `.env`, API keys (OpenWeatherMap, Groq, OpenAI), JWT secrets, or passwords must **never** be committed.
   - Ensure `.gitignore` is respected. Use `.env.example` as a template for environment variables.
4. **Clean Code & Verification**:
   - Run tests and verify local functionality before opening a pull request.

---

## 3. Commit Message Convention

All commit messages in the repository **must** adhere strictly to the following conventional commit format:

### Format
```text
<type>(<scope>): <short description>
```

### 3.1 Allowed Types
| Type | Description |
| :--- | :--- |
| `feat` | A new feature or capability |
| `fix` | A bug fix |
| `test` | Adding or updating tests |
| `docs` | Documentation changes only |
| `refactor` | Code refactoring without changing behavior |
| `chore` | Maintenance tasks, configs, dependencies, repo setup |

### 3.2 Allowed Scopes
| Scope | Area / Component |
| :--- | :--- |
| `orchestrator` | Orchestrator Agent service, session context, NLP layer, routing |
| `disease` | Disease Agent, symptom matching, diagnosis logic |
| `weather` | Weather Agent, OpenWeatherMap integration, risk scoring |
| `rag` | RAG / IR Agent, embeddings, ChromaDB search |
| `crop` | Crop Advisory Agent, cultivation planning, seasonal calendars |
| `ui` | Streamlit user interface, multi-language UI, layout components |
| `auth` | Authentication, JWT, security middleware, password hashing |
| `kb` | Knowledge base curation, JSON data schemas, dataset updates |
| `deploy` | Hosting, Docker/Render/Streamlit Cloud configuration, environment setups |

### 3.3 Commit Message Examples

#### Valid Examples:
- `feat(disease): add symptom ranking with confidence score`
- `feat(rag): return source attribution with top-3 results`
- `fix(ui): correct Sinhala rendering in the advisory block`
- `test(api): add contract tests for /api/weather/advice`
- `docs(kb): document the disease knowledge base schema`
- `chore(repo): initialize folder structure and .gitignore`
- `feat(auth): implement JWT token verification middleware`
- `fix(orchestrator): handle empty candidate disease response gracefully`

#### Invalid Examples:
- ❌ `updated stuff` (missing type, scope, and descriptive message)
- ❌ `feat: added disease agent` (missing required scope)
- ❌ `WIP on weather` (non-standard type and format)
- ❌ `Fix(UI): bug` (type and scope must be lowercase)

---

## 4. Pull Request & Review Process

1. **Self-Test**: Complete the subtask on your branch, run all local tests, and ensure code is clean.
2. **Sync with Development**: Pull and merge `origin/development` locally and resolve any conflicts.
3. **Open PR**: Create a Pull Request from `<your-branch>` into `development` on GitHub.
   - Title: `<type>(<scope>): <summary> (Task ID)` e.g., `feat(disease): implement symptom matcher (T-13)`
   - Description: Include task ID, changes made, and test evidence.
4. **Code Review**:
   - Sanketh reviews all incoming PRs into `development`.
   - Danindu reviews Sanketh's PRs.
   - Review checks: Contract conformance, failure case handling, zero secrets committed, passes tests.
5. **Merge**: Once approved, merge using standard merge commit or squash merge.
6. **Verify `development`**: Verify `development` remains stable after merge.

---

## 5. Conflict Resolution Protocol

- **Different Files**: Because each developer owns a vertical slice, conflicts are minimized.
- **Shared Files (`requirements.txt`, root configs)**: Coordinated with the file owner before editing.
- **API Contract Discrepancies**: Discussed at daily stand-ups and decided by the Team Lead (Sanketh) in `/docs/api-contract.md`.
