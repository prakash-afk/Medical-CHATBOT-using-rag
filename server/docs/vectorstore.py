import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import asyncio

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
        output_dimensionality=768,
    )


async def load_vectorStore(uploaded_files, role: str, doc_id: str):
    embed_model = get_embedding_model()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
    )
    total_chunks = 0

    for file_number, file in enumerate(uploaded_files):
        saved_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(saved_path, "wb") as f:
            f.write(file.file.read())

        loader = PyPDFLoader(saved_path)
        documents = loader.load()
        chunks = splitter.split_documents(documents)
        texts = [chunk.page_content for chunk in chunks]

        if not texts:
            print(f"Skipping {file.filename}: no text extracted")
            continue

        ids = [f"{doc_id}-{file_number}-{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": file.filename,
                "doc_id": doc_id,
                "role": role,
                "page": chunk.metadata.get("page", 0),
                "text": chunk.page_content,
            }
            for chunk in chunks
        ]

        print(f"Embedding {len(texts)} chunks from {file.filename}...")
        embeddings = await asyncio.to_thread(embed_model.embed_documents, texts)

        print(f"Upserting {len(embeddings)} vectors to Pinecone index '{PINECONE_INDEX_NAME}'...")
        with tqdm(total=len(embeddings), desc=f"Upserting {file.filename}") as progress:
            index.upsert(vectors=zip(ids, embeddings, metadatas))
            progress.update(len(embeddings))

        total_chunks += len(chunks)
        print(f"Upload completed for {file.filename}")

    return {
        "doc_id": doc_id,
        "file_count": len(uploaded_files),
        "chunk_count": total_chunks,
        "index_name": PINECONE_INDEX_NAME,
    }


def describe_index_stats() -> dict[str, Any]:
    return index.describe_index_stats()
