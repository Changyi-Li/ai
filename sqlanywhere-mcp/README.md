# SQL Anywhere MCP Server

A Model Context Protocol (MCP) server for connecting to SAP SQL Anywhere databases via ODBC. Built with **FastMCP** framework, this server enables LLMs to explore database schemas and execute data queries safely with automatic tool registration and comprehensive input validation.

## Highlights

- 🚀 **Built with FastMCP**: Modern MCP Python SDK framework for clean, maintainable code
- 🔒 **Security First**: Owner-based access control, query validation, and SQL injection prevention
- 📊 **Rich Schema Discovery**: Tables, views, procedures, indexes, and keys using modern SQL Anywhere system views
- 🔍 **Smart Search**: Case-insensitive substring search across all database objects
- 📝 **Dual Output Formats**: Human-readable Markdown and machine-readable JSON
- ⚡ **Async/Await**: Non-blocking database operations for better performance
- ✅ **Pydantic v2**: Comprehensive input validation with automatic schema generation

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

### Core Capabilities

- **Schema Discovery**: Retrieve tables, columns, views, stored procedures, indexes, and keys using modern SQL Anywhere system views (SYS.SYSTAB, SYS.SYSTABCOL, etc.)
- **Name Search**: Case-insensitive substring search for tables, views, and procedures
- **Security Filtering**: Expose only objects from authorized users (configured via `SQLANYWHERE_AUTHORIZED_USERS`)
- **Data Queries**: Execute SELECT queries with configurable row limits and automatic authorization validation
- **Safe Operations**: Read-only access with comprehensive safety constraints and input validation
- **Structured Output**: Both human-readable Markdown and machine-readable JSON formats

### FastMCP Implementation Benefits

- **Automatic Tool Registration**: Tools are registered using `@mcp.tool()` decorators with automatic schema generation
- **Comprehensive Input Validation**: Pydantic v2 models with `model_config` for robust input validation across all tools
  - Mutual exclusion validation (e.g., owner vs search parameters)
  - Range validation (limits, string lengths)
  - SQL injection prevention via regex patterns
  - Automatic string sanitization (whitespace trimming)
  - Extra field prevention with `extra='forbid'`
- **Clean Async Pattern**: All database operations use async/await for optimal I/O performance
- **Rich Documentation**: Every tool includes detailed docstrings with examples, error handling, and security notes
- **Type Safety**: Full type hints throughout the codebase for better IDE support and maintainability
- **Organized Model Structure**: Pydantic models organized by tool functionality (tables, views, procedures, indexes, queries)

## Prerequisites

1. **Python**: 3.10 or higher
   - Verify installation: `python --version` or `py --version`
2. **SQL Anywhere ODBC Driver**: Must be installed and accessible

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

### 2. Configure Connection

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

### 3. ODBC Driver Setup

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

The FastMCP framework automatically registers all tools and generates their schemas from the function signatures and docstrings.

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

Establish connection to SQL Anywhere database. Usually automatic, but can be called explicitly to verify connectivity.

**Returns**: Connection status with server and database information

### Schema Discovery - Tables

#### `sqlanywhere_list_tables`

List all tables in the database with metadata (owner, type, row count).
Only exposes tables created by authorized users (configured via `SQLANYWHERE_AUTHORIZED_USERS`).

**Parameters**:
- `owner` (optional): Filter by owner (e.g., 'monitor', 'dbo')
- `search` (optional): Search for tables by name substring (case-insensitive, mutually exclusive with owner)
  - Example: 'part' matches 'PartTable', 'OrderPart', 'PartDetail'
- `limit` (optional): Maximum number of tables to return (default: 100, max: 10000)
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: Table names, owners, types, and row counts

#### `sqlanywhere_get_table_details`

Get comprehensive metadata for a specific table including columns, data types, primary keys, foreign keys, indexes, and check constraints.

**Parameters**:
- `table_name` (required): Name of the table (without owner prefix)
  - Format: `TableName` (e.g., 'Part', 'Customers')
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: Complete table schema with all constraints and relationships

### Schema Discovery - Views

#### `sqlanywhere_list_views`

List all views in the database with owner information.

**Parameters**:
- `owner` (optional): Filter by owner
- `search` (optional): Search for views by name substring (case-insensitive)
  - Example: 'customer' matches 'CustomerView', 'AllCustomers', 'CustomerSummary'
- `limit` (optional): Maximum number of views to return (default: 100)
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: View names and owners

#### `sqlanywhere_get_view_details`

Get detailed information about a specific view including column definitions.

**Parameters**:
- `view_name` (required): Name of the view (without owner prefix)
  - Format: `ViewName` (e.g., 'CustomerView', 'AllCustomers')
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: View definition and column information

### Schema Discovery - Stored Procedures

#### `sqlanywhere_list_procedures`

List all stored procedures and functions in the database.

**Parameters**:
- `owner` (optional): Filter by owner
- `search` (optional): Search for procedures by name substring (case-insensitive)
  - Example: 'get' matches 'GetUser', 'getUserById', 'get_customer_data'
- `limit` (optional): Maximum number of procedures to return (default: 100)
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: Procedure names, types, and owners

#### `sqlanywhere_get_procedure_details`

Get detailed information about a specific procedure or function including parameters with data types and modes.

**Parameters**:
- `procedure_name` (required): Name of the procedure (without owner prefix)
  - Format: `ProcedureName` (e.g., 'GetUser', 'sp_get_data')
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: Parameter definitions with IN/OUT/INOUT modes

### Schema Discovery - Indexes

#### `sqlanywhere_list_indexes`

List all indexes in the database with associated table information.

**Parameters**:
- `table_name` (optional): Filter by specific table name (without owner prefix, e.g., 'Part')
- `limit` (optional): Maximum number of indexes to return (default: 100)
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: Index names, tables, uniqueness, and column information

#### `sqlanywhere_get_index_details`

Get detailed information about a specific index including column ordering.

**Parameters**:
- `index_name` (required): Name of the index
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: Index column details with ASC/DESC ordering and sequence information

### Database Information

#### `sqlanywhere_get_database_info`

Get comprehensive database metadata and connection information.

**Returns**: Database name, version, character set, collation, page size, and object counts

### Data Queries

#### `sqlanywhere_execute_query`

Execute a SELECT query on the database with comprehensive security validation.

**Parameters**:
- `query` (required): SQL SELECT query to execute
  - **IMPORTANT**: All FROM and JOIN clauses must use owner.table format (e.g., 'monitor.Part')
  - Only authorized owners can be accessed (per `SQLANYWHERE_AUTHORIZED_USERS`)
- `limit` (optional): Maximum rows to return (default: 1000, max: 10000)
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: Query results with metadata (row count, execution time, column types)

**Safety**:
- Only SELECT queries are allowed (INSERT, UPDATE, DELETE, DDL are blocked)
- Validates all FROM/JOIN clauses reference authorized owners only
- Enforces maximum row limits to prevent large result sets
- Uses parameterized bindings to prevent SQL injection

#### `sqlanywhere_query_builder`

Build and execute a simple SELECT query with automatic validation. Convenience tool for safe query construction.

**Parameters**:
- `table_name` (required): Table to query with owner prefix
  - Format: `owner.TableName` (e.g., 'monitor.Part', 'dbo.Customers')
- `columns` (optional): Columns to select (default: '*')
  - Example: 'Id,Name,Email'
- `where` (optional): WHERE clause condition
- `order_by` (optional): ORDER BY clause
- `limit` (optional): Row limit (default: 100)
- `response_format` (optional): Output format - "markdown" or "json" (default: "markdown")

**Returns**: Query results with metadata

**Note**: Automatically uses SQL Anywhere's `TOP` syntax instead of `LIMIT`.

#### `sqlanywhere_validate_query`

Validate a SQL query without executing it. Performs basic safety checks.

**Parameters**:
- `query` (required): SQL query to validate

**Returns**: Validation result with error messages if invalid

## Examples

### Search for tables by name

```python
# Search for tables containing 'part'
sqlanywhere_list_tables(search="part")

# Result:
## Tables (3 found)
| Table Name | Owner | Type | Row Count |
|------------|-------|------|-----------|
| Part | monitor | BASE | 9 |
| OrderPart | monitor | BASE | 523 |
| SparePart | monitor | BASE | 12 |

# Case-insensitive search (same results)
sqlanywhere_list_tables(search="PART")
sqlanywhere_list_tables(search="Part")
```

### Get table schema

```python
# Get detailed table schema
sqlanywhere_get_table_details(table_name="Part")

# Result:
## Table: monitor.Part
**Type**: BASE
**Row Count**: 9

### Columns (9)
| Column | Type | Length | Scale | Nullable | Default |
|--------|------|--------|-------|----------|---------|
| Id | bigint | NULL | NULL | NO | NULL |
| PartNumber | nvarchar | 20 | NULL | NO | NULL |
| Description | nvarchar | 400 | NULL | NO | NULL |
| Type | integer | NULL | NULL | NO | NULL |

### Primary Keys
- **Part**: (Id)

### Foreign Keys
- **bk_Part_CompanyId**: → Company(CompanyId)
- **bk_Part_ProductGroupId**: → ProductGroup(ProductGroupId)

### Indexes
- **Part** (Primary Key): (Id ASC)
- **idx_part_Description**: (Description ASC)
```

### Query data

```python
# Using query_builder for simple queries
sqlanywhere_query_builder(
    table_name="monitor.Part",
    columns="Id,PartNumber,Description",
    where="Type = 1",
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
| 3 | PART-003   | Sample Part 3 |
| 4 | PART-004   | Sample Part 4 |
| 5 | PART-005   | Sample Part 5 |
```

### Execute custom query

```python
# For complex queries, use execute_query
sqlanywhere_execute_query(
    query="""
        SELECT c.Id, c.Name, COUNT(o.OrderId) as OrderCount
        FROM dbo.Customers c
        LEFT JOIN dbo.Orders o ON c.Id = o.CustomerId
        GROUP BY c.Id, c.Name
        ORDER BY OrderCount DESC
    """,
    limit=10
)

# Result: Ranked customers by order count
```

## Architecture

### FastMCP Implementation

This server is built using the **FastMCP framework** from the MCP Python SDK, which provides:

- **Declarative Tool Registration**: Tools are registered using `@mcp.tool()` decorators
- **Automatic Schema Generation**: Input schemas are automatically generated from function signatures and Pydantic models
- **Comprehensive Validation**: All inputs are validated using Pydantic v2 with proper `model_config`
- **Async Support**: All database operations use async/await for optimal performance
- **Rich Documentation**: Tool docstrings include complete parameter descriptions, return schemas, examples, and security notes

### Project Structure

```
sqlanywhere-mcp/
├── sqlanywhere_mcp/
│   ├── __init__.py         # Package initialization
│   ├── server.py           # FastMCP server with @mcp.tool decorators
│   ├── db.py               # Database connection management
│   ├── schema.py           # Schema discovery tools (async)
│   ├── queries.py          # Data query tools (async)
│   ├── models.py           # Pydantic v2 data models
│   ├── formatters.py       # Markdown/JSON output formatting
│   └── errors.py           # Custom exception classes
├── pyproject.toml          # Project configuration
├── README.md               # This file
└── .env.example            # Environment variable template
```

### Code Quality

The implementation follows MCP best practices:

- ✅ All tools use `@mcp.tool()` decorator with proper annotations
- ✅ Comprehensive docstrings with parameter descriptions and return schemas
- ✅ **Pydantic v2 Input Models**: All tools use dedicated input validation models
  - Organized by tool functionality (tables, views, procedures, indexes, queries)
  - Mutual exclusion validation (e.g., owner vs search)
  - Range validation and type checking
  - SQL injection prevention
  - Automatic sanitization and security constraints
- ✅ Async/await pattern throughout for I/O operations
- ✅ Type hints on all functions and methods
- ✅ Security filtering via `SQLANYWHERE_AUTHORIZED_USERS`
- ✅ SQL injection prevention through validation and parameterized queries
- ✅ Clear error messages with actionable suggestions

## Security

### Multi-Layer Security Model

1. **Owner-Based Access Control**
   - Only objects owned by `SQLANYWHERE_AUTHORIZED_USERS` are exposed
   - All queries validate FROM/JOIN clauses reference authorized owners

2. **Query Validation**
   - Only SELECT queries are allowed (no INSERT, UPDATE, DELETE, DDL)
   - Dangerous keyword detection (DROP, DELETE, TRUNCATE, etc.)
   - SQL injection prevention through input validation

3. **Row Limits**
   - Configurable default and maximum row limits
   - Prevents large result sets from impacting performance

4. **Connection Security**
   - Supports encrypted connections via ODBC parameters
   - Environment variable-based credential management
   - No hardcoded credentials

5. **Input Validation**
   - Pydantic v2 models with comprehensive validation
   - Automatic string whitespace trimming
   - Extra field prevention with `extra='forbid'`

## Troubleshooting

### Installation Issues

**Error**: `pip: command not found` (Windows)

**Solution**:
- Use `python -m pip` instead of `pip`
- If `python` is not found, try the Windows launcher: `py -m pip`
- Verify Python installation: `python --version` or `py --version`

**Error**: `Access denied` during installation

**Solution**:
- Run PowerShell as Administrator
- Or install to user directory: `python -m pip install --user mcp pyodbc python-dotenv pydantic`

### Connection Issues

**Error**: `[SAP][ODBC Driver][SQL Anywhere]Database server not found (-100)`

**Solution**: This error indicates incorrect connection parameters.

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

4. **Verify database server is running**

**Error**: `[unixODBC][Driver Manager]Data source name not found`

**Solution**:
- Verify ODBC driver is installed: `odbcinst -q -d`
- Check driver name matches exactly (case-sensitive on Linux)
- Try using a complete connection string instead of DSN

### Query Issues

**Error**: `Only SELECT queries are allowed`

**Solution**: The tool intentionally blocks non-SELECT queries. Use `sqlanywhere_query_builder` for safe query construction.

**Error**: `Access to owners X, Y is not authorized`

**Solution**: Add the required owners to `SQLANYWHERE_AUTHORIZED_USERS` environment variable.

**Error**: `Query timeout exceeded`

**Solution**:
- Optimize the query
- Increase timeout via `SQLANYWHERE_QUERY_TIMEOUT` environment variable
- Add more restrictive WHERE clauses

## Development

### Testing

Run the server with MCP Inspector to test tools:

```bash
npx @modelcontextprotocol/inspector python -m sqlanywhere_mcp.server
```

### Adding New Tools

To add a new tool using FastMCP:

1. **Create Pydantic Input Model** in `models.py`:
```python
# ============================================================================
# New Tool Models
# ============================================================================

class NewToolInput(BaseModel):
    """Input model for new_tool operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    param1: str = Field(..., description="Parameter description", min_length=1, max_length=200)
    param2: int = Field(default=100, description="Parameter description", ge=1, le=10000)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

    @field_validator('param1')
    @classmethod
    def validate_param1(cls, v: str) -> str:
        """Validate param1."""
        if not v or not v.strip():
            raise ValueError("Param1 cannot be empty")
        return v
```

2. **Define async function** in `server.py`:
```python
from sqlanywhere_mcp.models import NewToolInput

@mcp.tool(
    name="sqlanywhere_new_tool",
    annotations={
        "title": "Human-Readable Title",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_new_tool(params: NewToolInput):
    """Tool description with comprehensive documentation.

    Args (from NewToolInput):
        param1: Description of parameter
        param2: Description of parameter with default
        response_format: Output format

    Returns:
        Formatted results with complete schema documentation

    Examples:
        - Use when: Description of when to use this tool
        - Don't use when: Description of when not to use

    Error Handling:
        - Description of error scenarios

    Security:
        - Description of security considerations
    """
    try:
        # Implementation here - access validated parameters via params object
        result = await some_function(params.param1, params.param2)
        return result
    except ValueError as e:
        return f"## Error\n\n{str(e)}"
    except MCPError as e:
        return str(e)
```

3. **Organize models in models.py**:
   - Group input models with their related output models
   - Use section comments to organize by tool functionality
   - Follow naming pattern: `{ToolName}Input`

4. FastMCP automatically:
   - Registers the tool
   - Generates input schema from Pydantic model
   - Uses docstring for tool description
   - Applies annotations for tool hints
   - Validates all inputs before calling the function

### Extending Functionality

- **Add new schema tools**: Update `schema.py` with async functions
- **Add query features**: Extend `queries.py` with new query builders
- **Add data models**: Update `models.py` with new Pydantic models
- **Custom formatting**: Extend `formatters.py` with new output formats

## License

MIT

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

## Resources

- [SAP SQL Anywhere Documentation](https://help.sap.com/docs/SAP_SQL_Anywhere)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Guide](https://github.com/jlowin/fastmcp) - FastMCP framework documentation

## Changelog

### v0.3.0 (Current)
- **Pydantic Input Models**: Implemented comprehensive input validation models for all tools
  - 11 dedicated input models (ListTablesInput, GetTableDetailsInput, etc.)
  - Mutual exclusion validation (owner vs search parameters)
  - SQL injection prevention via regex validation
  - Automatic string sanitization and type checking
- **Model Organization**: Reorganized models.py by tool functionality
  - Grouped input and output models by tool (tables, views, procedures, indexes, queries)
  - Improved maintainability and developer experience
- **Parameter Clarification**: Updated get_*_details tools to accept names without owner prefix
  - get_table_details: `table_name` (e.g., 'Part') not 'monitor.Part'
  - get_view_details: `view_name` (e.g., 'CustomerView') not 'monitor.CustomerView'
  - get_procedure_details: `procedure_name` (e.g., 'GetUser') not 'monitor.GetUser'
  - list_indexes: `table_name` filter accepts name without owner prefix
- **Enhanced Documentation**: Updated README with Pydantic model usage patterns and examples

### v0.2.0
- **Refactored to FastMCP**: Migrated from low-level Server API to FastMCP framework
- **Async Support**: All database operations now use async/await
- **Pydantic v2**: Updated to Pydantic v2 with `model_config` and classmethod validators
- **Enhanced Documentation**: Comprehensive docstrings with examples and security notes
- **Improved Type Safety**: Full type hints throughout the codebase

### v0.1.0
- Initial release with basic MCP server functionality
