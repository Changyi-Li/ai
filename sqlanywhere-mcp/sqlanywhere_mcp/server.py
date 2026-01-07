"""SQL Anywhere MCP Server - Main entry point."""

import asyncio
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from sqlanywhere_mcp import schema, queries
from sqlanywhere_mcp.db import get_connection_manager
from sqlanywhere_mcp.errors import MCPError
from sqlanywhere_mcp.models import ResponseFormat

# Create server instance
server = Server("sqlanywhere-mcp")


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="database:///info",
            name="Database Information",
            description="General information about the SQL Anywhere database",
            mimeType="text/plain",
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a resource by URI."""
    if uri == "database:///info":
        return schema.get_database_info()
    else:
        raise ValueError(f"Unknown resource URI: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        # Connection Management
        Tool(
            name="sqlanywhere_connect",
            description="Establish connection to SQL Anywhere database. "
            "Usually automatic, but can be called explicitly to verify connection.",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),

        # Schema Discovery - Tables
        Tool(
            name="sqlanywhere_list_tables",
            description="List all tables in the database. "
            "Returns table names, owners, types, and row counts. "
            "Only exposes tables created by authorized users (configured via SQLANYWHERE_AUTHORIZED_USERS). "
            "Supports optional filtering by owner/schema.",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Filter by schema/owner (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of tables to return (default: 100)",
                        "default": 100,
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "description": "Output format (default: markdown)",
                        "default": "markdown",
                    },
                },
            },
        ),
        Tool(
            name="sqlanywhere_get_table_details",
            description="Get comprehensive metadata for a specific table. "
            "Includes columns, data types, primary keys, foreign keys, indexes, "
            "and check constraints. Only accessible for tables created by authorized users.",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table",
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "description": "Output format (default: markdown)",
                        "default": "markdown",
                    },
                },
                "required": ["table_name"],
            },
        ),

        # Schema Discovery - Views
        Tool(
            name="sqlanywhere_list_views",
            description="List all views in the database. "
            "Returns view names and owners. "
            "Only exposes views created by authorized users (configured via SQLANYWHERE_AUTHORIZED_USERS).",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Filter by schema/owner (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of views to return (default: 100)",
                        "default": 100,
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "description": "Output format (default: markdown)",
                        "default": "markdown",
                    },
                },
            },
        ),
        Tool(
            name="sqlanywhere_get_view_details",
            description="Get detailed information about a specific view. "
            "Includes column information with data types. "
            "Only accessible for views created by authorized users.",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {
                    "view_name": {
                        "type": "string",
                        "description": "Name of the view",
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "description": "Output format (default: markdown)",
                        "default": "markdown",
                    },
                },
                "required": ["view_name"],
            },
        ),

        # Schema Discovery - Procedures
        Tool(
            name="sqlanywhere_list_procedures",
            description="List all stored procedures and functions in the database. "
            "Returns procedure names and owners. "
            "Only exposes procedures created by authorized users (configured via SQLANYWHERE_AUTHORIZED_USERS).",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Filter by schema/owner (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of procedures to return (default: 100)",
                        "default": 100,
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "description": "Output format (default: markdown)",
                        "default": "markdown",
                    },
                },
            },
        ),
        Tool(
            name="sqlanywhere_get_procedure_details",
            description="Get detailed information about a specific procedure or function. "
            "Includes parameters with data types and modes. "
            "Only accessible for procedures created by authorized users.",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {
                    "procedure_name": {
                        "type": "string",
                        "description": "Name of the procedure",
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "description": "Output format (default: markdown)",
                        "default": "markdown",
                    },
                },
                "required": ["procedure_name"],
            },
        ),

        # Schema Discovery - Indexes
        Tool(
            name="sqlanywhere_list_indexes",
            description="List all indexes in the database. "
            "Returns index names, associated tables, uniqueness, and columns. "
            "Only exposes indexes on tables created by authorized users (configured via SQLANYWHERE_AUTHORIZED_USERS). "
            "Can filter by specific table.",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Filter by specific table (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of indexes to return (default: 100)",
                        "default": 100,
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "description": "Output format (default: markdown)",
                        "default": "markdown",
                    },
                },
            },
        ),
        Tool(
            name="sqlanywhere_get_index_details",
            description="Get detailed information about a specific index. "
            "Includes column details and ordering. "
            "Only accessible for indexes on tables created by authorized users.",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {
                    "index_name": {
                        "type": "string",
                        "description": "Name of the index",
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "description": "Output format (default: markdown)",
                        "default": "markdown",
                    },
                },
                "required": ["index_name"],
            },
        ),

        # Database Information
        Tool(
            name="sqlanywhere_get_database_info",
            description="Get database metadata and connection information. "
            "Returns database name, version, character set, collation, "
            "and object counts (filtered by authorized users).",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),

        # Data Queries
        Tool(
            name="sqlanywhere_execute_query",
            description="Execute a SELECT query on the database. "
            "Only SELECT queries are allowed for security. "
            "Returns results with metadata (row count, execution time, column types). "
            "Supports configurable row limits to prevent large result sets.",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum rows to return (default: 1000, max: 10000)",
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "description": "Output format (default: markdown)",
                        "default": "markdown",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="sqlanywhere_query_builder",
            description="Build and execute a simple SELECT query with parameters. "
            "Convenience tool for safe query construction. "
            "Supports WHERE, ORDER BY, and TOP clauses. "
            "IMPORTANT: table_name must include schema/owner prefix (e.g., 'monitor.Part', 'dbo.Customers').",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Table to query with schema/owner prefix (REQUIRED). "
                            "Examples: 'monitor.Part', 'dbo.Customers', 'ExtensionsUser.Config'. "
                            "Format must be: schema.TableName",
                    },
                    "columns": {
                        "type": "string",
                        "description": "Columns to select (default: *)",
                        "default": "*",
                    },
                    "where": {
                        "type": "string",
                        "description": "WHERE clause condition (optional)",
                    },
                    "order_by": {
                        "type": "string",
                        "description": "ORDER BY clause (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Row limit (default: 100)",
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "description": "Output format (default: markdown)",
                        "default": "markdown",
                    },
                },
                "required": ["table_name"],
            },
        ),
        Tool(
            name="sqlanywhere_validate_query",
            description="Validate a SQL query without executing it. "
            "Performs basic validation checks for safety.",
            annotations={
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            },
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to validate",
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls."""

    if arguments is None:
        arguments = {}

    # Extract response_format with default
    response_format_str = arguments.get("response_format", "markdown")
    try:
        response_format = ResponseFormat(response_format_str)
    except ValueError:
        response_format = ResponseFormat.MARKDOWN

    try:
        if name == "sqlanywhere_connect":
            # Just establish connection
            import pyodbc
            cm = get_connection_manager()
            conn = cm.connect()
            return [
                TextContent(
                    type="text",
                    text=f"✅ Connected to SQL Anywhere database\n\n"
                    f"**Server**: {conn.getinfo(pyodbc.SQL_SERVER_NAME)}\n"
                    f"**Database**: {conn.getinfo(pyodbc.SQL_DATABASE_NAME)}\n"
                )
            ]

        elif name == "sqlanywhere_list_tables":
            result = schema.list_tables(
                owner=arguments.get("owner"),
                limit=arguments.get("limit", 100),
                response_format=response_format
            )
            return [TextContent(type="text", text=result)]

        elif name == "sqlanywhere_get_table_details":
            result = schema.get_table_details(
                table_name=arguments["table_name"],
                response_format=response_format
            )
            return [TextContent(type="text", text=result)]

        elif name == "sqlanywhere_list_views":
            result = schema.list_views(
                owner=arguments.get("owner"),
                limit=arguments.get("limit", 100),
                response_format=response_format
            )
            return [TextContent(type="text", text=result)]

        elif name == "sqlanywhere_get_view_details":
            result = schema.get_view_details(
                view_name=arguments["view_name"],
                response_format=response_format
            )
            return [TextContent(type="text", text=result)]

        elif name == "sqlanywhere_list_procedures":
            result = schema.list_procedures(
                owner=arguments.get("owner"),
                limit=arguments.get("limit", 100),
                response_format=response_format
            )
            return [TextContent(type="text", text=result)]

        elif name == "sqlanywhere_get_procedure_details":
            result = schema.get_procedure_details(
                procedure_name=arguments["procedure_name"],
                response_format=response_format
            )
            return [TextContent(type="text", text=result)]

        elif name == "sqlanywhere_list_indexes":
            result = schema.list_indexes(
                table_name=arguments.get("table_name"),
                limit=arguments.get("limit", 100),
                response_format=response_format
            )
            return [TextContent(type="text", text=result)]

        elif name == "sqlanywhere_get_index_details":
            result = schema.get_index_details(
                index_name=arguments["index_name"],
                response_format=response_format
            )
            return [TextContent(type="text", text=result)]

        elif name == "sqlanywhere_get_database_info":
            result = schema.get_database_info()
            return [TextContent(type="text", text=result)]

        elif name == "sqlanywhere_execute_query":
            result = queries.execute_query(
                query=arguments["query"],
                limit=arguments.get("limit"),
                response_format=response_format
            )
            return [TextContent(type="text", text=result)]

        elif name == "sqlanywhere_query_builder":
            result = queries.query_builder(
                table_name=arguments["table_name"],
                columns=arguments.get("columns", "*"),
                where=arguments.get("where"),
                order_by=arguments.get("order_by"),
                limit=arguments.get("limit"),
                response_format=response_format
            )
            return [TextContent(type="text", text=result)]

        elif name == "sqlanywhere_validate_query":
            result = queries.validate_query(
                query=arguments["query"]
            )
            return [TextContent(type="text", text=result)]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except MCPError as e:
        # Custom MCP errors already have formatted messages
        return [TextContent(type="text", text=str(e))]
    except Exception as e:
        # Generic errors - wrap in simple error message
        return [TextContent(type="text", text=f"## Error\n\n{str(e)}")]


async def main():
    """Main entry point for the server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sqlanywhere-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import pyodbc  # Import here to avoid issues if not installed
    asyncio.run(main())
