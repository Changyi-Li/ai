"""Data query execution tools for SQL Anywhere."""

import re
from typing import Optional, List
from sqlanywhere_mcp.db import get_connection_manager
from sqlanywhere_mcp.errors import QueryValidationError, InvalidParameterError, DatabaseError


def execute_query(query: str, limit: Optional[int] = None) -> str:
    """
    Execute a SELECT query on the database.

    Args:
        query: SQL SELECT query to execute
        limit: Maximum number of rows to return (default: use config default)

    Returns:
        Markdown formatted query results with metadata

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

        if not rows:
            return f"## Query Results\n\nNo rows returned.\n\n**Execution time**: {execution_time:.3f} seconds"

        # Format output
        output = []
        output.append("## Query Results")
        output.append("")
        output.append(f"**Rows returned**: {row_count:,}")
        output.append(f"**Execution time**: {execution_time:.3f} seconds")
        if has_more:
            output.append(f"**⚠️ Note**: Result set truncated at {limit} rows (more rows exist)")
        output.append("")

        # Get column names from first row
        columns = list(rows[0].keys())

        # Create table header
        output.append("| " + " | ".join(columns) + " |")
        output.append("| " + " | ".join(["---"] * len(columns)) + " |")

        # Add rows
        for row in rows:
            # Convert values to strings and handle None
            values = []
            for col in columns:
                val = row[col]
                if val is None:
                    values.append("NULL")
                else:
                    # Truncate long strings
                    val_str = str(val)
                    if len(val_str) > 100:
                        val_str = val_str[:97] + "..."
                    values.append(val_str)
            output.append("| " + " | ".join(values) + " |")

        return "\n".join(output)

    except Exception as e:
        raise DatabaseError("query execution", e)


def query_builder(
    table_name: str,
    columns: Optional[str] = "*",
    where: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
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

    # Execute the query
    return execute_query(query, limit)


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
