"""Custom exception classes for SQL Anywhere MCP server.

Provides actionable error messages that guide users toward solutions.
"""

from typing import Optional


class MCPError(Exception):
    """Base exception for all MCP server errors."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        """
        Initialize MCP error.

        Args:
            message: Error message describing what went wrong
            suggestion: Optional suggestion for how to fix the issue
        """
        self.message = message
        self.suggestion = suggestion
        super().__init__(self.format_error())

    def format_error(self) -> str:
        """Format error with optional suggestion."""
        error_text = f"## Error\n\n{self.message}"
        if self.suggestion:
            error_text += f"\n\n**Suggestion**: {self.suggestion}"
        return error_text


class DatabaseNotFoundError(MCPError):
    """Raised when a database object (table, view, procedure, index) is not found."""

    def __init__(self, object_type: str, object_name: str):
        """
        Initialize database not found error.

        Args:
            object_type: Type of object (table, view, procedure, index)
            object_name: Name of the object that was not found
        """
        super().__init__(
            message=f"{object_type.capitalize()} '{object_name}' not found or access denied.",
            suggestion=f"Use sqlanywhere_list_{object_type}s to see available {object_type}s."
        )


class AccessDeniedError(MCPError):
    """Raised when access to a database object is denied."""

    def __init__(self, object_type: str, object_name: str):
        """
        Initialize access denied error.

        Args:
            object_type: Type of object (table, view, procedure, index)
            object_name: Name of the object that access was denied to
        """
        super().__init__(
            message=f"Access denied to {object_type} '{object_name}'.",
            suggestion="This object is not owned by an authorized user. "
                      "Check SQLANYWHERE_AUTHORIZED_USERS environment variable."
        )


class QueryValidationError(MCPError):
    """Raised when a SQL query fails validation."""

    def __init__(self, query: str, reason: str):
        """
        Initialize query validation error.

        Args:
            query: The query that failed validation
            reason: Why the query failed validation
        """
        super().__init__(
            message=f"Query validation failed: {reason}",
            suggestion="Ensure the query is a valid SELECT statement and does not contain "
                      "dangerous keywords (DROP, DELETE, INSERT, UPDATE, etc.)."
        )


class ConnectionError(MCPError):
    """Raised when database connection fails."""

    def __init__(self, message: str, details: Optional[str] = None):
        """
        Initialize connection error.

        Args:
            message: Error message
            details: Optional additional details about the connection failure
        """
        suggestion = (
            "Please verify:\n"
            "1. SQL Anywhere ODBC driver is installed\n"
            "2. Database server is running\n"
            "3. Connection parameters are correct"
        )
        if details:
            message = f"{message}\n\n{details}"
        super().__init__(message=message, suggestion=suggestion)


class DatabaseError(MCPError):
    """Raised when a database operation fails."""

    def __init__(self, operation: str, original_error: Exception):
        """
        Initialize database error.

        Args:
            operation: The operation that failed (e.g., "query execution")
            original_error: The original exception that caused this error
        """
        super().__init__(
            message=f"Database {operation} failed: {str(original_error)}",
            suggestion="Check the query syntax and ensure the database is in a consistent state."
        )


class InvalidParameterError(MCPError):
    """Raised when an invalid parameter is provided to a tool."""

    def __init__(self, parameter_name: str, reason: str):
        """
        Initialize invalid parameter error.

        Args:
            parameter_name: Name of the invalid parameter
            reason: Why the parameter is invalid
        """
        super().__init__(
            message=f"Invalid parameter '{parameter_name}': {reason}",
            suggestion="Check the tool's input schema for valid parameter values."
        )
