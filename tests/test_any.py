# text_to_sql_schema/readers/base.py
from abc import ABC, abstractmethod
from typing import Dict

class SchemaReader(ABC):
    @abstractmethod
    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Returns schema in the form:
        {
            "table_name": {
                "column_name": "DATA_TYPE"
            }
        }
        """
        pass


# text_to_sql_schema/readers/json_reader.py
import json
from typing import Dict
from .base import SchemaReader

class JSONSchemaReader(SchemaReader):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        with open(self.file_path) as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Schema must be a dict of table -> { column: type }")

        for table, columns in data.items():
            if not isinstance(columns, dict):
                raise ValueError(f"Columns for table '{table}' must be a dict")

        return data


# text_to_sql_schema/readers/postgres.py
import psycopg2
from typing import Dict
from .base import SchemaReader

class PostgresSchemaReader(SchemaReader):
    def __init__(self, conn_details):
        self.conn_details = conn_details

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        conn = psycopg2.connect(**self.conn_details)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """)

        schema = {}
        for table, column, dtype in cursor.fetchall():
            schema.setdefault(table, {})[column] = dtype

        cursor.close()
        conn.close()
        return schema


# text_to_sql_schema/readers/mysql.py
import pymysql
from typing import Dict
from .base import SchemaReader

class MySQLSchemaReader(SchemaReader):
    def __init__(self, conn_details):
        self.conn_details = conn_details

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        conn = pymysql.connect(**self.conn_details)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        schema = {}
        for table in tables:
            cursor.execute(f"DESCRIBE {table}")
            for col in cursor.fetchall():
                schema.setdefault(table, {})[col[0]] = col[1]

        cursor.close()
        conn.close()
        return schema


# text_to_sql_schema/readers/sqlite.py
import sqlite3
from typing import Dict
from .base import SchemaReader

class SQLiteSchemaReader(SchemaReader):
    def __init__(self, conn_details):
        self.database = conn_details["database"]

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            for row in cursor.fetchall():
                schema.setdefault(table, {})[row[1]] = row[2]

        cursor.close()
        conn.close()
        return schema


# text_to_sql_schema/readers/mongo.py
from pymongo import MongoClient
from typing import Dict
from .base import SchemaReader

class MongoSchemaReader(SchemaReader):
    def __init__(self, conn_details):
        self.client = MongoClient(conn_details["uri"])
        self.database = self.client[conn_details["database"]]

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        schema = {}
        for collection_name in self.database.list_collection_names():
            doc = self.database[collection_name].find_one()
            if doc:
                schema[collection_name] = {k: type(v).__name__ for k, v in doc.items() if k != '_id'}
        return schema


# text_to_sql_schema/readers/sqlserver.py
import pyodbc
from typing import Dict
from .base import SchemaReader

class SQLServerSchemaReader(SchemaReader):
    def __init__(self, conn_details):
        self.conn_details = conn_details

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        conn_str = (
            f"DRIVER={self.conn_details['driver']};"
            f"SERVER={self.conn_details['server']};"
            f"DATABASE={self.conn_details['database']};"
            f"UID={self.conn_details['user']};"
            f"PWD={self.conn_details['password']};"
            f"TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            ORDER BY TABLE_NAME, ORDINAL_POSITION
        """)

        schema = {}
        for table, column, dtype in cursor.fetchall():
            schema.setdefault(table, {})[column] = dtype

        cursor.close()
        conn.close()
        return schema


# text_to_sql_schema/readers/factory.py
import os
from .postgres import PostgresSchemaReader
from .mysql import MySQLSchemaReader
from .sqlite import SQLiteSchemaReader
from .mongo import MongoSchemaReader
from .sqlserver import SQLServerSchemaReader
from .json_reader import JSONSchemaReader


def get_schema_reader(source_type: str, db_type: str = None, conn_details: dict = None, file_path: str = None):
    if source_type == "json":
        return JSONSchemaReader(file_path)
    elif source_type == "db":
        if db_type == "postgres":
            return PostgresSchemaReader(conn_details)
        elif db_type == "mysql":
            return MySQLSchemaReader(conn_details)
        elif db_type == "sqlite":
            return SQLiteSchemaReader(conn_details)
        elif db_type == "mongodb":
            return MongoSchemaReader(conn_details)
        elif db_type == "sqlserver":
            return SQLServerSchemaReader(conn_details)
        else:
            raise ValueError(f"Unsupported db_type: {db_type}")
    else:
        raise ValueError(f"Unsupported source_type: {source_type}")

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
