# rag_config.py
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class RAGConfig:
    chunk_size: int = 500
    chunk_overlap: int = 50
    file_type: str = "pdf"
    search_kwargs: Dict = field(default_factory=lambda: {"k": 5})
    llm_config: Dict = field(default_factory=lambda: {
        "provider": "openai",  # openai, anthropic, cohere, hf
        "model_name": "gpt-3.5-turbo-instruct",
        "temperature": 0.3
    })
