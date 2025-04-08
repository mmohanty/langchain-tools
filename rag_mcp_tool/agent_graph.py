from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor, tool
from langchain.chat_models import ChatOpenAI
from langchain.tools.render import render_text_description

llm = ChatOpenAI(temperature=0, model="gpt-4")

# Simple tool that echoes the MCP context
@tool
def read_context_tool(context: dict) -> str:
    content = "\n\n".join([c["content"] for c in context.get("context", [])])
    return f"Retrieved Context:\n{content}"

tools = [read_context_tool]
tool_executor = ToolExecutor(tools)

# Node 1: Decide to use a tool or respond
def agent_node(state):
    query, context = state["query"], state["mcp"]
    tools_text = render_text_description(tools)
    prompt = f"""You are an assistant. Answer this query using tools if needed.

Context:
{tools_text}

User Query: {query}
"""
    return {
        "query": query,
        "mcp": context,
        "response": llm.invoke(prompt).content
    }

# Node 2: Execute tool
def tool_node(state):
    result = tool_executor.invoke({"context": state["mcp"]})
    return {"query": state["query"], "mcp": state["mcp"], "response": result}

# Build LangGraph
def build_graph():
    builder = StateGraph()
    builder.add_node("agent", agent_node)
    builder.add_node("tool", tool_node)

    builder.set_entry_point("agent")
    builder.add_edge("agent", "tool")
    builder.add_edge("tool", END)

    return builder.compile()

graph = build_graph()

async def run_agent(query: str, mcp_context: dict):
    state = {"query": query, "mcp": mcp_context}
    result = await graph.ainvoke(state)
    return result["response"]
