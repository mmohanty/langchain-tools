from rag.rag_tool import RAGTool
from rag.rag_config import RAGConfig
from vector_db.vector_db_config import VectorDBConfig
import unittest

class TestTools(unittest.TestCase):
    def setUp(self):
        print("Setup")

    def tearDown(self):
        print("Tear Down")

    def test_rag_tool_with_openai(self):
        rag_config = RAGConfig(
            file_type="txt",
            chunk_size=400,
            chunk_overlap=30,
            search_kwargs={"k": 3},
            llm_config={
                "provider": "openai",
                "model_name": "gpt-3.5-turbo-instruct",
                "temperature": 0.2
            }
        )

        vector_config = VectorDBConfig(
            db_type="faiss",
            persist_path="rag_index"
        )

        rag_tool = RAGTool(rag_config, vector_config)
        rag_tool.ingest_document("docs/example.txt")
        print(rag_tool.query("Summarize the main ideas in the document."))

    def test_rag_tool_with_anthropic(self):
        rag_config = RAGConfig(
            file_type="pdf",
            chunk_size=400,
            chunk_overlap=20,
            search_kwargs={"k": 5},
            llm_config={
                "provider": "anthropic",
                "model_name": "claude-2.1",
                "temperature": 0.2
            }
        )

        vector_config = VectorDBConfig(
            db_type="faiss",
            persist_path="rag_index"
        )

        rag_tool = RAGTool(rag_config, vector_config)
        rag_tool.ingest_document("docs/example.txt")
        print(rag_tool.query("Summarize the main ideas in the document."))

