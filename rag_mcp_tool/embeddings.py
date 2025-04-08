import yaml


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def get_embedding_model(config):
    if config["embedding_model"] == "openai":
        from langchain.embeddings import OpenAIEmbeddings
        return OpenAIEmbeddings(openai_api_key=config["openai_api_key"])

    elif config["embedding_model"] == "huggingface":
        from langchain.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings()

    raise ValueError("Unsupported embedding model specified.")
