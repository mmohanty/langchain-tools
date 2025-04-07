# llm_loader.py
from langchain.llms import OpenAI, Cohere, HuggingFaceHub
from langchain.chat_models import ChatAnthropic
from typing import Dict

def load_llm(llm_config: Dict):
    provider = llm_config.get("provider", "openai").lower()
    model_name = llm_config.get("model_name")
    temperature = llm_config.get("temperature", 0.3)

    if provider == "openai":
        return OpenAI(model_name=model_name, temperature=temperature)
    elif provider == "anthropic":
        return ChatAnthropic(model=model_name, temperature=temperature)
    elif provider == "cohere":
        return Cohere(model=llm_config.get("model_name"), temperature=temperature)
    elif provider == "hf":
        return HuggingFaceHub(repo_id=model_name, model_kwargs={"temperature": temperature})
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
