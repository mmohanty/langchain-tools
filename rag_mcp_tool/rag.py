from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_and_split_documents(file_path, chunk_size=500, chunk_overlap=50):
    loader = TextLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(docs)

def query_vector_store(query, db, k=4):
    return db.similarity_search(query, k=k)
