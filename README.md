# Medical Chatbot Using RAG

A role-aware healthcare chatbot built with FastAPI, Streamlit, MongoDB, Pinecone, Google Gemini embeddings, and Groq.

The project lets authenticated users ask healthcare-related questions over uploaded PDF documents. Admins and doctors can upload PDFs, which are chunked, embedded, and stored in Pinecone. Chat responses are generated from the retrieved document context.

## Features

- User signup and login with Basic Auth
- Password hashing with `bcrypt`
- Role-based document upload permissions
- PDF parsing and chunking with LangChain
- Google Gemini embeddings with 768-dimensional output
- Pinecone vector search for retrieval
- Groq-powered answer generation
- Streamlit frontend for login, upload, and chat
- FastAPI backend for auth, document ingestion, and chat APIs
- Batch embedding flow to reduce quota spikes during large uploads

## Current Roles

- `admin`
- `doctor`
- `nurse`
- `patient`
- `other`

At the moment, only `admin` and `doctor` can upload documents. All logged-in users can ask questions against the indexed content.

## Project Structure

```text
Medical_CHATBOT/
|-- client/
|   |-- main.py
|   |-- .env
|   |-- requirements.txt
|   `-- pyproject.toml
|-- server/
|   |-- auth/
|   |   |-- hashUtils.py
|   |   |-- models.py
|   |   `-- routes.py
|   |-- chat/
|   |   |-- chatQuerry.py
|   |   `-- routes.py
|   |-- config/
|   |   `-- db.py
|   |-- docs/
|   |   |-- routes.py
|   |   `-- vectorstore.py
|   |-- uploaded_docs/
|   |-- .env
|   |-- main.py
|   |-- requirements.txt
|   `-- pyproject.toml
|-- .gitignore
`-- README.md
```

## How It Works

### 1. Authentication

The backend stores users in MongoDB. Passwords are hashed with `bcrypt`.

- Signup endpoint creates a user record
- Login endpoint validates credentials and returns the user's role
- Protected routes use HTTP Basic authentication

Relevant files:

- `server/auth/routes.py`
- `server/auth/hashUtils.py`
- `server/auth/models.py`
- `server/config/db.py`

### 2. Document Upload and Indexing

When an authorized user uploads a PDF:

1. The file is saved in `server/uploaded_docs/`
2. The PDF is loaded with `PyPDFLoader`
3. Text is split into chunks using `RecursiveCharacterTextSplitter`
4. Chunks are embedded using `models/gemini-embedding-001`
5. Embeddings are upserted into Pinecone with metadata such as:
   - source filename
   - page number
   - document id
   - role
   - raw chunk text

The current embedding configuration uses `output_dimensionality=768` so it matches the existing Pinecone index dimension.

To reduce provider rate-limit failures, embeddings are sent in batches instead of one large request.

Relevant files:

- `server/docs/routes.py`
- `server/docs/vectorstore.py`

### 3. Retrieval and Answer Generation

When a user asks a question:

1. The question is embedded using the same Google embedding model
2. Pinecone is queried for the nearest chunks
3. Retrieved chunks are joined into context
4. A Groq LLM generates the final answer
5. Source filenames are returned with the response

Relevant files:

- `server/chat/chatQuerry.py`
- `server/chat/routes.py`

### 4. Frontend

The Streamlit app provides:

- Login and signup tabs
- PDF upload UI for allowed roles
- Chat interface for question answering
- Friendly error messages for backend failures

Relevant file:

- `client/main.py`

## Tech Stack

### Backend

- FastAPI
- MongoDB
- Pinecone
- LangChain
- Google Gemini Embeddings
- Groq
- PyPDF
- bcrypt

### Frontend

- Streamlit
- Requests

## Environment Variables

Create the following files before running the app.

### Backend: `server/.env`

Required keys:

```env
MONGO_URI=
dbName=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=
PINECONE_ENVIRONMENT=
GOOGLE_API_KEY=
GROQ_API_KEY=
```

Notes:

- `GOOGLE_API_KEY` is used for Gemini embeddings
- `GROQ_API_KEY` is used for answer generation
- `PINECONE_INDEX_NAME` should point to a 768-dimensional index if you keep the current embedding setup

### Frontend: `client/.env`

```env
API_URL=http://localhost:8000
```

## Installation

This project is split into two runnable apps: `server` and `client`.

### 1. Clone the repository

```bash
git clone https://github.com/prakash-afk/Medical-CHATBOT-using-rag.git
cd Medical-CHATBOT
```

### 2. Set up the backend

```bash
cd server
python -m venv .venv
```

Activate the environment:

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Set up the frontend

Open a second terminal:

```bash
cd client
python -m venv .venv
```

Activate the environment:

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Project

### Start the backend

From the `server` directory:

```bash
uvicorn main:app --reload
```

The backend will run at:

```text
http://localhost:8000
```

Useful endpoint:

```text
http://localhost:8000/health
```

### Start the frontend

From the `client` directory:

```bash
streamlit run main.py
```

The frontend will run at:

```text
http://localhost:8501
```

## API Overview

### Auth

#### `POST /auth/signup`

Creates a user.

Example JSON body:

```json
{
  "username": "doctor1",
  "password": "strongpassword",
  "role": "doctor"
}
```

#### `POST /auth/login`

Uses HTTP Basic Auth.

Returns:

```json
{
  "message": "Welcome doctor1! Your role is doctor.",
  "username": "doctor1",
  "role": "doctor"
}
```

### Documents

#### `POST /documents/upload-docs`

Protected route.

- Requires HTTP Basic Auth
- Only `admin` and `doctor` can upload
- Accepts file upload field named `files`

Successful response includes:

- `doc_id`
- `chunk_count`
- `index_name`

### Chat

#### `POST /chat`

Protected route.

- Requires HTTP Basic Auth
- Accepts form field `message`

Response example:

```json
{
  "answer": "Generated answer here",
  "sources": [
    "sample.pdf"
  ]
}
```

## Pinecone Notes

Your current code expects a Pinecone index compatible with:

- vector dimension: `768`
- dense vectors
- semantic retrieval over uploaded PDF chunks

If you change the embedding model output dimension, the Pinecone index dimension must match.

## Google Embedding Notes

The project currently uses:

```python
GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    output_dimensionality=768,
)
```

This was chosen so the embedding vector size matches the current Pinecone index.

## Known Limitations

- Authentication uses HTTP Basic Auth rather than JWT/session tokens
- Uploaded files are currently available to all logged-in users
- Role filtering is not yet applied during retrieval
- Large PDF uploads may still hit provider quota limits, though batching reduces the risk
- The project depends on several external services, so setup requires multiple API keys

## Troubleshooting

### Upload shows "Embedding quota is temporarily exhausted"

This usually means the Google embedding API hit a rate limit or temporary quota limit.

What to try:

- wait a bit and retry
- upload smaller PDFs first
- reduce chunk count if needed
- check backend logs for the original traceback

### Pinecone upsert dimension error

This happens when the embedding vector dimension does not match the Pinecone index dimension.

Current expected setup:

- embedding dimension: `768`
- Pinecone index dimension: `768`

### Login fails

Check:

- MongoDB is reachable
- the user exists
- the password is correct
- `MONGO_URI` and `dbName` are configured correctly

### Chat returns weak answers

Check:

- PDFs were uploaded successfully
- Pinecone contains vectors
- the question is relevant to the uploaded documents
- `GROQ_API_KEY` is valid

## Suggested Next Improvements

- Replace Basic Auth with JWT authentication
- Add per-role document filtering during retrieval
- Prevent duplicate uploads of the same file
- Add document listing and delete endpoints
- Add automated tests
- Improve logging and error observability
- Add Docker support

## License

No license file is currently included in the repository. Add one if you plan to distribute or open-source the project publicly.
