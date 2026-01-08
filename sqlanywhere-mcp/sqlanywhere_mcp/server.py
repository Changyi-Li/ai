"""SQL Anywhere MCP Server - FastMCP implementation.

This server provides tools to interact with SAP SQL Anywhere databases via ODBC,
including schema discovery, metadata queries, and safe data retrieval.

Uses FastMCP framework for automatic tool registration and input validation.
"""

from mcp.server.fastmcp import FastMCP
from sqlanywhere_mcp.models import (
    ResponseFormat,
    ListTablesInput,
    ListViewsInput,
    GetTableDetailsInput,
    GetViewDetailsInput,
    ListProceduresInput,
    GetProcedureDetailsInput,
    ListIndexesInput,
    GetIndexDetailsInput,
    ExecuteQueryInput,
    QueryBuilderInput,
    ValidateQueryInput,
)
from sqlanywhere_mcp import schema, queries
from sqlanywhere_mcp.db import get_connection_manager
from sqlanywhere_mcp.errors import MCPError

# Initialize FastMCP server
mcp = FastMCP("sqlanywhere_mcp")


# ============================================================================
# Connection Management
# ============================================================================

@mcp.tool(
    name="sqlanywhere_connect",
    annotations={
        "title": "Connect to SQL Anywhere Database",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_connect():
    """Establish connection to SQL Anywhere database.

    This tool verifies the database connection. Usually automatic, but can be
    called explicitly to ensure the connection is active.

    Returns:
        str: Connection status with server and database information

    Examples:
        - Use when: You want to verify database connectivity before running queries
        - Don't use when: You just want to run queries (connection is automatic)

    Error Handling:
        - Returns detailed error message if connection fails
        - Suggests checking ODBC driver installation and connection parameters
    """
    try:
        import pyodbc
        cm = get_connection_manager()
        conn = cm.connect()

        return (
            f"✅ Connected to SQL Anywhere database\n\n"
            f"**Server**: {conn.getinfo(pyodbc.SQL_SERVER_NAME)}\n"
            f"**Database**: {conn.getinfo(pyodbc.SQL_DATABASE_NAME)}\n"
        )
    except Exception as e:
        return f"## Connection Error\n\n{str(e)}"


# ============================================================================
# Schema Discovery - Tables
# ============================================================================

@mcp.tool(
    name="sqlanywhere_list_tables",
    annotations={
        "title": "List SQL Anywhere Tables",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_list_tables(params: ListTablesInput):
    """List all tables in the SQL Anywhere database.

    This tool lists tables with metadata including owner, type, and row count.
    Only exposes tables created by authorized users (configured via
    SQLANYWHERE_AUTHORIZED_USERS environment variable).

    Uses modern SQL Anywhere system views (SYS.SYSTAB) with security filtering.

    Args:
        params (ListTablesInput): Input parameters containing:
            - owner (Optional[str]): Filter by owner. Cannot be combined with 'search'.
              Examples: 'monitor', 'dbo', 'ExtensionsUser'
            - search (Optional[str]): Search for tables by name substring (case-insensitive).
              Cannot be combined with 'owner'.
              Examples: 'part' matches 'PartTable', 'OrderPart', 'PartDetail'
            - limit (int): Maximum number of tables to return (default: 100, range: 1-10000)
            - response_format (ResponseFormat): Output format - 'markdown' or 'json' (default: 'markdown')

    Returns:
        str: Formatted table list with the following schema:

        Markdown format:
        ## Tables (N found)
        | Table Name | Owner | Type | Row Count |
        |------------|-------|------|-----------|
        | ...

        JSON format:
        {
            "tables": [
                {
                    "name": str,
                    "owner": str,
                    "table_type": str,
                    "row_count": int,
                    "columns": [],
                    "primary_keys": [],
                    "foreign_keys": [],
                    "indexes": [],
                    "check_constraints": []
                }
            ],
            "total_count": int,
            "has_more": bool
        }

    Examples:
        - Use when: "Show me all tables in the database"
        - Use when: "Find tables containing 'part' in the name"
        - Use when: "List all tables owned by monitor user"
        - Don't use when: You need detailed table schema (use sqlanywhere_get_table_details)

    Error Handling:
        - Pydantic validates input parameters (mutually exclusive owner/search, limit range)
        - Returns empty result if no tables match criteria
        - Validation errors returned with descriptive messages

    Security:
        - Only returns tables owned by authorized users (SQLANYWHERE_AUTHORIZED_USERS)
        - All table access is filtered by owner authorization
    """
    try:
        return await schema.list_tables(
            owner=params.owner,
            search=params.search,
            limit=params.limit,
            response_format=params.response_format
        )
    except ValueError as e:
        return f"## Error\n\n{str(e)}"
    except MCPError as e:
        return str(e)


@mcp.tool(
    name="sqlanywhere_get_table_details",
    annotations={
        "title": "Get Table Schema Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_get_table_details(params: GetTableDetailsInput):
    """Get comprehensive metadata for a specific SQL Anywhere table.

    This tool retrieves detailed schema information including columns, data types,
    primary keys, foreign keys, indexes, and check constraints.

    Uses modern SQL Anywhere system views with security filtering to only expose
    tables created by authorized users.

    Args:
        params (GetTableDetailsInput): Input parameters containing:
            - table_name (str): Table name (REQUIRED).
              Accepts both formats: 'Part' or 'monitor.Part'
              Examples: 'Part', 'monitor.Part', 'Customers', 'dbo.Customers'
            - response_format (ResponseFormat): Output format - 'markdown' or 'json' (default: 'markdown')

    Returns:
        str: Formatted table details with the following schema:

        Markdown format:
        ## Table: owner.TableName
        **Type**: BASE or VIEW
        **Row Count**: N

        ### Columns (N)
        | Column | Type | Length | Scale | Nullable | Default |
        |--------|------|--------|-------|----------|---------|
        | ...

        ### Primary Keys
        - **constraint_name**: (col1, col2, ...)

        ### Foreign Keys
        - **fk_name**: → referenced_table(pk_column)

        ### Indexes
        - **index_name**: (Unique col1 ASC, col2 DESC, ...)

        JSON format:
        {
            "name": str,
            "owner": str,
            "table_type": str,
            "row_count": int,
            "columns": [...],
            "primary_keys": [...],
            "foreign_keys": [...],
            "indexes": [...],
            "check_constraints": [...]
        }

    Examples:
        - Use when: "Show me the schema for the Part table"
        - Use when: "What columns are in the monitor.Part table?"
        - Use when: "Get the primary keys for dbo.Customers"
        - Don't use when: You just need a list of tables (use sqlanywhere_list_tables)

    Error Handling:
        - Pydantic validates table_name is provided and not empty
        - Returns "Table not found or access denied" if table doesn't exist or
          user is not authorized to access it
        - Suggests using sqlanywhere_list_tables to see available tables

    Security:
        - Only accessible for tables owned by authorized users
        - All metadata queries include security filtering
    """
    try:
        return await schema.get_table_details(
            table_name=params.table_name,
            response_format=params.response_format
        )
    except MCPError as e:
        return str(e)


# ============================================================================
# Schema Discovery - Views
# ============================================================================

@mcp.tool(
    name="sqlanywhere_list_views",
    annotations={
        "title": "List SQL Anywhere Views",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_list_views(params: ListViewsInput):
    """List all views in the SQL Anywhere database.

    This tool lists views with owner information. Only exposes views created
    by authorized users (configured via SQLANYWHERE_AUTHORIZED_USERS).

    Uses modern SQL Anywhere system views (SYS.SYSTAB) with security filtering.

    Args:
        params (ListViewsInput): Input parameters containing:
            - owner (Optional[str]): Filter by owner. Cannot be combined with 'search'.
              Examples: 'monitor', 'dbo'
            - search (Optional[str]): Search for views by name substring (case-insensitive).
              Cannot be combined with 'owner'.
              Examples: 'customer' matches 'CustomerView', 'AllCustomers', 'CustomerSummary'
            - limit (int): Maximum number of views to return (default: 100, range: 1-10000)
            - response_format (ResponseFormat): Output format - 'markdown' or 'json' (default: 'markdown')

    Returns:
        str: Formatted view list with the following schema:

        Markdown format:
        ## Views (N found)
        | View Name | Owner |
        |-----------|-------|
        | ...

        JSON format:
        {
            "views": [
                {
                    "name": str,
                    "owner": str,
                    "definition": Optional[str],
                    "columns": []
                }
            ],
            "total_count": int,
            "has_more": bool
        }

    Examples:
        - Use when: "Show me all views in the database"
        - Use when: "Find views containing 'customer' in the name"
        - Use when: "List all views owned by monitor user"
        - Don't use when: You need detailed view schema (use sqlanywhere_get_view_details)

    Error Handling:
        - Pydantic validates input parameters (mutually exclusive owner/search, limit range)
        - Returns empty result if no views match criteria
        - Validation errors returned with descriptive messages

    Security:
        - Only returns views owned by authorized users (SQLANYWHERE_AUTHORIZED_USERS)
        - All view access is filtered by owner authorization
    """
    try:
        return await schema.list_views(
            owner=params.owner,
            search=params.search,
            limit=params.limit,
            response_format=params.response_format
        )
    except ValueError as e:
        return f"## Error\n\n{str(e)}"
    except MCPError as e:
        return str(e)


@mcp.tool(
    name="sqlanywhere_get_view_details",
    annotations={
        "title": "Get View Schema Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_get_view_details(params: GetViewDetailsInput):
    """Get detailed information about a specific SQL Anywhere view.

    This tool retrieves view metadata including column information with data types.
    Only accessible for views created by authorized users.

    Args:
        params (GetViewDetailsInput): Input parameters containing:
            - view_name (str): View name (REQUIRED).
              Accepts both formats: 'CustomerView' or 'monitor.CustomerView'
              Examples: 'CustomerView', 'monitor.CustomerView', 'AllCustomers'
            - response_format (ResponseFormat): Output format - 'markdown' or 'json' (default: 'markdown')

    Returns:
        str: Formatted view details with the following schema:

        Markdown format:
        ## View: owner.ViewName

        ### Columns (N)
        | Column | Type | Nullable |
        |--------|------|----------|
        | ...

        JSON format:
        {
            "name": str,
            "owner": str,
            "definition": Optional[str],
            "columns": [
                {
                    "name": str,
                    "type": str,
                    "length": Optional[int],
                    "scale": Optional[int],
                    "nullable": bool,
                    "default_value": Optional[str],
                    "is_primary_key": bool
                }
            ]
        }

    Examples:
        - Use when: "Show me the schema for CustomerView"
        - Use when: "What columns are in the monitor.CustomerView view?"
        - Don't use when: You just need a list of views (use sqlanywhere_list_views)

    Error Handling:
        - Pydantic validates view_name is provided and not empty
        - Returns "View not found or access denied" if view doesn't exist or
          user is not authorized to access it
        - Suggests using sqlanywhere_list_views to see available views

    Security:
        - Only accessible for views owned by authorized users
        - All metadata queries include security filtering
    """
    try:
        return await schema.get_view_details(
            view_name=params.view_name,
            response_format=params.response_format
        )
    except MCPError as e:
        return str(e)


# ============================================================================
# Schema Discovery - Stored Procedures
# ============================================================================

@mcp.tool(
    name="sqlanywhere_list_procedures",
    annotations={
        "title": "List Stored Procedures and Functions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_list_procedures(params: ListProceduresInput):
    """List all stored procedures and functions in the SQL Anywhere database.

    This tool lists procedures and functions with owner information.
    Only exposes procedures created by authorized users (configured via
    SQLANYWHERE_AUTHORIZED_USERS).

    Args:
        params (ListProceduresInput): Input parameters containing:
            - owner (Optional[str]): Filter by owner. Cannot be combined with 'search'.
              Examples: 'monitor', 'dbo', 'sys'
            - search (Optional[str]): Search for procedures by name substring (case-insensitive).
              Cannot be combined with 'owner'.
              Examples: 'get' matches 'GetUser', 'getUserById', 'get_customer_data'
            - limit (int): Maximum number of procedures to return (default: 100, range: 1-10000)
            - response_format (ResponseFormat): Output format - 'markdown' or 'json' (default: 'markdown')

    Returns:
        str: Formatted procedure list with the following schema:

        Markdown format:
        ## Procedures & Functions (N found)
        | Name | Owner |
        |------|-------|
        | ...

        JSON format:
        {
            "procedures": [
                {
                    "name": str,
                    "owner": str,
                    "procedure_type": str,
                    "parameters": [],
                    "return_type": Optional[str],
                    "definition": Optional[str]
                }
            ],
            "total_count": int,
            "has_more": bool
        }

    Examples:
        - Use when: "Show me all stored procedures in the database"
        - Use when: "Find procedures containing 'get' in the name"
        - Use when: "List all procedures owned by monitor user"
        - Don't use when: You need detailed procedure information (use sqlanywhere_get_procedure_details)

    Error Handling:
        - Pydantic validates input parameters (mutually exclusive owner/search, limit range)
        - Returns empty result if no procedures match criteria
        - Validation errors returned with descriptive messages

    Security:
        - Only returns procedures owned by authorized users (SQLANYWHERE_AUTHORIZED_USERS)
        - All procedure access is filtered by owner authorization
    """
    try:
        return await schema.list_procedures(
            owner=params.owner,
            search=params.search,
            limit=params.limit,
            response_format=params.response_format
        )
    except ValueError as e:
        return f"## Error\n\n{str(e)}"
    except MCPError as e:
        return str(e)


@mcp.tool(
    name="sqlanywhere_get_procedure_details",
    annotations={
        "title": "Get Stored Procedure Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_get_procedure_details(params: GetProcedureDetailsInput):
    """Get detailed information about a specific stored procedure or function.

    This tool retrieves procedure metadata including parameters with data types
    and modes (IN, OUT, INOUT). Only accessible for procedures created by
    authorized users.

    Args:
        params (GetProcedureDetailsInput): Input parameters containing:
            - procedure_name (str): Procedure name (REQUIRED).
              Accepts both formats: 'GetUser' or 'monitor.GetUser'
              Examples: 'GetUser', 'monitor.GetUser', 'sp_get_data'
            - response_format (ResponseFormat): Output format - 'markdown' or 'json' (default: 'markdown')

    Returns:
        str: Formatted procedure details with the following schema:

        Markdown format:
        ## Procedure: owner.ProcedureName

        ### Parameters
        | Name | Type | Mode |
        |------|------|------|
        | ...

        JSON format:
        {
            "name": str,
            "owner": str,
            "procedure_type": str,
            "parameters": [
                {
                    "name": str,
                    "type": str,
                    "mode": str  # "IN", "OUT", or "INOUT"
                }
            ],
            "return_type": Optional[str],
            "definition": Optional[str]
        }

    Examples:
        - Use when: "Show me the parameters for GetUser procedure"
        - Use when: "What parameters does monitor.sp_get_data require?"
        - Don't use when: You just need a list of procedures (use sqlanywhere_list_procedures)

    Error Handling:
        - Pydantic validates procedure_name is provided and not empty
        - Returns "Procedure not found or access denied" if procedure doesn't exist or
          user is not authorized to access it
        - Suggests using sqlanywhere_list_procedures to see available procedures

    Security:
        - Only accessible for procedures owned by authorized users
        - All metadata queries include security filtering
    """
    try:
        return await schema.get_procedure_details(
            procedure_name=params.procedure_name,
            response_format=params.response_format
        )
    except MCPError as e:
        return str(e)


# ============================================================================
# Schema Discovery - Indexes
# ============================================================================

@mcp.tool(
    name="sqlanywhere_list_indexes",
    annotations={
        "title": "List Database Indexes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_list_indexes(params: ListIndexesInput):
    """List all indexes in the SQL Anywhere database.

    This tool lists index names, associated tables, uniqueness, and columns.
    Only exposes indexes on tables created by authorized users (configured via
    SQLANYWHERE_AUTHORIZED_USERS).

    Args:
        params (ListIndexesInput): Input parameters containing:
            - table_name (Optional[str]): Filter by specific table.
              Examples: 'Part', 'Customers'
              If not provided, lists all indexes for all authorized tables.
            - limit (int): Maximum number of indexes to return (default: 100, range: 1-10000)
            - response_format (ResponseFormat): Output format - 'markdown' or 'json' (default: 'markdown')

    Returns:
        str: Formatted index list with the following schema:

        Markdown format:
        ## Indexes (N found)
        | Index Name | Table | Owner | Unique |
        |------------|-------|-------|--------|
        | ...

        JSON format:
        {
            "indexes": [
                {
                    "name": str,
                    "table_name": str,
                    "is_unique": bool,
                    "is_primary_key": bool,
                    "columns": [...],
                    "index_type": Optional[str]
                }
            ],
            "total_count": int,
            "has_more": bool
        }

    Examples:
        - Use when: "Show me all indexes in the database"
        - Use when: "List all indexes for the monitor.Part table"
        - Don't use when: You need detailed index information (use sqlanywhere_get_index_details)

    Error Handling:
        - Pydantic validates input parameters (table_name not empty if provided, limit range)
        - Returns empty result if no indexes match criteria
        - Validation errors returned with descriptive messages

    Security:
        - Only returns indexes on tables owned by authorized users
        - All index access is filtered by owner authorization
    """
    try:
        return await schema.list_indexes(
            table_name=params.table_name,
            limit=params.limit,
            response_format=params.response_format
        )
    except MCPError as e:
        return str(e)


@mcp.tool(
    name="sqlanywhere_get_index_details",
    annotations={
        "title": "Get Index Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_get_index_details(params: GetIndexDetailsInput):
    """Get detailed information about a specific index.

    This tool retrieves index metadata including column details and ordering
    (ASC/DESC). Only accessible for indexes on tables created by authorized users.

    Args:
        params (GetIndexDetailsInput): Input parameters containing:
            - index_name (str): Index name.
              Examples: 'Part_PK', 'idx_customer_email', 'IX_Order_Date'
            - response_format (ResponseFormat): Output format - 'markdown' or 'json' (default: 'markdown')

    Returns:
        str: Formatted index details with the following schema:

        Markdown format:
        ## Index: index_name
        **Table**: owner.table_name
        **Unique**: Yes/No

        ### Columns
        | Column | Order | Sequence |
        |--------|-------|----------|
        | ...

        JSON format:
        {
            "name": str,
            "table_name": str,
            "is_unique": bool,
            "is_primary_key": bool,
            "columns": [
                {
                    "column_name": str,
                    "order": str  # "ASC" or "DESC"
                }
            ],
            "index_type": Optional[str]
        }

    Examples:
        - Use when: "Show me the details of Part_PK index"
        - Use when: "What columns are in the idx_customer_email index?"
        - Don't use when: You just need a list of indexes (use sqlanywhere_list_indexes)

    Error Handling:
        - Pydantic validates index_name is provided
        - Returns "Index not found or access denied" if index doesn't exist or
          user is not authorized to access it
        - Suggests using sqlanywhere_list_indexes to see available indexes

    Security:
        - Only accessible for indexes on tables owned by authorized users
        - All metadata queries include security filtering
    """
    try:
        return await schema.get_index_details(
            index_name=params.index_name,
            response_format=params.response_format
        )
    except MCPError as e:
        return str(e)


# ============================================================================
# Database Information
# ============================================================================

@mcp.tool(
    name="sqlanywhere_get_database_info",
    annotations={
        "title": "Get Database Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_get_database_info():
    """Get database metadata and connection information.

    This tool retrieves comprehensive database information including name,
    version, character set, collation, page size, and object counts
    (filtered by authorized users).

    Returns:
        str: Formatted database information with the following schema:

        Markdown format:
        ## Database Information

        **Database Name**: name
        **SQL Anywhere Version**: version

        ### Connection Information
        **Server Name**: server_name
        **Database Name**: db_name
        **DBMS Name**: dbms_name
        **DBMS Version**: dbms_version

        ### Database Properties
        **Character Set**: charset
        **Collation**: collation
        **Page Size**: page_size bytes

        ### Database Objects
        - **Tables** (authorized): N
        - **Views** (authorized): N
        - **Procedures/Functions**: N

    Examples:
        - Use when: "What database version am I connected to?"
        - Use when: "Show me database properties and configuration"
        - Use when: "How many tables are in the database?"

    Error Handling:
        - Returns error if database connection fails
        - Includes suggestions for troubleshooting connection issues

    Security:
        - Object counts are filtered by authorized users
        - Only shows counts for objects owned by authorized users
    """
    try:
        return await schema.get_database_info()
    except MCPError as e:
        return str(e)


# ============================================================================
# Data Queries
# ============================================================================

@mcp.tool(
    name="sqlanywhere_execute_query",
    annotations={
        "title": "Execute SQL SELECT Query",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_execute_query(params: ExecuteQueryInput):
    """Execute a SELECT query on the SQL Anywhere database.

    This tool executes read-only SELECT queries with configurable row limits.
    Only SELECT queries are allowed for security. All queries are validated
    to ensure they only access tables/views from authorized owners.

    IMPORTANT: All FROM and JOIN clauses must use owner.table format with
    authorized owners (configured via SQLANYWHERE_AUTHORIZED_USERS).

    Args:
        params (ExecuteQueryInput): Input parameters containing:
            - query (str): SQL SELECT query to execute. Must use owner.table format for all tables.
              Examples:
                - "SELECT * FROM monitor.Part WHERE Type = 1"
                - "SELECT Id, Name FROM dbo.Customers ORDER BY Name"
                - "SELECT c.Id, c.Name, o.OrderId FROM dbo.Customers c JOIN dbo.Orders o ON c.Id = o.CustomerId"
            - limit (Optional[int]): Maximum rows to return (default: 1000, max: 10000).
              If not specified, uses configured default (SQLANYWHERE_MAX_ROWS env var).
            - response_format (ResponseFormat): Output format - 'markdown' or 'json' (default: 'markdown')

    Returns:
        str: Formatted query results with the following schema:

        Markdown format:
        ## Query Results

        **Rows returned**: N
        **Execution time**: X.XXX seconds

        | Column1 | Column2 | ... |
        |---------|---------|-----|
        | value1  | value2  | ... |
        | ...     | ...     | ... |

        JSON format:
        {
            "rows": [
                {"column1": value1, "column2": value2, ...},
                ...
            ],
            "row_count": int,
            "columns": [str, ...],
            "column_types": {"column1": "type1", ...},
            "execution_time_seconds": float,
            "has_more": bool
        }

    Examples:
        - Use when: "Get all parts with Type = 1"
        - Use when: "List customer names and IDs"
        - Use when: "Join customers with their orders"
        - Don't use when: You need to modify data (INSERT, UPDATE, DELETE are not allowed)
        - Don't use when: Building simple queries (use sqlanywhere_query_builder instead)

    Error Handling:
        - Pydantic validates query starts with SELECT and limit is within range
        - Returns "Access to owners X, Y is not authorized" if query references unauthorized tables
        - Returns database errors if query fails (syntax, invalid column, etc.)

    Security:
        - Only SELECT queries are allowed (no INSERT, UPDATE, DELETE, DDL)
        - Validates all FROM/JOIN clauses reference authorized owners only
        - Enforces maximum row limits to prevent large result sets
        - All queries use parameterized bindings to prevent SQL injection
    """
    try:
        return await queries.execute_query(
            query=params.query,
            limit=params.limit,
            response_format=params.response_format
        )
    except MCPError as e:
        return str(e)


@mcp.tool(
    name="sqlanywhere_query_builder",
    annotations={
        "title": "Build and Execute SELECT Query",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sqlanywhere_query_builder(params: QueryBuilderInput):
    """Build and execute a simple SELECT query with parameters.

    This is a convenience tool for building safe SELECT queries without writing
    raw SQL. Supports WHERE, ORDER BY, and TOP clauses. Automatically validates
    inputs to prevent SQL injection.

    IMPORTANT: table_name must include owner prefix (e.g., 'monitor.Part').

    Args:
        params (QueryBuilderInput): Input parameters containing:
            - table_name (str): Table to query with owner prefix (REQUIRED).
              Format must be: owner.TableName
              Examples: 'monitor.Part', 'dbo.Customers', 'ExtensionsUser.Config'
            - columns (str): Columns to select (default: '*'). Comma-separated column names.
              Examples: 'Id,PartNumber,Description', 'Name,Email,Phone'
            - where (Optional[str]): WHERE clause condition. Simple conditions only.
              Examples: 'Type = 1', 'Status = "Active" AND CreatedDate > "2024-01-01"'
            - order_by (Optional[str]): ORDER BY clause. Column names with optional ASC/DESC.
              Examples: 'Name', 'CreatedDate DESC', 'LastName, FirstName ASC'
            - limit (Optional[int]): Row limit (default: 100, max: 10000).
            - response_format (ResponseFormat): Output format - 'markdown' or 'json' (default: 'markdown')

    Returns:
        str: Query results in the same format as sqlanywhere_execute_query

    Examples:
        - Use when: "Get first 10 rows from monitor.Part"
        - Use when: "Select Id and Name from dbo.Customers where Status is Active"
        - Use when: "Get all parts ordered by PartNumber"
        - Don't use when: You need complex queries (joins, subqueries, etc.)
        - Don't use when: You prefer writing raw SQL (use sqlanywhere_execute_query)

    Error Handling:
        - Pydantic validates all inputs (table_name owner prefix, columns, where, order_by, limit)
        - Validation errors returned with descriptive messages

    Security:
        - All inputs are validated before query construction
        - Uses parameterized TOP clause (SQL Anywhere syntax)
        - Only accesses tables from authorized owners
        - Prevents SQL injection through input validation
    """
    try:
        return await queries.query_builder(
            table_name=params.table_name,
            columns=params.columns,
            where=params.where,
            order_by=params.order_by,
            limit=params.limit,
            response_format=params.response_format
        )
    except MCPError as e:
        return str(e)


@mcp.tool(
    name="sqlanywhere_validate_query",
    annotations={
        "title": "Validate SQL Query",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def sqlanywhere_validate_query(params: ValidateQueryInput):
    """Validate a SQL query without executing it.

    This tool performs basic validation checks on SQL queries to ensure they
    are safe SELECT statements. Useful for testing queries before execution.

    Args:
        params (ValidateQueryInput): Input parameters containing:
            - query (str): SQL query to validate.
              Examples: 'SELECT * FROM monitor.Part'

    Returns:
        str: Validation result message indicating whether the query is valid or not.

        Success: "✅ Valid: Query appears to be a safe SELECT query (basic validation passed)"
        Error: "❌ Invalid: [specific reason]"

    Examples:
        - Use when: "Check if this query is valid before running it"
        - Use when: "Validate a complex SELECT query"
        - Don't use when: You want to actually execute the query (use sqlanywhere_execute_query)

    Error Handling:
        - Pydantic validates query starts with SELECT
        - Returns additional validation errors for dangerous keywords

    Security:
        - Checks for dangerous SQL keywords (DROP, DELETE, INSERT, UPDATE, CREATE, ALTER, TRUNCATE)
        - Validates basic SQL syntax
        - Does not execute the query (read-only validation)
    """
    try:
        return await queries.validate_query(query=params.query)
    except MCPError as e:
        return str(e)


# ============================================================================
# Server Entry Point
# ============================================================================

def main():
    """Main entry point for the SQL Anywhere MCP server.

    This function starts the FastMCP server using stdio transport.
    The server will listen for MCP client requests and respond with
    tool executions and resource reads.
    """
    mcp.run()


if __name__ == "__main__":
    main()
