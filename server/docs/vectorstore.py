import os
from pathlib import Path

from dotenv import load_dotenv
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

pc = Pinecone(api_key=PINECONE_API_KEY)
spec = ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)

index = pc.Index(PINECONE_INDEX_NAME)

def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is missing in server/.env")

    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY,
    )


def load_vectorStore(uploaded_files, role: str, doc_id: str):
    embed_model = get_embedding_model()

    # 2. Save file to disk
    for file in uploaded_files:
        saved_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(saved_path, "wb") as f:
            f.write(file.file.read())

    # 3. Load and extract text from PDF
    loader = PyPDFLoader(saved_path)
    documents = loader.load()

    # 4. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
    )
    chunks = splitter.split_documents(documents)

    # 5. Prepare texts, ids and metadata
    texts = [chunk.page_content for chunk in chunks]
    ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "source": file.filename,
            "doc_id": doc_id,
            "role": role,
            "page": chunk.metadata.get("page", 0),
        }
        for chunk in chunks
    ]

    # 6. Embed the texts
    print(f"Embedding {len(texts)} chunks...")
    embeddings = embed_model.embed_documents(texts)

    # 7. Upsert to Pinecone
    print(f"Upserting to Pinecone index '{PINECONE_INDEX_NAME}'...")
    with tqdm(total=len(embeddings), desc="Upserting to pinecone") as progress:
        index.upsert(vectors=zip(ids, embeddings, metadatas))
        progress.update(len(embeddings))

    print(f"Upload completed for {file.filename}")
