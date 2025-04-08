def create_mcp_context(query, retrieved_docs):
    context_blocks = [
        {
            "type": "document",
            "role": "retriever",
            "name": f"chunk_{i}",
            "content": doc.page_content
        } for i, doc in enumerate(retrieved_docs)
    ]

    return {
        "metadata": {
            "query": query,
            "source": "vector_db_search",
            "retrieved_at": "2025-04-08"
        },
        "context": context_blocks
    }
