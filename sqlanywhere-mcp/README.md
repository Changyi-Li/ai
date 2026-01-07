# SQL Anywhere MCP Server

A Model Context Protocol (MCP) server for connecting to SAP SQL Anywhere databases via ODBC. This server enables LLMs to explore database schemas and execute data queries safely.

## Quick Start (Windows)

```powershell
# 1. Navigate to project
cd sqlanywhere-mcp

# 2. Install dependencies
python -m pip install mcp pyodbc python-dotenv pydantic

# 3. Configure connection
copy .env.example .env
# Edit .env with your database credentials

# 4. Test with MCP Inspector
npx @modelcontextprotocol/inspector python -m sqlanywhere_mcp.server
```

## Features

- **Schema Discovery**: Retrieve tables, columns, views, stored procedures, indexes, and keys using modern SQL Anywhere system views
- **Name Search**: Case-insensitive substring search for tables, views, and procedures
- **Security Filtering**: Expose only objects from authorized users (configured via SQLANYWHERE_AUTHORIZED_USERS)
- **Data Queries**: Execute SELECT queries with configurable row limits
- **Safe Operations**: Read-only access with comprehensive safety constraints
- **Structured Output**: Both human-readable Markdown and machine-readable JSON

## Prerequisites

1. **Python**: 3.10 or higher
   - Verify installation: `python --version` or `py --version`
2. **SQL Anywhere ODBC Driver**

## Installation

### 1. Install Dependencies

**Windows (PowerShell or CMD)**:

```powershell
# Navigate to project directory
cd sqlanywhere-mcp

# Install dependencies (recommended)
python -m pip install mcp pyodbc python-dotenv pydantic

# Alternative: use py launcher if python is not in PATH
py -m pip install mcp pyodbc python-dotenv pydantic

# Or install the package in editable mode
python -m pip install -e .
```

**Linux/macOS**:

```bash
cd sqlanywhere-mcp
pip install -e .
```

**Using uv (faster alternative)**:

```bash
uv pip install -e .
```

**Troubleshooting pip issues**:

- If `pip` is not found, use `python -m pip` instead
- If `python` is not found, try `py` (Windows launcher) or install Python
- Verify Python is installed: `python --version` or `py --version`

### 3. Configure Connection

Copy `.env.example` to `.env`:

**Windows**:

```powershell
copy .env.example .env
```

**Linux/macOS**:

```bash
cp .env.example .env
```

Edit `.env` with your database connection details:

```bash
# Option 1: Connection string (recommended)
# SQL Anywhere uses DBN parameter (not DATABASE)
# For shared memory (default, fastest for local):
SQLANYWHERE_CONNECTION_STRING="DRIVER={SQL Anywhere 17};ServerName=myserver;DBN=mydb;UID=dba;PWD=password"

# For TCP/IP connections:
# SQLANYWHERE_CONNECTION_STRING="DRIVER={SQL Anywhere 17};ServerName=myserver;Host=localhost:2638;DBN=mydb;UID=dba;PWD=password"

# Option 2: Individual parameters
SQLANYWHERE_SERVER_NAME=myserver  # (REQUIRED) Server name
SQLANYWHERE_DATABASE=mydb         # (REQUIRED) Maps to DBN parameter
SQLANYWHERE_USER=dba              # (REQUIRED) Maps to UID
SQLANYWHERE_PASSWORD=password     # (REQUIRED) Maps to PWD
# SQLANYWHERE_USE_TCP=true         # Force TCP/IP instead of shared memory

# Security Settings
SQLANYWHERE_AUTHORIZED_USERS=monitor,ExtensionsUser  # Only expose objects from these users

# Query Settings
SQLANYWHERE_QUERY_TIMEOUT=30  # Query timeout in seconds
SQLANYWHERE_MAX_ROWS=1000      # Default row limit for queries
SQLANYWHERE_MAX_ROWS_LIMIT=10000  # Maximum allowed row limit
```

**Important SQL Anywhere Connection Notes**:

- Use `DBN` (DataBase Name) parameter, not `DATABASE`
- When using Option 2 (individual parameters), all four are required: `SQLANYWHERE_SERVER_NAME`, `SQLANYWHERE_DATABASE`, `SQLANYWHERE_USER`, `SQLANYWHERE_PASSWORD`
- For local connections, shared memory is default and fastest (no host/port needed)
- Use `Host=hostname:port` for TCP/IP connections
- Only include host/port if using TCP/IP protocol or connecting to remote server

### 4. ODBC Driver Setup

**Windows**:

- The ODBC driver is typically installed with SQL Anywhere
- Verify driver name in ODBC Data Source Administrator (odbcad32.exe)

**Linux**:

- Install the SQL Anywhere ODBC driver package
- Configure `/etc/odbcinst.ini` to register the driver

### 4. Verify Installation

Test that the package is installed correctly:

**Windows**:

```powershell
# Check if package can be imported
python -c "import sqlanywhere_mcp; print('Installation successful!')"

# List installed packages
python -m pip list | findstr sqlanywhere
```

**Linux/macOS**:

```bash
# Check if package can be imported
python -c "import sqlanywhere_mcp; print('Installation successful!')"

# List installed packages
pip list | grep sqlanywhere
```

## Usage

### With MCP Inspector (Testing)

```bash
npx @modelcontextprotocol/inspector python -m sqlanywhere_mcp.server
```

### With Claude Desktop

Add to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sqlanywhere": {
      "command": "python",
      "args": ["-m", "sqlanywhere_mcp.server"],
      "env": {
        "SQLANYWHERE_CONNECTION_STRING": "DRIVER={SQL Anywhere 17};DBN=mydb;UID=dba;PWD=password"
      }
    }
  }
}
```

## Available Tools

### Connection Management

#### `sqlanywhere_connect`

Establish connection to SQL Anywhere database. Usually automatic, but can be called explicitly.

### Schema Discovery

#### `sqlanywhere_list_tables`

List all tables in the database with metadata (owner, type, row count).
Only exposes tables created by authorized users (configured via SQLANYWHERE_AUTHORIZED_USERS).

**Parameters**:

- `owner` (optional): Filter by owner
- `search` (optional): Search for tables by name substring (case-insensitive, mutually exclusive with owner)
  - Example: 'part' matches 'PartTable', 'OrderPart', 'PartDetail'
- `limit` (optional): Maximum number of tables to return (default: 100)
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: Table names, owners, types, and row counts

#### `sqlanywhere_get_table_details`

Get comprehensive metadata for a specific table.

**Parameters**:

- `table_name` (required): Name of the table

**Returns**:

- Column information (name, type, length, nullable, default)
- Primary keys
- Foreign keys with references
- Indexes
- Check constraints

#### `sqlanywhere_list_views`

List all views in the database.

**Parameters**:

- `owner` (optional): Filter by owner
- `search` (optional): Search for views by name substring (case-insensitive, mutually exclusive with owner)
  - Example: 'customer' matches 'CustomerView', 'AllCustomers', 'CustomerSummary'
- `limit` (optional): Maximum number of views to return (default: 100)
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: View names, owners, and definitions

#### `sqlanywhere_get_view_details`

Get detailed information about a specific view.

**Parameters**:

- `view_name` (required): Name of the view

**Returns**:

- View definition SQL
- Column information

#### `sqlanywhere_list_procedures`

List all stored procedures and functions.

**Parameters**:

- `owner` (optional): Filter by owner
- `search` (optional): Search for procedures by name substring (case-insensitive, mutually exclusive with owner)
  - Example: 'get' matches 'GetUser', 'getUserById', 'get_customer_data'
- `limit` (optional): Maximum number of procedures to return (default: 100)
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: Procedure names, types, owners, and parameter counts

#### `sqlanywhere_get_procedure_details`

Get detailed information about a specific procedure.

**Parameters**:

- `procedure_name` (required): Name of the procedure

**Returns**:

- Parameter definitions
- Return type
- Procedure definition (if available)

#### `sqlanywhere_list_indexes`

List all indexes in the database.

**Parameters**:

- `table_name` (optional): Filter by specific table
- `limit` (optional): Maximum number of indexes to return

**Returns**: Index names, associated tables, uniqueness, and columns

#### `sqlanywhere_get_index_details`

Get detailed information about a specific index.

**Parameters**:

- `index_name` (required): Name of the index

**Returns**:

- Index column details
- Column ordering (ASC/DESC)
- Sequence information

### Data Queries

#### `sqlanywhere_execute_query`

Execute a SELECT query on the database.

**Parameters**:

- `query` (required): SQL SELECT query
- `limit` (optional): Maximum rows to return (default: 1000, max: 10000)

**Returns**: Query results with metadata (row count, execution time, column types)

**Safety**: Only SELECT queries are allowed. INSERT, UPDATE, DELETE, DDL are blocked.

#### `sqlanywhere_query_builder`

Build and execute a simple SELECT query with parameters.

**Parameters**:

- `table_name` (required): Table to query with owner prefix
  - Format must be: `owner.TableName`
  - Examples: `monitor.Part`, `dbo.Customers`, `ExtensionsUser.Config`
- `columns` (optional): Columns to select (default: \*)
- `where` (optional): WHERE clause (parameterized)
- `order_by` (optional): ORDER BY clause
- `limit` (optional): Row limit (default: 100)

**Returns**: Query results with metadata

**Note**: SQL Anywhere uses `TOP` instead of `LIMIT`. The query builder automatically generates correct SQL syntax.

#### `sqlanywhere_validate_query`

Validate a SQL query without executing it.

**Parameters**:

- `query` (required): SQL query to validate

**Returns**: Validation result with error messages if invalid

### Database Information

#### `sqlanywhere_get_database_info`

Get database metadata and connection information.

**Returns**: Database name, version, charset, collation, connection details

## Examples

### Search for tables by name

```python
# Search for tables containing 'part'
sqlanywhere_list_tables(search="part")

# Result from sqlanywhere_list_tables
Tables: 3 (showing only authorized users)
- monitor.Part (BASE, 9 rows)
- monitor.OrderPart (BASE, 523 rows)
- monitor.SparePart (BASE, 12 rows)

# Case-insensitive search (same results)
sqlanywhere_list_tables(search="PART")
sqlanywhere_list_tables(search="Part")
```

### Search for views by name

```python
# Search for views containing 'customer'
sqlanywhere_list_views(search="customer", limit=5)

# Result from sqlanywhere_list_views
Views: 2 (showing only authorized users)
- monitor.CustomerView (VIEW)
- monitor.AllCustomers (VIEW)
```

### Search for procedures by name

```python
# Search for procedures containing 'get'
sqlanywhere_list_procedures(search="get", limit=10)

# Result from sqlanywhere_list_procedures
Procedures & Functions: 8 (showing only authorized users)
- monitor.GetUserById (PROCEDURE)
- monitor.GetCustomerData (PROCEDURE)
- monitor.get_order_status (PROCEDURE)
```

### List all tables

```python
# Result from sqlanywhere_list_tables
Tables: 25 (showing only authorized users)
- monitor.Part (BASE, 9 rows)
- ExtensionsUser.Config (BASE, 15 rows)
- dbo.Customers (BASE, 1523 rows)
```

### Get table schema

```python
# Result from sqlanywhere_get_table_details(table_name="monitor.Part")
Table: monitor.Part

**Type**: BASE
**Row Count**: 9

Columns (134):
- Id (bigint, NOT NULL)
- CompanyId (bigint)
- PartNumber (nvarchar(20), NOT NULL)
- Description (nvarchar(400), NOT NULL)
- Type (integer, NOT NULL)
- ...

Primary Keys:
- Part: Id

Foreign Keys:
- bk_Part_CompanyId: → Company(Company)
- bk_Part_ProductGroupId: → ProductGroup(ProductGroup)
- ...

Indexes:
- Part (Primary Key): (Id ASC)
- idx_part_Description: (Description ASC)
- ...
```

### Query with owner-qualified table name

```python
# Using query_builder with owner prefix
sqlanywhere_query_builder(
    table_name="monitor.Part",
    columns="Id,PartNumber,Description",
    limit=5
)

# Result:
## Query Results

**Rows returned**: 5
**Execution time**: 0.015 seconds

| Id | PartNumber | Description |
|----|------------|-------------|
| 1 | PART-001   | Sample Part 1 |
| 2 | PART-002   | Sample Part 2 |
| ...
```

### Execute custom SELECT query

```python
# Result from sqlanywhere_execute_query
sqlanywhere_execute_query(
    query="SELECT Id, PartNumber, Type FROM monitor.Part WHERE Type = 1",
    limit=10
)

Query returned 10 rows in 0.012 seconds

Id | PartNumber | Type
----|------------|------
1  | PART-001   | 1
2  | PART-002   | 1
...
```

## Security

- **Read-Only**: `execute_query` only allows SELECT statements
- **User Filtering**: `SQLANYWHERE_AUTHORIZED_USERS` environment variable restricts object exposure to only specified users
- **Modern System Views**: Uses SQL Anywhere modern system views (SYS.SYSTAB, SYS.SYSTABCOL, etc.) with security filtering
- **Row Limits**: Configurable maximum row limits prevent large result sets
- **Connection Security**: Supports encrypted connections via ODBC parameters
- **Credential Management**: Use environment variables, never hardcode credentials
- **SQL Injection**: All queries use parameterized bindings and input validation

## Troubleshooting

### Installation Issues

**Error**: `pip: command not found` (Windows)

**Solution**:

- Use `python -m pip` instead of `pip`:
  ```powershell
  python -m pip install mcp pyodbc python-dotenv pydantic
  ```
- If `python` is not found, try the Windows launcher:
  ```powershell
  py -m pip install mcp pyodbc python-dotenv pydantic
  ```
- Verify Python installation:
  ```powershell
  python --version
  # or
  py --version
  ```

**Error**: `Access denied` during installation

**Solution**:

- Run PowerShell as Administrator
- Or install to user directory:
  ```powershell
  python -m pip install --user mcp pyodbc python-dotenv pydantic
  ```

### Connection Issues

**Error**: `[SAP][ODBC Driver][SQL Anywhere]Database server not found (-100)`

**Solution**:

This error means incorrect connection parameters. SQL Anywhere uses specific parameter names:

1. **Use DBN instead of DATABASE**:

   ```env
   # Wrong:
   SQLANYWHERE_CONNECTION_STRING="DRIVER={SQL Anywhere 17};DATABASE=mydb;UID=dba;PWD=sql"

   # Correct:
   SQLANYWHERE_CONNECTION_STRING="DRIVER={SQL Anywhere 17};DBN=mydb;UID=dba;PWD=sql"
   ```

2. **Include ServerName in all connections**:

   ```env
   # Wrong:
   SQLANYWHERE_CONNECTION_STRING="DRIVER={SQL Anywhere 17};DBN=mydb;UID=dba;PWD=sql"

   # Correct:
   SQLANYWHERE_CONNECTION_STRING="DRIVER={SQL Anywhere 17};ServerName=myserver;DBN=mydb;UID=dba;PWD=sql"
   ```

3. **For TCP/IP connections**, use Host parameter:

   ```env
   SQLANYWHERE_CONNECTION_STRING="DRIVER={SQL Anywhere 17};ServerName=myserver;Host=localhost:2638;DBN=mydb;UID=dba;PWD=sql"
   ```

4. **Verify database server is running**:
   - Check SQL Anywhere service/process is running
   - Verify server name, database name, and credentials are correct

**Error**: `[unixODBC][Driver Manager]Data source name not found`

**Solution**:

- Verify ODBC driver is installed: `odbcinst -q -d`
- Check driver name matches exactly (case-sensitive on Linux)
- Try using a complete connection string instead of DSN

**Error**: `[SQL Anywhere]Database not found`

**Solution**:

- Verify database server is running
- Check server name and database name in connection string
- Ensure user has permissions to access the database

### Query Issues

**Error**: `Only SELECT queries are allowed`

**Solution**: The tool intentionally blocks non-SELECT queries. Use `sqlanywhere_query_builder` for safe query construction.

**Error**: `Query timeout exceeded`

**Solution**:

- Optimize the query
- Increase timeout via `SQLANYWHERE_QUERY_TIMEOUT` environment variable
- Add more restrictive WHERE clauses

## Development

### Project Structure

```
sqlanywhere-mcp/
├── sqlanywhere_mcp/
│   ├── __init__.py
│   ├── server.py       # MCP server initialization
│   ├── db.py           # Database connection management
│   ├── schema.py       # Schema discovery tools
│   ├── queries.py      # Data query tools
│   └── models.py       # Pydantic data models
├── pyproject.toml
├── README.md
└── .env.example
```

### Testing

Run the server with MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python -m sqlanywhere_mcp.server
```

## License

MIT

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

## Resources

- [SAP SQL Anywhere Documentation](https://help.sap.com/docs/SAP_SQL_Anywhere)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
