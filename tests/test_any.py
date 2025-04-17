# text_to_sql_schema/readers/base.py
from abc import ABC, abstractmethod
from typing import Dict, TypedDict, Optional

class ColumnMeta(TypedDict):
    type: str
    description: Optional[str]


class TableSchema(TypedDict):
    description: Optional[str]
    columns: Dict[str, ColumnMeta]
    
class SchemaReader(ABC):
    @abstractmethod
    def get_schema(self) -> Dict[str, TableSchema]:
        """
        Returns schema in the form:
        {
          "users": {
            "description": "Contains user account info",
            "columns": {
              "id": { "type": "INTEGER", "description": "Unique user ID" },
              "name": { "type": "VARCHAR", "description": "User's full name" },
              ...
            }
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

    def get_schema(self) -> Dict[str, TableSchema]:
        with open(self.file_path) as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Schema must be a dict of table -> { column: type }")

        for table, meta in data.items():
            if not isinstance(meta, dict) or "columns" not in meta:
                raise ValueError(f"Invalid table schema format in '{table}'")

        return data


# text_to_sql_schema/readers/postgres.py
import psycopg2
from typing import Dict
from .base import SchemaReader

class PostgresSchemaReader(SchemaReader):
    def __init__(self, conn_details):
        self.conn_details = conn_details

    def get_schema(self) -> Dict[str, TableSchema]:
        conn = psycopg2.connect(**self.conn_details)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """)

        schema = {}
        for table, column, dtype in result.fetchall():
            if table not in schema:
                schema[table] = {
                    "description": None,
                    "columns": {}
                }

            schema[table]["columns"][column] = {
                "type": dtype,
                "description": None
            }

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

    def get_schema(self) -> Dict[str, TableSchema]:
        conn = pymysql.connect(**self.conn_details)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        schema: Dict[str, TableSchema] = {}

        for table in tables:
            cursor.execute(f"DESCRIBE `{table}`")
            columns = cursor.fetchall()
            schema[table] = {
                "description": None,
                "columns": {
                    col[0]: {
                        "type": col[1],
                        "description": None
                    } for col in columns
                }
            }

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

    def get_schema(self) -> Dict[str, TableSchema]:
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        # tables = [row[0] for row in cursor.fetchall()]

        schema = {}
        tables = [row[0] for row in cursor.fetchall()]

        schema: Dict[str, TableSchema] = {}

        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            schema[table] = {
                "description": None,
                "columns": {
                    col[1]: {
                        "type": col[2],
                        "description": None
                    } for col in columns
                }
            }

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

    def get_schema(self) -> Dict[str, TableSchema]:
        schema: Dict[str, TableSchema] = {}

        for coll_name in db.list_collection_names():
            doc = db[coll_name].find_one()
            schema[coll_name] = {
                "description": None,
                "columns": {
                    k: {
                        "type": type(v).__name__.upper(),
                        "description": None
                    } for k, v in (doc or {}).items()
                }
            }
        return schema


# text_to_sql_schema/readers/sqlserver.py
import pyodbc
from typing import Dict
from .base import SchemaReader

class SQLServerSchemaReader(SchemaReader):
    def __init__(self, conn_details):
        self.conn_details = conn_details

    def get_schema(self) -> Dict[str, TableSchema]:
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
        for table, column, dtype in result.fetchall():
            if table not in schema:
                schema[table] = {
                    "description": None,
                    "columns": {}
                }

            schema[table]["columns"][column] = {
                "type": dtype,
                "description": None
            }

        cursor.close()
        conn.close()
        return schema


# text_to_sql_schema/readers/oracle.py
import oracledb
from typing import Dict
from .base import SchemaReader, TableSchema

class OracleSchemaReader(SchemaReader):
    def __init__(self, conn_details):
        self.conn_details = conn_details

    def get_schema(self) -> Dict[str, TableSchema]:
        conn = oracledb.connect(
            user=self.conn_details["user"],
            password=self.conn_details["password"],
            dsn=oracledb.makedsn(
                self.conn_details["host"],
                self.conn_details["port"],
                service_name=self.conn_details["service_name"]
            )
        )

        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, column_name, data_type
            FROM all_tab_columns
            WHERE owner = :schema
            ORDER BY table_name, column_id
        """, schema=self.conn_details["schema"].upper())

        schema: Dict[str, TableSchema] = {}

        for table, column, dtype in cursor.fetchall():
            schema.setdefault(table, {
                "description": None,
                "columns": {}
            })
            schema[table]["columns"][column] = {
                "type": dtype,
                "description": None
            }

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
import json
import os
from dotenv import load_dotenv
from .readers.factory import get_schema_reader

load_dotenv()

SCHEMA_CACHE = None


class ConnectionDetailsFactory:
    _strategies = {}

    @classmethod
    def register(cls, db_type):
        def decorator(strategy_cls):
            cls._strategies[db_type] = strategy_cls()
            return strategy_cls
        return decorator

    @classmethod
    def get(cls, db_type):
        if db_type not in cls._strategies:
            raise ValueError(f"Unsupported db_type: {db_type}")
        return cls._strategies[db_type].get_connection_details()


@ConnectionDetailsFactory.register("postgres")
@ConnectionDetailsFactory.register("mysql")
class DefaultSQLStrategy:
    def get_connection_details(self):
        return {
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD")
        }


@ConnectionDetailsFactory.register("sqlite")
class SQLiteStrategy:
    def get_connection_details(self):
        return {
            "database": os.getenv("DB_NAME")
        }


@ConnectionDetailsFactory.register("oracle")
class OracleStrategy:
    def get_connection_details(self):
        return {
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT", 1521)),
            "service_name": os.getenv("DB_SERVICE_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "schema": os.getenv("DB_SCHEMA")
        }


@ConnectionDetailsFactory.register("mongodb")
class MongoDBStrategy:
    def get_connection_details(self):
        return {
            "uri": os.getenv("DB_URI"),
            "database": os.getenv("DB_NAME")
        }


@ConnectionDetailsFactory.register("sqlserver")
class SQLServerStrategy:
    def get_connection_details(self):
        return {
            "server": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT", 1433)),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "driver": os.getenv("DB_DRIVER")
        }

def enrich_schema_with_descriptions(
    schema: Dict[str, TableSchema],
    desc_file_path: str
) -> Dict[str, TableSchema]:
    if not desc_file_path or not os.path.exists(desc_file_path):
        return schema  # skip if not provided

    with open(desc_file_path, "r") as f:
        descriptions = json.load(f)

    for table_name, table_info in schema.items():
        # Add table-level description
        if table_name in descriptions:
            desc_entry = descriptions[table_name]
            table_info["description"] = desc_entry.get("description", table_info.get("description"))

            # Add column-level descriptions
            for col_name, col_info in table_info["columns"].items():
                if col_name in desc_entry.get("columns", {}):
                    col_info["description"] = desc_entry["columns"][col_name]

    return schema


def get_schema_from_db():
    db_type = os.getenv("DB_TYPE")
    source_type = os.getenv("SCHEMA_SOURCE", "db")
    file_path = os.getenv("SCHEMA_FILE")
    conn_details = ConnectionDetailsFactory.get(db_type)
    desc_file_path = os.getenv("SCHEMA_DESC_FILE")

    reader = get_schema_reader(
        source_type=source_type,
        db_type=db_type,
        conn_details=conn_details,
        file_path=file_path
    )
    raw_schema = reader.get_schema()
    return enrich_schema_with_descriptions(raw_schema, desc_file_path)


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
    for table, details in schema.items():
        lines.append(f"Table `{table}`: {details.get('description', '')}")
        for col, col_meta in details["columns"].items():
            lines.append(f"  - {col}: {col_meta['type']} — {col_meta.get('description', '')}")
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
