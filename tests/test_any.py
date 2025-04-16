# text_to_sql_schema/schema.py
import os
from dotenv import load_dotenv
from .readers.factory import get_schema_reader

load_dotenv()

SCHEMA_CACHE = None


def get_schema_from_db():
    db_type = os.getenv("DB_TYPE")
    source_type = os.getenv("SCHEMA_SOURCE", "db")
    file_path = os.getenv("SCHEMA_FILE")

    conn_details = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "service_name": os.getenv("DB_SERVICE_NAME"),
        "driver": os.getenv("DB_DRIVER"),
        "uri": os.getenv("DB_URI")
    }

    reader = get_schema_reader(
        source_type=source_type,
        db_type=db_type,
        conn_details=conn_details,
        file_path=file_path
    )
    return reader.get_schema()


def filter_tables(schema: dict, include: dict) -> dict:
    """
    Filters tables based on criteria:
    include = {
        "exact": ["users", "orders"],
        "starts_with": ["user_"],
        "ends_with": ["_log"]
    }
    """
    def match(table_name: str) -> bool:
        return (
            table_name in include.get("exact", []) or
            any(table_name.startswith(prefix) for prefix in include.get("starts_with", [])) or
            any(table_name.endswith(suffix) for suffix in include.get("ends_with", []))
        )

    return {table: columns for table, columns in schema.items() if match(table)}


def get_or_load_cached_schema():
    global SCHEMA_CACHE
    if SCHEMA_CACHE is None:
        full_schema = get_schema_from_db()
        include = {
            "exact": os.getenv("INCLUDE_TABLES_EXACT", "").split(",") if os.getenv("INCLUDE_TABLES_EXACT") else [],
            "starts_with": os.getenv("INCLUDE_TABLES_STARTS_WITH", "").split(",") if os.getenv("INCLUDE_TABLES_STARTS_WITH") else [],
            "ends_with": os.getenv("INCLUDE_TABLES_ENDS_WITH", "").split(",") if os.getenv("INCLUDE_TABLES_ENDS_WITH") else []
        }
        SCHEMA_CACHE = filter_tables(full_schema, include) if any(include.values()) else full_schema
    return SCHEMA_CACHE


def schema_to_prompt(schema: dict) -> str:
    lines = ["The database has the following tables and columns:\n"]
    for table, columns in schema.items():
        lines.append(f"Table `{table}`:")
        for col, dtype in columns.items():
            lines.append(f"  - {col}: {dtype}")
        lines.append("")
    return "\n".join(lines)


# text_to_sql_schema/tools.py
from mcp import tool, tool_server
from .schema import get_or_load_cached_schema, get_schema_from_db, schema_to_prompt
from your_sql_generation_module import generate_sql_from_text

SCHEMA = get_or_load_cached_schema()
SCHEMA_PROMPT = schema_to_prompt(SCHEMA)


@tool
def text_to_sql(query: str) -> str:
    return generate_sql_from_text(query, SCHEMA_PROMPT)


@tool
def reload_schema() -> str:
    global SCHEMA, SCHEMA_PROMPT
    SCHEMA = get_or_load_cached_schema()
    SCHEMA_PROMPT = schema_to_prompt(SCHEMA)
    return "Schema reloaded successfully."


if __name__ == "__main__":
    tool_server([text_to_sql, reload_schema]).run()
