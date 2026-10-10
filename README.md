# Personalized AI Learning & Student Support Platform

The platform has a FastAPI backend and a Next.js dashboard. Phase 1 turns an uploaded PDF into page-aware text chunks, stores embeddings in PostgreSQL with pgvector, and answers semantic search. Phase 2 is a source-grounded tutor. Phase 3 writes multiple-choice checks, scores them, and keeps an explainable topic mastery record. Phase 4A is the dashboard shell. It reads progress and learning gaps when a development student id is configured, and it leaves sections empty when that data does not exist.

Video or slide processing, authentication, and the Government Scheme Eligibility Predictor are not part of this codebase. The mastery score is a weighted average for this MVP. It is not Deep Knowledge Tracing, Bayesian Knowledge Tracing, or another validated knowledge-tracing model. The dashboard does not invent analytics.

## Phase 1 architecture

```
PDF
  -> POST /api/v1/knowledge/documents
  -> PDF text extraction (PyMuPDF, page numbers kept)
  -> whitespace cleaning
  -> page-bounded chunking
  -> embedding generation
  -> PostgreSQL + pgvector
  -> POST /api/v1/knowledge/search
```

Chunking does not cross a page boundary. Within a page it prefers paragraph, sentence, and word breaks, then applies the configured overlap. Each stored chunk keeps the document id, page number, chunk index, text, and embedding so later phases can cite a source.

The embedding provider is selected with environment variables:

- `local` uses the fastembed model `BAAI/bge-small-en-v1.5` (384 dimensions) and does not need an API key. The model is downloaded on the first embed call.
- `openai` calls an OpenAI-compatible `POST /embeddings` endpoint. The API key is read from `EMBEDDING_API_KEY`.

There is no Alembic setup in this repository. On startup the backend runs `CREATE EXTENSION IF NOT EXISTS vector` and creates any missing tables. The embedding column dimension is fixed when the table is created. If you change `EMBEDDING_DIMENSION` or switch to a model with a different size, use a new database or drop the knowledge-base tables before starting the app again.

## Required software

- Windows with PowerShell
- Python 3.12 or 3.13
- PostgreSQL 16 with the pgvector extension
- Docker Desktop, if you use the database command below

## PostgreSQL and pgvector

Start Docker Desktop, then create a database that already includes pgvector:

```powershell
docker run --name learning-kb-pg -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=learning_kb -p 5432:5432 -d pgvector/pgvector:pg16
```

If that container already exists, start it with `docker start learning-kb-pg`.

The backend enables the `vector` extension on startup. The database user needs permission to run `CREATE EXTENSION`. The Docker `postgres` user has that permission.

Optional database for the pgvector integration test (the test refuses to run unless the database name contains `test`):

```powershell
docker exec learning-kb-pg psql -U postgres -c "CREATE DATABASE learning_kb_test;"
```

If PostgreSQL is already installed without Docker, create a database named `learning_kb`, install pgvector for that PostgreSQL version, and put that database in `DATABASE_URL`. The application still runs `CREATE EXTENSION IF NOT EXISTS vector` at startup.

## Environment variables

From `backend`:

```powershell
Copy-Item .env.example .env
```

`.env.example` contains placeholders and the local Docker database URL. It does not contain a real embedding API key.

| Variable | Purpose |
| --- | --- |
| `EMBEDDING_PROVIDER` | `local` or `openai` |
| `EMBEDDING_MODEL` | Model name. Local default: `BAAI/bge-small-en-v1.5`. OpenAI example: `text-embedding-3-small` |
| `EMBEDDING_API_KEY` | Required for `openai`. Leave empty for `local` |
| `EMBEDDING_BASE_URL` | OpenAI-compatible base URL. Default `https://api.openai.com/v1` |
| `EMBEDDING_DIMENSION` | Vector size. `384` for bge-small, `1536` for text-embedding-3-small. Must match the model |
| `DATABASE_URL` | SQLAlchemy URL, for example `postgresql+psycopg://postgres:postgres@localhost:5432/learning_kb` |
| `CHUNK_SIZE` | Target chunk length in characters. Default `1000` |
| `CHUNK_OVERLAP` | Overlap in characters. Must be smaller than `CHUNK_SIZE`. Default `150` |
| `MAX_UPLOAD_BYTES` | Upload limit. Default `20971520` (20 MB) |
| `UPLOAD_DIR` | Directory for stored PDFs, relative to `backend` unless absolute |
| `EMBEDDING_TIMEOUT_SECONDS` | HTTP timeout for the OpenAI-compatible embedding provider |
| `LLM_PROVIDER` | `openai` for chat completions, or `mock` for a fixed sentence with no network call |
| `LLM_MODEL` | Chat model name, for example `gpt-4o-mini`. Required for `openai` |
| `LLM_API_KEY` | Required for `LLM_PROVIDER=openai`. Leave empty for `mock` |
| `LLM_BASE_URL` | OpenAI-compatible chat base URL. Default `https://api.openai.com/v1` |
| `LLM_TIMEOUT_SECONDS` | HTTP timeout for the language model. Default `60` |
| `TUTOR_MIN_SIMILARITY` | Minimum cosine similarity for a chunk to be sent to the model or used for questions. Default `0.55` |
| `MASTERY_PRIOR_WEIGHT` | Weight of the previous topic mastery. Default `0.7` |
| `MASTERY_CURRENT_WEIGHT` | Weight of the current assessment accuracy. Default `0.3`. The two weights must sum to 1 |
| `LEARNING_GAP_THRESHOLD` | Mastery at or above this value clears an active gap. Default `60` |
| `LEARNING_GAP_MEDIUM_FLOOR` | Mastery at or above this value, and below the threshold, is a medium gap. Default `50` |
| `ADAPTIVE_EASY_BELOW` | Mastery below this value asks for mostly easy questions. Default `40` |
| `ADAPTIVE_HARD_AT` | Mastery at or above this value mixes medium and hard questions. Default `70` |
| `ASSESSMENT_MAX_GENERATION_ATTEMPTS` | How many times invalid model output may be requested again. Default `2` |

To use OpenAI instead of the local model, set:

```
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=your-key-here
EMBEDDING_DIMENSION=1536
```

Put the real key only in `.env`. Do not commit `.env`. Changing the dimension after tables already exist requires a new database, because pgvector will not resize the column automatically.

## Installation

```powershell
cd "C:\Users\91959\Desktop\Personalized AI Learning & Student Support Platform\backend"
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

You can skip activation and call `.\.venv\Scripts\python.exe` directly.

## Running the backend

Start the database container first, then:

```powershell
cd "C:\Users\91959\Desktop\Personalized AI Learning & Student Support Platform\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

`GET /health` returns the process status and database connectivity, including whether the pgvector extension is present when the database is PostgreSQL.

## Example PDF upload

In Swagger, open `POST /api/v1/knowledge/documents`, choose a `.pdf` file, and execute.

Or from PowerShell:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/knowledge/documents" -F "file=@C:\path\to\lecture.pdf"
```

A successful response includes `document_id`, `filename`, `total_pages`, `total_chunks`, and `processing_status`. Internal file paths are not returned.

List documents:

```powershell
curl.exe "http://127.0.0.1:8000/api/v1/knowledge/documents"
```

One document:

```powershell
curl.exe "http://127.0.0.1:8000/api/v1/knowledge/documents/<document_id>"
```

## Example semantic search

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/knowledge/search" -H "Content-Type: application/json" --data-raw '{"query":"Explain Bayes theorem","top_k":5}'
```

`top_k` is optional (default 5, maximum 20). Each result includes `document_id`, `document_name`, `chunk_id`, `page_number`, `chunk_index`, `content`, and `similarity`. `similarity` is cosine similarity from pgvector (`1 - cosine distance`), not a placeholder.

The first `local` upload or search downloads the embedding model, so that call takes longer. On Windows, Hugging Face may warn that the model cache cannot use symlinks. The download still works.

## Phase 2: source-grounded tutor

Retrieval-augmented generation here means the tutor does not answer from the model's general knowledge. The question is embedded with the same embedding service used for search, pgvector returns the closest chunks, and only those chunks are given to the language model. The model writes the explanation. The API adds document name, page number, chunk id, and similarity from the database rows. The model is not asked to invent those fields.

Chunks below `TUTOR_MIN_SIMILARITY` are discarded. If nothing remains, the tutor returns a short message that the uploaded materials do not cover the question, and it does not call the language model.

`LLM_PROVIDER=mock` skips the network and returns one fixed sentence. Use it to exercise the route without an API key. For real answers, set `LLM_PROVIDER=openai`, `LLM_MODEL`, and `LLM_API_KEY` in `.env`.

Example request:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/tutor/chat" -H "Content-Type: application/json" --data-raw '{"question":"Explain Bayes theorem in simple terms","top_k":5}'
```

A successful response has `answer` and `sources`. Each source includes `document_id`, `document_name`, `page_number`, `chunk_id`, and `similarity`. `top_k` is optional (default 5, maximum 20). Swagger shows this route as `POST /api/v1/tutor/chat`.

## Phase 3: adaptive assessment and learner record

An assessment is a set of multiple-choice questions grounded in the uploaded material. The topic is embedded with the existing embedding service, pgvector returns the closest chunks, and chunks below `TUTOR_MIN_SIMILARITY` are dropped. If nothing remains, the API returns `status: no_context` and does not ask the language model to invent questions.

When context exists, the existing language-model service receives only that context and must return JSON. Each question needs exactly four options (A–D), one correct letter, an explanation, and a difficulty of `easy`, `medium`, or `hard`. Invalid output is rejected and requested again, up to `ASSESSMENT_MAX_GENERATION_ATTEMPTS`. The backend copies `source_document_id` and `source_page_number` from the top retrieved chunk. The model is not asked for page numbers. The student-facing assessment does not include `correct_answer` or `explanation`.

Create a student, then generate a check:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/students" -H "Content-Type: application/json" --data-raw '{"name":"Asha"}'
curl.exe -X POST "http://127.0.0.1:8000/api/v1/assessments/generate" -H "Content-Type: application/json" --data-raw '{"student_id":"STUDENT_ID","topic":"Bayes Theorem","number_of_questions":5}'
```

`LLM_PROVIDER=mock` returns a fixed sentence, so it cannot produce questions. Set `LLM_PROVIDER=openai` with `LLM_MODEL` and `LLM_API_KEY` for a real model. Unit tests stub the model and do not call a paid API.

Submit every question. The answer letter is compared with the stored correct letter inside one database transaction:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/assessments/ASSESSMENT_ID/submit" -H "Content-Type: application/json" --data-raw '{"student_id":"STUDENT_ID","answers":[{"question_id":"QUESTION_ID","selected_option":"A"}]}'
```

### Mastery formula

Mastery is stored per topic. On the first attempt it is the accuracy for that topic on the attempt, times 100. After that:

```
new mastery = (old mastery × MASTERY_PRIOR_WEIGHT) + (current accuracy × 100 × MASTERY_CURRENT_WEIGHT)
```

With the defaults, old mastery 60 and current accuracy 80% becomes `60 × 0.7 + 80 × 0.3 = 66`. This is an explainable running average. It is not a validated knowledge-tracing algorithm.

### Learning gaps

A topic at or above `LEARNING_GAP_THRESHOLD` (default 60) has no active gap. From `LEARNING_GAP_MEDIUM_FLOOR` (default 50) up to but not including the threshold, the gap is `medium`. Below the floor it is `high`. The reason uses the latest stored answers, at most four. Example: `3 of the last 4 questions were answered incorrectly.` One active row is kept per student and topic. Crossing the threshold marks that row resolved.

### Adaptive difficulty

`POST /api/v1/assessments/adaptive` reads the topic mastery and chooses a difficulty list:

- No previous mastery: every question is medium.
- Mastery below 40: about 60% easy and the rest medium. Five questions are easy, easy, easy, medium, medium.
- Mastery from 40 up to but not including 70: every question is medium.
- Mastery 70 or higher: half the questions are hard and the rest are medium. Five questions are medium, medium, hard, hard, medium.

Unseen questions already stored for that topic and difficulty are reused first. If more are needed and the knowledge base has relevant context, the missing ones are generated. If it does not, previously seen questions are reused instead of failing. This is a fixed rule, not a reinforcement-learning policy.

Progress and active gaps:

```powershell
curl.exe "http://127.0.0.1:8000/api/v1/students/STUDENT_ID/progress"
curl.exe "http://127.0.0.1:8000/api/v1/students/STUDENT_ID/learning-gaps"
```

## Phase 4A: dashboard

The frontend lives in `frontend`. It is a Next.js application with the LearnAI shell: sidebar, top bar, and the `/dashboard` overview. Progress and learning gaps are loaded from the existing API when `NEXT_PUBLIC_DEMO_STUDENT_ID` is set. That variable is for development only. There is no login in this phase.

The backend allows the local dashboard origin through `CORS_ORIGINS` (default `http://localhost:3000` and `http://127.0.0.1:3000`). No API keys are placed in the frontend.

```powershell
cd "C:\Users\91959\Desktop\Personalized AI Learning & Student Support Platform\frontend"
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). It redirects to `/dashboard`. Leave the student id blank to see empty states. To load a real record, create a student with `POST /api/v1/students` and put that id in `NEXT_PUBLIC_DEMO_STUDENT_ID`.

Mastery history and assessment history are not returned by the API, so those dashboard sections stay empty on purpose.

## Testing

Unit tests use an in-memory SQLite database and do not call a paid embedding or chat API. The embedding service and the language model are stubbed. Semantic similarity, the tutor's retrieval path, and the assessment flow are covered by integration tests, which need PostgreSQL and pgvector. Those integration tests still use a stand-in language model.

```powershell
cd "C:\Users\91959\Desktop\Personalized AI Learning & Student Support Platform\backend"
.\.venv\Scripts\Activate.ps1
pytest
```

Integration test:

```powershell
$env:INTEGRATION_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/learning_kb_test"
pytest -m integration
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Backend and database status |
| POST | `/api/v1/knowledge/documents` | Upload a PDF |
| GET | `/api/v1/knowledge/documents` | List documents |
| GET | `/api/v1/knowledge/documents/{document_id}` | Document metadata |
| POST | `/api/v1/knowledge/search` | Semantic search |
| POST | `/api/v1/tutor/chat` | Source-grounded tutor answer |
| POST | `/api/v1/students` | Create a student |
| POST | `/api/v1/assessments/generate` | Grounded multiple-choice assessment |
| POST | `/api/v1/assessments/adaptive` | Assessment matched to topic mastery |
| GET | `/api/v1/assessments/{assessment_id}` | Assessment without correct answers |
| POST | `/api/v1/assessments/{assessment_id}/submit` | Score an assessment and update mastery |
| GET | `/api/v1/students/{student_id}/progress` | Topic mastery |
| GET | `/api/v1/students/{student_id}/learning-gaps` | Active learning gaps |

Invalid files, empty PDFs, PDFs with no extractable text, a missing embedding or language-model configuration, provider failures, database failures, an unknown document id, an empty question, and an invalid `top_k` return an error `detail` and an HTTP status. Responses do not include stack traces or API keys. A tutor question with no relevant uploaded material returns HTTP 200, an explanation that the materials do not cover it, and an empty `sources` list.
