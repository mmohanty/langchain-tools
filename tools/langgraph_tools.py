# langgraph_tools.py
from langchain_core.tools import tool

from rag.rag_tool import RAGTool
from vector_db.vector_db_tool import VectorDBTool

rag_tool = RAGTool()
vector_tool = VectorDBTool()

@tool
def ingest_rag_document(file_path: str) -> str:
    return rag_tool.ingest_document(file_path)

@tool
def query_rag(question: str) -> str:
    return rag_tool.query(question)

@tool
def add_to_vector_db(texts: list[str]) -> str:
    return vector_tool.add_texts(texts)

@tool
def search_vector_db(query: str, k: int = 5) -> list[str]:
    return vector_tool.search(query, k)

@tool
def clear_vector_db() -> str:
    return vector_tool.clear()


from langgraph.graph import Graph

graph = Graph()

graph.add_tool(ingest_rag_document)
graph.add_tool(query_rag)
graph.add_tool(add_to_vector_db)
graph.add_tool(search_vector_db)
graph.add_tool(clear_vector_db)
