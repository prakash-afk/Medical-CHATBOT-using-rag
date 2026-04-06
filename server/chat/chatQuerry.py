import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pinecone import Pinecone

SERVER_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from docs.vectorstore import get_embedding_model

load_dotenv(SERVER_DIR / ".env")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
embed_model = get_embedding_model()
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3,
    max_tokens=2048,
    api_key=GROQ_API_KEY,
)

prompt = PromptTemplate(
    template="""
      You are a helpful medical assistant.
      Answer ONLY from the provided medical transcript context.
      If the context is insufficient, just say you don't know.

      {context}
      Question: {question}
    """,
    input_variables=["context", "question"],
)


class PineconeRetriever:
    def __init__(self, *, top_k: int = 4):
        self.top_k = top_k

    async def invoke(self, query: str, user_role: str | None = None) -> list[Document]:
        query_embedding = await asyncio.to_thread(embed_model.embed_query, query)
        query_kwargs = {
            "vector": query_embedding,
            "top_k": self.top_k,
            "include_metadata": True,
        }

        results = await asyncio.to_thread(index.query, **query_kwargs)
        documents: list[Document] = []
        for match in results.get("matches", []):
            metadata = dict(match.get("metadata", {}))
            text = metadata.pop("text", "")
            if text:
                documents.append(Document(page_content=text, metadata=metadata))
        return documents


retriever = PineconeRetriever(top_k=4)


async def answer_query(query: str, user_role: str | None = None) -> dict:
    retrieved_docs = await retriever.invoke(query)
    if not retrieved_docs:
        return {"answer": "No relevant info found", "sources": []}

    context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
    sources = sorted(
        {
            doc.metadata.get("source")
            for doc in retrieved_docs
            if doc.metadata.get("source")
        }
    )
    final_prompt = prompt.invoke({"context": context_text, "question": query})
    answer = await asyncio.to_thread(llm.invoke, final_prompt)
    return {"answer": answer.content, "sources": sources}


if __name__ == "__main__":
    sample_question = "What are the symptoms of diabetes?"
    result = asyncio.run(answer_query(sample_question, user_role="admin"))
    print(result["answer"])
