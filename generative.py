import os
from dotenv import load_dotenv
from pymongo import MongoClient

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_community.chains import create_retrieval_chain
from langchain_community.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI)
db = client["vector_db"]
collection = db["pdf_docs"]


def get_qa_chain(org_id=None, user_id=None):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name="vector_index"
    )

    # Correct filter according to your actual schema
    if org_id:
        search_filter = {"org_id": org_id}
    else:
        search_filter = {"user_id": user_id}

    def retrieve_docs(inputs):
        if isinstance(inputs, dict):
            query = inputs.get("input", "")
        else:
            query = inputs

        print("Query:", query)
        print("Using filter:", search_filter)

        docs = vector_store.similarity_search(
            query,
            k=4,
            pre_filter=search_filter   # <-- FIXED
        )

        print("Retrieved docs:", len(docs))
        return docs

    retriever = RunnableLambda(retrieve_docs)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0
    )

    prompt = ChatPromptTemplate.from_template(
        """Answer using the context below.

If the answer is not in the context, say "I don't know."

Context:
{context}

Question:
{input}
"""
    )

    document_chain = create_stuff_documents_chain(llm, prompt)
    qa_chain = create_retrieval_chain(retriever, document_chain)

    return qa_chain

