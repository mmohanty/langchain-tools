# vector_db_tool.py
from vector_db_factory import get_vector_db
from vector_db_config import VectorDBConfig

class VectorDBTool:
    def __init__(self, config: VectorDBConfig):
        self.vector_db = get_vector_db(config)

    def add_texts(self, texts):
        return self.vector_db.add_texts(texts)

    def search(self, query, k=5):
        return self.vector_db.search(query, k)

    def clear(self):
        return self.vector_db.clear()
