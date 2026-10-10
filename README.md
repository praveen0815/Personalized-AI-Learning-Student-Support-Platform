# Personalized AI Learning & Student Support Platform

An AI-powered learning platform that provides personalized tutoring, adaptive assessments, learning-gap detection, and student progress tracking through a unified dashboard.

## 🚀 Overview

The **Personalized AI Learning & Student Support Platform** helps students learn more effectively using their own study materials. It combines document-based knowledge retrieval, AI-assisted tutoring, adaptive assessments, and topic-wise mastery tracking in one platform.

Students can upload educational PDFs, ask questions grounded in those materials, practice multiple-choice questions, track their learning progress, and identify topics that need additional attention.

## ✨ Key Features

- **Knowledge Base Management:** Upload educational PDFs and convert their contents into searchable text chunks.
- **Semantic Search:** Retrieve relevant information from uploaded study materials using vector embeddings.
- **AI Tutor:** Generate explanations grounded in retrieved document content, with source references.
- **Adaptive Assessments:** Generate multiple-choice questions based on uploaded learning materials and topic mastery.
- **Student Progress Tracking:** Maintain topic-wise mastery records from assessment performance.
- **Learning-Gap Detection:** Identify topics that need improvement and classify active gaps by severity.
- **Personalized Learning:** Adjust assessment difficulty according to the student's recorded mastery.
- **Interactive Dashboard:** View learning progress, topic mastery, and learning gaps through a Next.js interface.
- **REST API:** Access backend functionality through FastAPI endpoints and interactive Swagger documentation.

## 🏗️ System Architecture

```text
                Student
                   |
                   v
       Next.js Learning Dashboard
                   |
                   v
             FastAPI Backend
                   |
       +-----------+------------+
       |           |            |
       v           v            v
  Knowledge     AI Tutor     Assessment
    Base        Service        Engine
       |           |            |
       v           v            v
  PDF Upload   Semantic       Question
  & Extraction Retrieval      Generation
       |           |            |
       +-----------+------------+
                   |
                   v
          PostgreSQL + pgvector
                   |
                   v
        Student Learning Records
                   |
          +--------+--------+
          |                 |
          v                 v
     Topic Mastery     Learning Gaps
          |                 |
          +--------+--------+
                   |
                   v
          Personalized Dashboard
```

## 🛠️ Technology Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- pgvector
- PyMuPDF
- Pydantic

### AI and Machine Learning
- Retrieval-Augmented Generation (RAG)
- Text embeddings
- Semantic similarity search
- Large Language Models (LLMs)
- Rule-based adaptive assessment
- Topic mastery and learning-gap calculation

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS
- Recharts
- Lucide Icons

### Development and Testing
- Git and GitHub
- Docker
- Pytest
- Swagger / OpenAPI

## 🔄 How It Works

1. **Upload Study Materials:** The student uploads a PDF containing educational content.
2. **Extract and Process Text:** The backend extracts page-aware text, cleans it, and divides it into chunks.
3. **Generate Embeddings:** Each chunk is converted into a numerical vector representation.
4. **Store Knowledge:** Text chunks and embeddings are stored in PostgreSQL with pgvector.
5. **Retrieve Relevant Content:** Student questions are converted into embeddings, and relevant chunks are retrieved through semantic search.
6. **Provide AI Tutoring:** The tutor uses retrieved material to generate an explanation and returns source references.
7. **Generate Assessments:** The assessment engine creates multiple-choice questions based on relevant study content.
8. **Evaluate Performance:** Submitted answers are scored, and topic mastery is updated.
9. **Identify Learning Gaps:** Topics below the configured mastery threshold are marked for improvement.
10. **Personalize Learning:** The assessment engine selects question difficulty based on the student's recorded mastery.

## 📊 Learning Intelligence

### Topic Mastery

The platform calculates a topic mastery score using assessment accuracy.

For the first assessment attempt:

```text
Mastery = Current Assessment Accuracy × 100
```

For subsequent attempts:

```text
New Mastery =
    (Previous Mastery × 0.7)
  + (Current Accuracy × 100 × 0.3)
```

The weights are configurable through environment variables.

### Learning-Gap Classification

| Mastery Score | Gap Status |
|---|---|
| 60 and above | No active learning gap |
| 50 to below 60 | Medium learning gap |
| Below 50 | High learning gap |

These are configurable MVP rules, not clinically or scientifically validated measurements of knowledge.

### Adaptive Assessment

- **No previous mastery:** Medium-difficulty questions.
- **Below 40 mastery:** Mostly easy questions with some medium questions.
- **40 to below 70 mastery:** Medium-difficulty questions.
- **70 or above mastery:** A mixture of medium and hard questions.

## 📁 Project Structure

```text
Personalized-AI-Learning-Student-Support-Platform/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── knowledge/
│   │   ├── tutor/
│   │   ├── assessments/
│   │   ├── students/
│   │   └── ...
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── ...
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── public/
│   ├── package.json
│   └── ...
│
└── README.md
```

*Note: The module names shown are illustrative where the exact internal folder names may differ.*

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.12 or 3.13
- Node.js and npm
- PostgreSQL 16 with pgvector, or Docker Desktop
- An LLM API key for live AI tutoring and assessment generation

### 1. Clone the Repository

```bash
git clone https://github.com/praveen0815/Personalized-AI-Learning-Student-Support-Platform.git
cd Personalized-AI-Learning-Student-Support-Platform
```

### 2. Start PostgreSQL with pgvector

If Docker Desktop is installed and running:

```bash
docker run --name learning-kb-pg \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=learning_kb \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

If the container already exists:

```bash
docker start learning-kb-pg
```

### 3. Configure the Backend

Open a terminal in the backend directory:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure the required values in `backend/.env`.

For local embeddings without an embedding API key:

```env
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSION=384

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/learning_kb
```

For live AI tutoring and assessment generation, configure an OpenAI-compatible chat provider:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your_actual_api_key
```

Use your own valid API key. Never commit `.env` or expose API keys in the frontend.

### 4. Run the Backend

From the `backend` directory:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend API documentation:

- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

### 5. Configure and Run the Frontend

Open a second terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open the application at:

http://localhost:3000

The frontend uses the local FastAPI backend. Configure any frontend environment variables according to `frontend/.env.example`.

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check backend and database status |
| POST | `/api/v1/knowledge/documents` | Upload a study PDF |
| GET | `/api/v1/knowledge/documents` | List uploaded documents |
| GET | `/api/v1/knowledge/documents/{document_id}` | Retrieve document metadata |
| POST | `/api/v1/knowledge/search` | Search study materials semantically |
| POST | `/api/v1/tutor/chat` | Ask the AI tutor a question |
| POST | `/api/v1/students` | Create a student record |
| POST | `/api/v1/assessments/generate` | Generate a topic-based assessment |
| POST | `/api/v1/assessments/adaptive` | Generate an assessment using topic mastery |
| GET | `/api/v1/assessments/{assessment_id}` | Retrieve assessment questions |
| POST | `/api/v1/assessments/{assessment_id}/submit` | Submit answers and update mastery |
| GET | `/api/v1/students/{student_id}/progress` | Retrieve topic-wise progress |
| GET | `/api/v1/students/{student_id}/learning-gaps` | Retrieve active learning gaps |

## 🧪 Testing

Run the backend tests from the `backend` directory:

```powershell
pytest
```

For PostgreSQL and pgvector integration tests, configure `INTEGRATION_DATABASE_URL` to point to a separate test database and run:

```powershell
$env:INTEGRATION_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/learning_kb_test"
pytest -m integration
```

The integration test database must have a name containing `test`. Tests use stand-in model services rather than requiring paid LLM calls.

## ⚠️ Current Scope and Limitations

- The platform uses uploaded PDFs as its knowledge source; video and slide processing are not included.
- Live AI responses and generated assessments require a valid LLM provider configuration.
- Local embeddings can run without an embedding API key, but the initial model download requires internet access.
- Mastery and adaptive difficulty use transparent, configurable MVP rules; they are not validated knowledge-tracing models.
- Authentication and production user management are not implemented in this version.
- The Government Scheme Eligibility Predictor is a separate project and is not included in this codebase.
- Dashboard history sections remain empty when the backend does not provide the corresponding historical data.

## 🔮 Future Enhancements

- User authentication and individual student profiles.
- Learning paths tailored to student performance.
- Support for video, slides, and additional educational formats.
- Richer analytics and learning-history visualizations.
- Course management and structured learning modules.
- Integration with the separate Government Scheme Eligibility Predictor.
- Deployment with production monitoring, security, and scalable infrastructure.

## 🎯 Project Goal

To make learning more personalized and accessible by combining document-grounded AI tutoring, adaptive assessments, and explainable learning-progress tracking in one platform.

## 👨‍💻 Author

**Praveenkumar R.**

---

*Built as an AI-powered student learning and support platform.*
