import os
import time
from pathlib import Path
from dotenv import load_dotenv
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import asyncio

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")    
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

pc=Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)

index = pc.Index(PINECONE_INDEX_NAME)

def load_vectorStore(uploaded_files,role:str,doc_id:str):
    # 1. Load embedding model
    embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # 2. Save file to disk
    for file in uploaded_files:
        saved_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(saved_path, "wb") as f:
            f.write(file.file.read())
            
            
    # 3. Load and extract text from PDF
    all_docs = []
    loader = PyPDFLoader(saved_path)
    documents = loader.load()

    # 4. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
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
                "page": chunk.metadata.get("page", 0)
            }
            for i, chunk in enumerate(chunks)
        ]

# 6. Embed the texts
print(f"Embedding {len(texts)} chunks...")
embeddings = embed_model.embed_documents(texts)

# 7. Upsert to Pinecone
print(f"Upserting to Pinecone index '{PINECONE_INDEX_NAME}'...")
with tqdm(total=len(embeddings), desc="Upserting to pinecone") as progress:
    index.upsert(
        vectors=zip(ids, embeddings, metadatas))
    progress.update(len(embeddings))
    
print(f"Upload completed for {file.filename}")
