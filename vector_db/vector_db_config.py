# vector_db_config.py
from dataclasses import dataclass

@dataclass
class VectorDBConfig:
    db_type: str  # e.g., "faiss", "qdrant", "pinecone"
    persist_path: str = "index"
    qdrant_url: str = None
    pinecone_index: str = None
    pinecone_env: str = None
    pinecone_api_key: str = None
