# vector_db_factory.py
from langchain.embeddings import OpenAIEmbeddings
from vector_db_interface import VectorDBInterface
from vector_db_config import VectorDBConfig

# backends
from langchain.vectorstores import FAISS, Qdrant, Pinecone
from qdrant_client import QdrantClient
import pinecone

class FAISSDB(VectorDBInterface):
    def __init__(self, config: VectorDBConfig):
        self.config = config
        self.embeddings = OpenAIEmbeddings()
        try:
            self.vectorstore = FAISS.load_local(config.persist_path, self.embeddings)
        except:
            self.vectorstore = FAISS.from_texts([], self.embeddings)

    def add_texts(self, texts):
        self.vectorstore.add_texts(texts)
        self.save()
        return f"Added {len(texts)} texts"

    def search(self, query, k=5):
        return [doc.page_content for doc in self.vectorstore.similarity_search(query, k=k)]

    def clear(self):
        self.vectorstore = FAISS.from_texts([], self.embeddings)
        self.save()
        return "FAISS index cleared"

    def save(self):
        self.vectorstore.save_local(self.config.persist_path)

    def get_vectorstore(self):
        return self.vectorstore

class QdrantDB(VectorDBInterface):
    def __init__(self, config: VectorDBConfig):
        self.embeddings = OpenAIEmbeddings()
        self.qdrant = Qdrant(
            client=QdrantClient(url=config.qdrant_url),
            collection_name="rag_collection",
            embeddings=self.embeddings,
        )

    def add_texts(self, texts):
        self.qdrant.add_texts(texts)
        return f"Added {len(texts)} texts"

    def search(self, query, k=5):
        return [doc.page_content for doc in self.qdrant.similarity_search(query, k=k)]

    def clear(self):
        self.qdrant.delete_collection()
        return "Qdrant index cleared"

    def save(self): pass
    def get_vectorstore(self):
        return self.qdrant

class PineconeDB(VectorDBInterface):
    def __init__(self, config: VectorDBConfig):
        self.embeddings = OpenAIEmbeddings()
        pinecone.init(api_key=config.pinecone_api_key, environment=config.pinecone_env)
        index = pinecone.Index(config.pinecone_index)
        self.pinecone = Pinecone(index, self.embeddings.embed_query, "text")

    def add_texts(self, texts):
        self.pinecone.add_texts(texts)
        return f"Added {len(texts)} texts"

    def search(self, query, k=5):
        return [doc.page_content for doc in self.pinecone.similarity_search(query, k=k)]

    def clear(self):
        # NOTE: This clears the whole index; handle with care.
        raise NotImplementedError("Clear operation not implemented for Pinecone.")

    def save(self): pass
    def get_vectorstore(self):
        return self.pinecone

def get_vector_db(config: VectorDBConfig) -> VectorDBInterface:
    db_map = {
        "faiss": FAISSDB,
        "qdrant": QdrantDB,
        "pinecone": PineconeDB,
    }
    if config.db_type not in db_map:
        raise ValueError(f"Unsupported DB type: {config.db_type}")
    return db_map[config.db_type](config)
