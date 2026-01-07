"""Data query execution tools for SQL Anywhere."""

import re
import json
from typing import Optional, List
from sqlanywhere_mcp.db import get_connection_manager
from sqlanywhere_mcp.errors import QueryValidationError, InvalidParameterError, DatabaseError
from sqlanywhere_mcp.models import ResponseFormat, QueryResult
from sqlanywhere_mcp import formatters


def execute_query(
    query: str,
    limit: Optional[int] = None,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
    """
    Execute a SELECT query on the database.

    Args:
        query: SQL SELECT query to execute
        limit: Maximum number of rows to return (default: use config default)
        response_format: Output format (markdown or json)

    Returns:
        Formatted query results in requested format

    Raises:
        ValueError: If query is not a SELECT statement
    """
    # Validate query is SELECT only
    cleaned_query = query.strip().upper()
    if not cleaned_query.startswith("SELECT"):
        raise QueryValidationError(
            query,
            "Only SELECT queries are allowed for security reasons. "
            "The query must start with 'SELECT'."
        )

    # Check for dangerous keywords
    dangerous_patterns = [
        r"\bDROP\b",
        r"\bDELETE\b",
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bCREATE\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bEXEC\b",
        r"\bEXECUTE\b",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, cleaned_query, re.IGNORECASE):
            raise QueryValidationError(
                query,
                f"Dangerous keyword detected: {pattern}. "
                "Only SELECT queries are allowed."
            )

    cm = get_connection_manager()

    # Use configured default limit if not specified
    if limit is None:
        limit = cm.default_max_rows
    else:
        # Enforce maximum limit
        if limit > cm.max_rows_limit:
            raise InvalidParameterError(
                "limit",
                f"Requested limit {limit} exceeds maximum allowed limit of {cm.max_rows_limit}"
            )

    try:
        rows, row_count, execution_time, has_more = cm.execute_query_with_metadata(
            query, max_rows=limit
        )

        # Get column information
        columns = list(rows[0].keys()) if rows else []
        column_types = {col: type(rows[0][col]).__name__ for col in columns} if rows else {}

        # Format output based on response_format
        if response_format == ResponseFormat.JSON:
            # Create QueryResult model and return JSON
            result = QueryResult(
                rows=rows,
                row_count=row_count,
                columns=columns,
                column_types=column_types,
                execution_time_seconds=execution_time,
                has_more=has_more
            )
            return result.model_dump_json(indent=2)
        else:
            # Use formatter for markdown
            return formatters.format_query_results_markdown(rows, row_count, execution_time, has_more, limit)

    except Exception as e:
        raise DatabaseError("query execution", e)


def query_builder(
    table_name: str,
    columns: Optional[str] = "*",
    where: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
    """
    Build and execute a simple SELECT query with parameters.

    This is a convenience tool for building safe SELECT queries.
    The WHERE clause should be a simple condition without user input.

    Args:
        table_name: Table to query with schema/owner prefix (REQUIRED).
            Examples: 'monitor.Part', 'dbo.Customers', 'ExtensionsUser.Config'.
            Format must be: schema.TableName or owner.TableName
        columns: Columns to select (default: *)
        where: WHERE clause condition (optional, use with caution)
        order_by: ORDER BY clause (optional)
        limit: Maximum number of rows to return

    Returns:
        Markdown formatted query results

    Raises:
        ValueError: If table_name is invalid or missing schema prefix

    Example:
        >>> query_builder(table_name='monitor.Part', columns='Id,PartNumber', limit=10)
        Returns: SELECT TOP 10 Id,PartNumber FROM monitor.Part
    """
    # Basic SQL injection prevention for table name
    # Allow schema.table format (e.g., 'monitor.Part')
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$", table_name):
        raise InvalidParameterError(
            "table_name",
            f"Invalid table name: '{table_name}'. "
            "Table name must include schema/owner prefix in format 'schema.TableName'. "
            "Examples: 'monitor.Part', 'dbo.Customers', 'ExtensionsUser.Config'"
        )

    # Validate column names
    if columns != "*":
        col_list = [c.strip() for c in columns.split(",")]
        for col in col_list:
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", col):
                raise InvalidParameterError(
                    "columns",
                    f"Invalid column name: '{col}'"
                )

    # Build query - Use TOP instead of LIMIT for SQL Anywhere
    if limit:
        if limit > 10000:
            raise InvalidParameterError(
                "limit",
                f"Limit {limit} exceeds maximum of 10000"
            )
        query = f"SELECT TOP {limit} {columns} FROM {table_name}"
    else:
        query = f"SELECT {columns} FROM {table_name}"

    if where:
        # Basic validation for WHERE clause
        # Only allow simple conditions
        if re.search(r";|--|/\*|\*/", where, re.IGNORECASE):
            raise InvalidParameterError(
                "where",
                "Invalid characters in WHERE clause"
            )
        query += f" WHERE {where}"

    if order_by:
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC))?(,\s*[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC))?)*$", order_by, re.IGNORECASE):
            raise InvalidParameterError(
                "order_by",
                f"Invalid ORDER BY clause: '{order_by}'"
            )
        query += f" ORDER BY {order_by}"

    # Execute the query with response_format
    return execute_query(query, limit, response_format=response_format)


def validate_query(query: str) -> str:
    """
    Validate a SQL query without executing it.

    This performs basic validation checks on the query.

    Args:
        query: SQL query to validate

    Returns:
        Validation result message
    """
    cleaned_query = query.strip()

    # Check if it starts with SELECT
    if not cleaned_query.upper().startswith("SELECT"):
        return "❌ **Invalid**: Query must start with SELECT"

    # Check for dangerous keywords
    dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER", "TRUNCATE"]

    for keyword in dangerous_keywords:
        if re.search(rf"\b{keyword}\b", cleaned_query, re.IGNORECASE):
            return f"❌ **Invalid**: Dangerous keyword '{keyword}' detected"

    # Basic syntax check (very basic)
    if not re.search(r"\bFROM\b", cleaned_query, re.IGNORECASE):
        return "❌ **Invalid**: SELECT query must include FROM clause"

    return "✅ **Valid**: Query appears to be a safe SELECT query (basic validation passed)"
