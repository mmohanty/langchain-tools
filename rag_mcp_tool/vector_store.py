from langchain.vectorstores import FAISS
# Future: from langchain.vectorstores import Chroma, Qdrant

def build_vector_store(docs, embedding_model, config):
    if config["vector_store"] == "faiss":
        return FAISS.from_documents(docs, embedding_model)
    raise NotImplementedError("Only FAISS is supported right now.")

def save_vector_store(db, config):
    if config["vector_store"] == "faiss":
        db.save_local(config["vector_store_path"])

def load_vector_store(config, embedding_model):
    if config["vector_store"] == "faiss":
        return FAISS.load_local(config["vector_store_path"], embedding_model, allow_dangerous_deserialization=True)
