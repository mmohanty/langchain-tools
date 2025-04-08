from langgraph.graph import StateGraph, END
from langchain.chat_models import ChatOpenAI
from typing import Dict, Any

llm = ChatOpenAI(temperature=0, model="gpt-4")

# Step 1: Define a simple function to simulate a tool
def read_context_tool(mcp_context: dict) -> str:
    content = "\n\n".join([c["content"] for c in mcp_context.get("context", [])])
    return f"Context Retrieved from MCP:\n{content}"

# Step 2: Define agent node (basic decision node for now)
def agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state["query"]
    mcp = state["mcp"]

    context_preview = read_context_tool(mcp)

    prompt = f"""You are an AI assistant using retrieved document context to answer questions.

Context:
{context_preview}

Question: {query}
Answer:"""

    response = llm.invoke(prompt).content
    return {"query": query, "mcp": mcp, "response": response}

# Optional tool node (can be expanded later)
def tool_node(state: Dict[str, Any]) -> Dict[str, Any]:
    tool_output = read_context_tool(state["mcp"])
    return {"query": state["query"], "mcp": state["mcp"], "response": tool_output}

# Step 3: Build LangGraph
def build_graph():
    builder = StateGraph()
    builder.add_node("agent", agent_node)
    # Optional: builder.add_node("tool", tool_node)
    builder.set_entry_point("agent")
    builder.add_edge("agent", END)
    return builder.compile()

graph = build_graph()

# Step 4: Entry function for FastAPI
async def run_agent(query: str, mcp_context: dict):
    initial_state = {"query": query, "mcp": mcp_context}
    result = await graph.ainvoke(initial_state)
    return result["response"]
