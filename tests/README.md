
# 📘 Schema Reader Framework (Text-to-SQL via MCP)

This framework enables LLM agents (Autogen, LangGraph, etc.) to generate SQL queries from natural language by understanding your database schema. It supports multi-DB introspection, schema filtering, prompt embedding, and in-memory caching.

---

## ✅ Features

- 🔌 **Multi-DB Support**: PostgreSQL, MySQL, SQLite, Oracle, MongoDB, SQL Server (via SQLAlchemy + pymssql)
- 📄 **Static Option**: Read schema from `.json` instead of live DB
- 🔁 **Strategy Pattern**: Dynamically builds DB connection info per `DB_TYPE`
- 🎯 **Optional Table Filtering**: filter schema by `exact`, `starts_with`, `ends_with`
- 🧠 **In-Memory Caching**: schema and LLM prompt only loaded once
- 💬 **Custom Prompt Embedding**: inject your system prompt into `schema_to_prompt`
- 🔧 **MCP-compatible Tools**: `text_to_sql(query: str)` only (lightweight and fast)

---

## 🧱 Project Layout

```
text_to_sql_schema/
├── readers/                # Schema readers per DB
│   ├── base.py
│   ├── postgres.py
│   ├── mysql.py
│   ├── sqlite.py
│   ├── oracle.py
│   ├── mongo.py
│   ├── sqlserver.py        # Uses sqlalchemy + pymssql (TDS)
│   └── json_reader.py
├── schema.py               # Loads + filters schema + formats prompt
├── factory.py              # Strategy pattern for connection details
├── tools.py                # MCP tool entrypoint
└── .env                    # DB configs and table filter rules
```

---

## 🔧 .env Example

```env
DB_TYPE=sqlserver
SCHEMA_SOURCE=db

DB_HOST=localhost
DB_PORT=1433
DB_NAME=mydb
DB_USER=sa
DB_PASSWORD=yourpass

INCLUDE_TABLES_EXACT=users,orders
INCLUDE_TABLES_STARTS_WITH=user_
INCLUDE_TABLES_ENDS_WITH=_log

# Optional custom system prompt
SYSTEM_PROMPT_PREFIX=You are an expert SQL generator AI.
```

---

## ⚙️ Tool Entry Point

```bash
uvx text_to_sql_schema.tools
```

Used via `StdioServerParams` in an Autogen Agent:

```python
ToolConfig(
    name="text_to_sql_tools",
    server=StdioServerParams(
        command="uvx",
        args=["text_to_sql_schema.tools"],
        env=dict(os.environ)  # or your custom dict
    )
)
```

---

## 🧠 Prompt Design (schema_to_prompt)

Embeds a custom system prompt before the generated schema.

```
The database has the following tables and columns:

Table `users`:
  - id: INTEGER
  - name: VARCHAR
  ...
```

This is:
- Generated **once** at startup
- Cached in memory
- Used in every call to `text_to_sql()`

---

## 🛠️ Available Tools

| Tool           | Description |
|----------------|-------------|
| `text_to_sql`  | Generates SQL string using natural language + embedded schema context |

> 🔥 `reload_schema()` tool has been removed — schema is loaded once at startup for performance.

---

## 📦 Install Dependencies

```bash
pip install python-dotenv sqlalchemy pymssql
```
