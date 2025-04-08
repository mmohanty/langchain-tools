from fastapi import FastAPI, Query
from pydantic import BaseModel
from embeddings import load_config, get_embedding_model
from rag import load_and_split_documents, query_vector_store
from vector_store import load_vector_store
from mcp_utils import create_mcp_context
from rag_mcp_tool.agent_graph import run_agent

config = load_config()
embedding_model = get_embedding_model(config)
db = load_vector_store(config, embedding_model)

app = FastAPI(title="RAG MCP LangGraph API")

class QueryRequest(BaseModel):
    query: str

@app.post("/query/")
async def query_docs(request: QueryRequest):
    docs = query_vector_store(request.query, db)
    mcp = create_mcp_context(request.query, docs)
    return mcp

@app.post("/agent/")
async def agent_response(request: QueryRequest):
    docs = query_vector_store(request.query, db)
    mcp = create_mcp_context(request.query, docs)
    answer = await run_agent(request.query, mcp)
    return {"response": answer}
