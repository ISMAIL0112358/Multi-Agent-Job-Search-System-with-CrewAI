# Multi-Agent Job Search System with CrewAI 🚀

An intelligent, AI-powered job search assistant and resume optimization platform. This system utilizes multiple AI agents working in tandem (via [CrewAI](https://www.crewai.com/)) to help you find jobs, analyze job descriptions, score your resume's match percentage, and automatically tailor your resume and cover letters to specific roles.

## ✨ What It Does

- **Interactive AI Chat:** Talk to an AI assistant to search for jobs based on keywords, location, and company preferences.
- **Automated Job Searching:** Pulls real job listings via integrated APIs based on your chat requests.
- **Resume Parsing & Storage:** Upload PDF resumes. The system parses the text and securely stores them in your profile.
- **Hiring Scorer Agent:** Automatically compares your uploaded resume to a job description and gives you a match score (0-100%) along with reasoning.
- **Company Profiler:** Gathers deep insights on the company including founders, company size, pay ranges, and work culture/reviews.
- **Interview Prep Assistant:** Generates past interview questions tailored to the role and provides actionable interview preparation tips.
- **Resume Tailor & Cover Letter Generator:** AI agents rewrite your resume to highlight the most relevant skills for a specific job and draft a personalized cover letter.
- **Profile Management:** Manage your personal details, skill tags, and multiple versions of your resumes in a clean, modern UI.

## 🛠️ Tech Stack

### Frontend
- **Framework:** React + Vite
- **Styling:** Custom CSS (Modern Glassmorphism Design)
- **Routing:** React Router
- **File Uploads:** React Dropzone

### Backend
- **Framework:** FastAPI (Python)
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** Google OAuth 2.0
- **PDF Processing:** PyPDF2 / pdfplumber

### AI & Agents
- **Multi-Agent Framework:** CrewAI
- **LLM Provider:** Google Gemini (`gemini-1.5-flash` / `gemini-1.5-pro`) via LiteLLM
- **Agent Monitoring:** AgentOps

---

## 🧠 Detailed Architecture Flow

1. **User Authentication:** Users log in using their Google account. The backend creates a secure session and provisions a dedicated local storage directory for their files.
2. **Profile & Skills:** Users define their core skills (stored as tags) and upload baseline PDF resumes. The backend extracts and stores the text.
3. **Conversational Interface:** The user opens a chat and requests a job search (e.g., *"Find me Data Analyst jobs in New York"*).
4. **Agent Orchestration:**
   - **Job Search Tool:** Fetches real job listings matching the criteria.
   - **Hiring Scorer Agent:** For each job, this agent compares the Job Description against the user's selected baseline resume and predefined skills, generating a "Match Score".
5. **Tailoring Pipeline:** When a user wants to apply for a specific job:
   - **JD Analyzer Agent:** Extracts core requirements and responsibilities from the job description.
   - **Company Research Agent:** Pulls data on the company's background, work culture, and estimated salary ranges.
   - **Resume Tailor Agent:** Takes the JD analysis and the user's baseline resume, outputting a highly targeted text resume.
   - **Cover Letter Agent:** Drafts a customized cover letter for the specific company and role.
   - **Interview Prep Agent:** Formulates potential interview questions (FAQs) and provides actionable tips based on the role and company culture.
6. **File Persistence:** All tailored documents are saved back to the user's profile storage for easy access and future downloads.

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

Create a `.env` file in the root directory and populate it:
```env
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_NAME=gemini/gemini-1.5-flash

# USAJobs API (or other integrated job board)
USAJOBS_API_KEY=your_usajobs_api_key

# AgentOps Monitoring
AGENTOPS_API_KEY=your_agentops_api_key
```

Run the FastAPI backend server:
```bash
uvicorn backend.main:app --reload
```
The backend will run at `http://127.0.0.1:8000`.

### 3. Frontend Setup
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

### 4. Enjoy!
Open your browser, navigate to `http://localhost:5173`, log in with Google, and let your AI crew find your next job!
