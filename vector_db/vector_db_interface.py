# vector_db_interface.py
from typing import List
from langchain.vectorstores.base import VectorStore

class VectorDBInterface:
    def add_texts(self, texts: List[str]) -> str:
        raise NotImplementedError

    def search(self, query: str, k: int = 5) -> List[str]:
        raise NotImplementedError

    def clear(self) -> str:
        raise NotImplementedError

    def save(self):
        raise NotImplementedError

    def get_vectorstore(self) -> VectorStore:
        raise NotImplementedError
