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
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# MongoDB setup
client = MongoClient(MONGODB_URI)
db = client["vector_db"]
collection = db["pdf_docs"]


def load_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text


def store_embeddings(files):
    # Read PDFs
    all_text = ""
    for file in files:
        all_text += load_pdf(file) + "\n"

    # Split text
    splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(all_text)

    # Create embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    docs = [Document(page_content=chunk) for chunk in chunks]

    # Store in MongoDB
    vector_store = MongoDBAtlasVectorSearch.from_documents(
        documents=docs,
        embedding=embeddings,
        collection=collection,
        index_name="vector_index"
    )

    return vector_store