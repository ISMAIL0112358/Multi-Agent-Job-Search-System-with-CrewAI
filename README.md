# AI Job Hunt & Recruitment Assistant 🚀

An AI-driven job hunt and talent recruitment platform using cooperative [CrewAI](https://www.crewai.com/) agents to assist both candidates and HR personnel. This dual-portal system helps job seekers find and tailor applications, while enabling HR professionals and hiring managers to ingest, search, screen, and vet candidate pools.

### 🛠️ Built With & Powered By

#### Core Stack
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=FFD62B)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F1F?style=for-the-badge&logo=sqlalchemy&logoColor=white)

#### AI Agents & RAG
![CrewAI](https://img.shields.io/badge/CrewAI-FF4B4B?style=for-the-badge&logo=crewai&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75C2?style=for-the-badge&logo=googlegemini&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3A?style=for-the-badge&logo=langchain&logoColor=white)
![Google Embeddings](https://img.shields.io/badge/Google%20Embeddings-Gemini--Embedding--001-4285F4?style=for-the-badge&logo=google&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-blue?style=for-the-badge)
![AgentOps](https://img.shields.io/badge/AgentOps-AI%20Observability-black?style=for-the-badge)
![LangSmith](https://img.shields.io/badge/LangSmith-AI%20Tracing-01C3A0?style=for-the-badge&logo=langchain&logoColor=white)

#### Ingestion & Tools
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![BeautifulSoup4](https://img.shields.io/badge/BS4-Parsing-orange?style=for-the-badge)
![Google OAuth](https://img.shields.io/badge/Google%20OAuth%202.0-4285F4?style=for-the-badge&logo=google&logoColor=white)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-PDF%20Parser-red?style=for-the-badge)
![React Router](https://img.shields.io/badge/React%20Router-CA4245?style=for-the-badge&logo=react-router&logoColor=white)
![Axios](https://img.shields.io/badge/Axios-5A29E4?style=for-the-badge&logo=axios&logoColor=white)

---

## ✨ Dual-Portal Capabilities

The system provides separate login paths and customized interfaces for both Job Seekers and HR/Hiring Managers, accessible from a single, unified landing page.

### 🔍 Job Seeker Portal
*   **Interactive AI Chat:** Chat with a multi-agent AI crew to search for jobs based on keywords, location, and preferences.
*   **Resume Parsing & Storage:** Upload PDF resumes. The system parses, extracts text, and stores them in your profile.
*   **Hiring Scorer Agent:** Compares your uploaded resume to a job description, outputting a match score (0–100%) and key recommendations.
*   **Company Profiler:** Automatically researches company size, key founders, culture, and pay scales.
*   **Interview Prep Assistant:** Generates custom interview questions and tips tailored to the target role.
*   **Resume Tailor & Cover Letter Generator:** Automatically rewrites your resume and drafts matching cover letters for specific job applications.

### 🏢 HR & Hiring Manager Portal
*   **Spreadsheet & Document Ingestion:** Upload PDF resumes or bulk-import candidate logs using Excel (`.xlsx`, `.xls`) or CSV spreadsheets (automatically parsing columns like `ID`, `Resume_str`, and `Category` while stripping HTML).
*   **Fuzzy Search Directory:** Instantly search through candidates with partial names, typos, status flags, or filenames using an intelligent, scored fuzzy-matching algorithm.
*   **AI Screening & RAG:** Match the entire candidate pool against open Job Descriptions using semantic vector searches (via ChromaDB), generating match percentages (0–100%) and clear reasoning.
*   **Vetting Q&A Generator:** Automatically generate customized vetting questions and verification answer guides for interviews, validating candidate claims and preventing misrepresentation.

---

## 🛠️ Tech Stack

### Frontend
- **Framework:** React + Vite
- **Styling:** Custom CSS (Modern glassmorphism design with responsive dark/light modes)
- **Routing:** React Router
- **Features:** React Dropzone, Lucide Icons

### Backend
- **Framework:** FastAPI (Python)
- **Database:** SQLite with SQLAlchemy ORM
- **Vector Search:** ChromaDB (for semantic RAG search across resumes)
- **Data Ingestion:** Pandas, OpenPyXL, BeautifulSoup4 (for spreadsheet bulk imports)
- **Authentication:** Google OAuth 2.0 (Role-based separation)
- **PDF Processing:** PyPDF2 / pdfplumber

### AI & Agents
- **Multi-Agent Framework:** CrewAI
- **LLM Provider:** Google Gemini (`gemini-1.5-flash` / `gemini-1.5-pro`) via LiteLLM
- **Agent Monitoring:** AgentOps
- **RAG & Chain Monitoring:** LangSmith (for tracing LangChain embeddings and vector store queries)


---

## 🧠 Detailed Architecture Flow

1. **Dual Entry Authentication:** Users log in using their Google account. Based on their selected login button, the system provisions their session under the appropriate role (`job_seeker` or `hr`).
2. **Data & Vector Ingestion:**
   - Job Seekers upload their individual profile details and PDFs.
   - HR Managers upload resume folders (PDF) or tabular spreadsheets. Resumes are parsed, cleaned, and ingested into SQLite as candidate records, with embeddings pushed to ChromaDB.
3. **Agent Orchestration (Job Seeker):**
   - **Job Search Tool:** Queries APIs for active listings.
   - **Resume Scorer / Tailor Agents:** Analyze job descriptions and draft personalized application files.
4. **Agent Orchestration (HR Manager):**
   - **Semantic Retriever:** Performs RAG queries to find the most relevant candidates for a Job Description.
   - **AI Match Analyst:** Compares candidate profiles to the JD requirements to score suitability.
   - **Vetting Agent:** Reviews the candidate's resume against the JD to generate specialized behavioral and technical vetting questions.
5. **Persistence:** All screening metrics, generated Q&As, and rewritten documents are saved securely for quick dashboard retrieval.

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- API Keys for Google OAuth, Gemini AI, and AgentOps.

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Multi-Agent-Job-Search-System-with-CrewAI
```

### 2. Backend Setup
Navigate to the root directory and set up your Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

Run database migrations to prepare both the Job Seeker and HR portal schemas (including user roles, candidate lists, job descriptions, and screening result tables):
```bash
python migrate_db.py
python migrate_hr.py
```

Create a `.env` file in the root directory and populate it:
```env
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_NAME=gemini/gemini-1.5-flash

# Environment (prod or local)
ENV=prod # Set to 'local' to use Ollama

# Local Ollama Settings (Required if ENV=local)
OLLAMA_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=gemma4
LOCAL_EMBEDDING_MODEL=embeddinggemma

# USAJobs API (or other integrated job board)
USAJOBS_API_KEY=your_usajobs_api_key

# AgentOps Monitoring
AGENTOPS_API_KEY=your_agentops_api_key

# LangSmith Monitoring (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=Multi-Agent-Job-Search-System
```

### 🦙 Local LLM & Embeddings (Ollama Setup)
To run the application entirely on your local machine using open models (such as `gemma`):

1. Install [Ollama](https://ollama.com/).
2. Pull the required LLM and Embedding models in your terminal:
   ```bash
   ollama pull gemma4          # For agents, screening, and chat
   ollama pull embeddinggemma  # For candidate resume database embeddings
   ```
3. Change the `ENV` setting in your `.env` file:
   ```env
   ENV=local
   ```
4. Start your local Ollama application/server. The backend will automatically switch to local embeddings and agent execution.

### 3. Background Tasks Setup (Redis & Celery)
The application uses Celery and Redis to handle heavy background tasks (like bulk resume parsing and AI screening). You must run these services alongside your backend.

1. **Install and Start Redis** (Requires [Homebrew](https://brew.sh/) on Mac):
   ```bash
   brew install redis
   redis-server
   ```
   *(Leave this running in its own terminal tab)*

2. **Start the Celery Worker**:
   Open a new terminal tab, navigate to the project root, and run:
   ```bash
   python3 -m celery -A backend.celery_app.celery_app worker --loglevel=info --concurrency=2
   ```
   *(Leave this running in its own terminal tab)*

### 4. Run the Backend Server
Once Redis and Celery are running, start the FastAPI backend server in a new terminal tab:
```bash
uvicorn backend.main:app --reload
```
The backend will run at `http://127.0.0.1:8000`.

### 5. Frontend Setup
Open a new terminal window and navigate to the `frontend` directory:
```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend` directory for Vite:
```env
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_API_URL=http://127.0.0.1:8000/api
```

Start the React development server:
```bash
npm run dev
```
The frontend will be accessible at `http://localhost:5173`.

### 6. Enjoy!
Open your browser, navigate to `http://localhost:5173`, log in with Google, and let your AI crew find your next job!
