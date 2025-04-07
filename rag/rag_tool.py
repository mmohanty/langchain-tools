# rag_tool.py
from rag_config import RAGConfig
from vector_db.vector_db_config import VectorDBConfig
from vector_db.vector_db_factory import get_vector_db
from llm.llm_loader import load_llm

from langchain.document_loaders import (
    TextLoader, PyPDFLoader, CSVLoader,
    UnstructuredHTMLLoader, UnstructuredWordDocumentLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

import os

class RAGTool:
    def __init__(self, rag_config: RAGConfig, vector_config: VectorDBConfig):
        self.rag_config = rag_config
        self.vector_db = get_vector_db(vector_config)

    def _get_loader(self, file_path: str):
        ext = self.rag_config.file_type or os.path.splitext(file_path)[-1][1:]
        ext = ext.lower()

        if ext == "pdf":
            return PyPDFLoader(file_path)
        elif ext in {"txt", "md"}:
            return TextLoader(file_path)
        elif ext == "csv":
            return CSVLoader(file_path)
        elif ext == "docx":
            return UnstructuredWordDocumentLoader(file_path)
        elif ext == "html":
            return UnstructuredHTMLLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def ingest_document(self, file_path: str):
        loader = self._get_loader(file_path)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.rag_config.chunk_size,
            chunk_overlap=self.rag_config.chunk_overlap,
        )
        chunks = splitter.split_documents(documents)
        self.vector_db.add_texts([chunk.page_content for chunk in chunks])
        return f"Ingested {len(chunks)} chunks from {file_path}"

    def query(self, question: str):
        retriever = self.vector_db.get_vectorstore().as_retriever(
            search_kwargs=self.rag_config.search_kwargs
        )

        llm = load_llm(self.rag_config.llm_config)
        qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
        return qa.run(question)
