from embeddings import get_embedding_model, load_config
from rag import load_and_split_documents, query_vector_store
from vector_store import build_vector_store, save_vector_store, load_vector_store
from mcp_utils import create_mcp_context
import json
import os

def main():
    config = load_config()
    embedding_model = get_embedding_model(config)

    if not os.path.exists(config["vector_store_path"]):
        docs = load_and_split_documents("example_docs/sample.txt", config["chunk_size"], config["chunk_overlap"])
        db = build_vector_store(docs, embedding_model, config)
        save_vector_store(db, config)
    else:
        db = load_vector_store(config, embedding_model)

    query = "What are the key payment terms?"
    results = query_vector_store(query, db)
    mcp_context = create_mcp_context(query, results)

    print(json.dumps(mcp_context, indent=2))

if __name__ == "__main__":
    main()
