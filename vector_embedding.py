import os
from dotenv import load_dotenv
from pymongo import MongoClient
from PyPDF2 import PdfReader

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI)
db = client["vector_db"]   # must match everywhere
collection = db["pdf_docs"]


def load_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text


from datetime import datetime
from langchain_core.documents import Document

def store_embeddings(files, org_id=None, user_id=None):
    all_text = ""

    for file in files:
        pdf_text = load_pdf(file)
        all_text += pdf_text + "\n"

    splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(all_text)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    docs = []

    for chunk in chunks:
        metadata = {
            "timestamp": datetime.now()
        }

        if org_id:
            metadata["org_id"] = org_id
        if user_id:
            metadata["user_id"] = user_id

        docs.append(
            Document(
                page_content=chunk,
                metadata=metadata
            )
        )

    vector_store = MongoDBAtlasVectorSearch.from_documents(
        documents=docs,
        embedding=embeddings,
        collection=collection,
        index_name="vector_index"
    )

    print("Documents being stored:", len(docs))
    if docs:
        print("Sample metadata:", docs[0].metadata)

    return vector_store
