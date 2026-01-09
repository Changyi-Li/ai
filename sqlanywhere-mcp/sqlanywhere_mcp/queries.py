"""Data query execution tools for SQL Anywhere."""

import re
import json
from typing import Optional, List
from sqlanywhere_mcp.db import get_connection_manager
from sqlanywhere_mcp.errors import QueryValidationError, InvalidParameterError, DatabaseError
from sqlanywhere_mcp.models import ResponseFormat, QueryResult
from sqlanywhere_mcp import formatters


def _validate_query_authorization(query: str, authorized_users: List[str]) -> None:
    """
    Validate that query only accesses tables/views from authorized users.

    This function parses the FROM clause and JOIN clauses to extract
    owner.table references and validates them against the authorized users list.

    Args:
        query: SQL SELECT query to validate
        authorized_users: List of authorized owner names

    Raises:
        QueryValidationError: If query references unauthorized owners
    """
    # Pattern to match owner.table references in FROM and JOIN clauses
    # Matches: owner.table, "owner"."table", [owner].[table], etc.
    # This looks for FROM/JOIN followed by optional whitespace and owner.table pattern
    from_join_pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\.\s*([a-zA-Z_][a-zA-Z0-9_]*)'

    # Also handle quoted identifiers: "owner"."table" or [owner].[table]
    quoted_pattern = r'\b(?:FROM|JOIN)\s+["\[]?([a-zA-Z_][a-zA-Z0-9_]*)["\]?\s*\.?\s*["\[]?([a-zA-Z_][a-zA-Z0-9_]*)["\]]?'

    # Find all owner.table references
    from_join_matches = re.findall(from_join_pattern, query, re.IGNORECASE)
    quoted_matches = re.findall(quoted_pattern, query, re.IGNORECASE)

    # Combine results and extract owners
    owners = set()
    for match in from_join_matches:
        if isinstance(match, tuple) and len(match) >= 1:
            owners.add(match[0].lower())

    for match in quoted_matches:
        if isinstance(match, tuple) and len(match) >= 1:
            owners.add(match[0].lower())

    # Check if all owners are authorized
    authorized_lower = [u.lower() for u in authorized_users]

    unauthorized = owners - set(authorized_lower)

    if unauthorized:
        raise QueryValidationError(
            query,
            f"Access to owners {', '.join(sorted(unauthorized))} is not authorized. "
            f"Queries can only access tables/views owned by: {', '.join(sorted(authorized_users))}. "
            f"Please ensure all FROM and JOIN clauses reference authorized owners."
        )


async def execute_query(
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
        QueryValidationError: If query references unauthorized owners
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

    # Validate query against authorized users
    _validate_query_authorization(query, cm._authorized_users)

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


async def validate_query(query: str) -> str:
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
