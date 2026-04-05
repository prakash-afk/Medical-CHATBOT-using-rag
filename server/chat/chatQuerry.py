import os
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_community.vectorstores import Pinecone as PineconeVectorStore
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from docs.vectorstore import get_embedding_model

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
embed_model = get_embedding_model()

vector_store = PineconeVectorStore(index=index, embedding=embed_model, text_key="text")
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3, max_tokens=2048, api_key=GROQ_API_KEY)

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

question = "is the topic of nuclear fusion discussed in this video? if yes then what was discussed"
retrieved_docs = retriever.invoke(question)
context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
final_prompt = prompt.invoke({"context": context_text, "question": question})

answer = llm.invoke(final_prompt)
print(answer.content) 

