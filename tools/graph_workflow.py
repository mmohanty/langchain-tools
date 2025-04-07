# graph_workflow.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

from rag.rag_tool import RAGTool


# State type
class RAGState(TypedDict, total=False):
    file_path: str
    question: str
    answer: str
    ingest_result: str


rag_tool_instance = RAGTool()
# Functions as LangGraph nodes
def ingest_node(state: RAGState) -> RAGState:
    result = rag_tool_instance.ingest_document(state["file_path"])
    return {"ingest_result": result}

def query_node(state: RAGState) -> RAGState:
    answer = rag_tool_instance.query(state["question"])
    return {"answer": answer}


def build_rag_graph():
    builder = StateGraph(RAGState)

    builder.add_node("ingest", ingest_node)
    builder.add_node("query", query_node)

    # Define flow: ingest → query → END
    builder.set_entry_point("ingest")
    builder.add_edge("ingest", "query")
    builder.add_edge("query", END)

    return builder.compile()


if __name__ == '__main__':
    from graph_workflow import build_rag_graph

    app = build_rag_graph()

    inputs = {
        "file_path": "docs/example.pdf",
        "question": "What is the summary of this document?"
    }

    final_state = app.invoke(inputs)
    print("Final output:", final_state["answer"])
