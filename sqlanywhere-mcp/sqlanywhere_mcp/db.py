"""Database connection management for SQL Anywhere."""

import os
import time
from typing import Optional, List
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ConnectionManager:
    """Manages SQL Anywhere database connections via ODBC."""

    def __init__(self):
        """Initialize connection manager with environment variables."""
        self._connection: Optional[pyodbc.Connection] = None
        self._connection_string = self._build_connection_string()
        self._query_timeout = int(os.getenv("SQLANYWHERE_QUERY_TIMEOUT", "30"))
        self._max_rows = int(os.getenv("SQLANYWHERE_MAX_ROWS", "1000"))
        self._max_rows_limit = int(os.getenv("SQLANYWHERE_MAX_ROWS_LIMIT", "10000"))
        self._authorized_users = self._parse_authorized_users()

    def _parse_authorized_users(self) -> List[str]:
        """
        Parse authorized users from environment variable.

        Returns:
            List of authorized user names for schema filtering
        """
        users_str = os.getenv("SQLANYWHERE_AUTHORIZED_USERS", "monitor,ExtensionsUser")
        return [u.strip() for u in users_str.split(",") if u.strip()]

    def _build_connection_string(self) -> str:
        """
        Build ODBC connection string from environment variables.

        SQL Anywhere connection parameters:
        - Shared Memory: DRIVER, ServerName, DBN, UID, PWD
        - TCP/IP: DRIVER, ServerName, Host=hostname:port, DBN, UID, PWD

        Returns:
            ODBC connection string
        """
        # If full connection string is provided, use it
        conn_str = os.getenv("SQLANYWHERE_CONNECTION_STRING")
        if conn_str:
            return conn_str

        # Otherwise build from individual components
        driver = os.getenv("SQLANYWHERE_DRIVER", "SQL Anywhere 17")
        host = os.getenv("SQLANYWHERE_HOST")
        port = os.getenv("SQLANYWHERE_PORT", "2638")
        database = os.getenv("SQLANYWHERE_DATABASE", "")
        user = os.getenv("SQLANYWHERE_USER", "")
        password = os.getenv("SQLANYWHERE_PASSWORD", "")
        server_name = os.getenv("SQLANYWHERE_SERVER_NAME", "")
        use_tcp = os.getenv("SQLANYWHERE_USE_TCP", "false").lower() in ("true", "yes", "1")

        if not database:
            raise ValueError(
                "SQLANYWHERE_DATABASE or SQLANYWHERE_CONNECTION_STRING must be provided"
            )

        # Build connection string with SQL Anywhere-specific parameters
        parts = [
            f"DRIVER={{{driver}}}",
            f"DBN={database}",  # SQL Anywhere uses DBN, not DATABASE
        ]

        # Add authentication
        if user:
            parts.append(f"UID={user}")
        if password:
            parts.append(f"PWD={password}")

        # ServerName is required for all connections
        if server_name:
            parts.append(f"ServerName={server_name}")
        else:
            # Log warning but continue for backward compatibility
            import warnings
            warnings.warn(
                "SQLANYWHERE_SERVER_NAME is not set. ServerName is recommended for all connections. "
                "Set SQLANYWHERE_SERVER_NAME environment variable or use a complete connection string.",
                UserWarning
            )

        # Add Host parameter for TCP/IP connections (Host=hostname:port format)
        if use_tcp and host:
            parts.append(f"Host={host}:{port}")

        # Optional encryption
        encrypt = os.getenv("SQLANYWHERE_ENCRYPT", "")
        if encrypt.lower() in ("true", "yes", "1"):
            parts.append("ENCRYPT=YES")

        return ";".join(parts)

    @property
    def query_timeout(self) -> int:
        """Get query timeout in seconds."""
        return self._query_timeout

    @property
    def default_max_rows(self) -> int:
        """Get default maximum rows for queries."""
        return self._max_rows

    @property
    def max_rows_limit(self) -> int:
        """Get maximum allowed row limit."""
        return self._max_rows_limit

    def connect(self) -> pyodbc.Connection:
        """
        Establish connection to SQL Anywhere database.

        Returns:
            Active pyodbc connection

        Raises:
            pyodbc.Error: If connection fails
        """
        if self._connection is None:
            try:
                self._connection = pyodbc.connect(
                    self._connection_string,
                    timeout=self._query_timeout,
                    autocommit=True
                )
            except pyodbc.Error as e:
                raise ConnectionError(
                    f"Failed to connect to SQL Anywhere database: {e}\n"
                    f"Connection string: {self._connection_string}\n"
                    f"Please verify:\n"
                    f"1. SQL Anywhere ODBC driver is installed\n"
                    f"2. Database server is running\n"
                    f"3. Connection parameters are correct"
                ) from e

        return self._connection

    def disconnect(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def reconnect(self) -> pyodbc.Connection:
        """
        Force reconnection to the database.

        Returns:
            New pyodbc connection
        """
        self.disconnect()
        return self.connect()

    def is_connected(self) -> bool:
        """
        Check if connection is active and valid.

        Returns:
            True if connection is valid
        """
        if self._connection is None:
            return False

        try:
            # Try a simple query to validate connection
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except pyodbc.Error:
            return False

    def get_connection(self) -> pyodbc.Connection:
        """
        Get active connection, reconnecting if necessary.

        Returns:
            Active pyodbc connection
        """
        if not self.is_connected():
            return self.reconnect()
        return self._connection

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        max_rows: Optional[int] = None
    ) -> tuple[list[dict], list[str], dict[str, str]]:
        """
        Execute a query and return results.

        Args:
            query: SQL query to execute
            params: Optional query parameters
            max_rows: Maximum number of rows to return

        Returns:
            Tuple of (rows as dicts, column names, column types)
        """
        start_time = time.time()

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Fetch rows
            if max_rows:
                rows = cursor.fetchmany(max_rows)
            else:
                rows = cursor.fetchall()

            # Get column information
            columns = [column[0] for column in cursor.description]
            column_types = {
                column[0]: self._get_sql_type_name(column[1])
                for column in cursor.description
            }

            # Convert to list of dicts
            result = [dict(zip(columns, row)) for row in rows]

            execution_time = time.time() - start_time

            return result, columns, column_types

        finally:
            cursor.close()

    def execute_query_with_metadata(
        self,
        query: str,
        params: Optional[tuple] = None,
        max_rows: Optional[int] = None
    ) -> tuple[list[dict], int, float, bool]:
        """
        Execute a query and return results with metadata.

        Args:
            query: SQL query to execute
            params: Optional query parameters
            max_rows: Maximum number of rows to return

        Returns:
            Tuple of (rows, row_count, execution_time, has_more)
        """
        start_time = time.time()

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Fetch rows
            if max_rows:
                rows = cursor.fetchmany(max_rows + 1)
                has_more = len(rows) > max_rows
                if has_more:
                    rows = rows[:max_rows]
            else:
                rows = cursor.fetchall()
                has_more = False

            # Get column information
            columns = [column[0] for column in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]

            execution_time = time.time() - start_time

            return result, len(result), execution_time, has_more

        finally:
            cursor.close()

    def _get_sql_type_name(self, type_code: int) -> str:
        """
        Get SQL type name from type code.

        Args:
            type_code: SQL type code

        Returns:
            Type name string
        """
        # Map common SQL types to names
        type_map = {
            pyodbc.SQL_CHAR: "CHAR",
            pyodbc.SQL_VARCHAR: "VARCHAR",
            pyodbc.SQL_LONGVARCHAR: "LONGVARCHAR",
            pyodbc.SQL_WCHAR: "NCHAR",
            pyodbc.SQL_WVARCHAR: "NVARCHAR",
            pyodbc.SQL_WLONGVARCHAR: "NLONGVARCHAR",
            pyodbc.SQL_DECIMAL: "DECIMAL",
            pyodbc.SQL_NUMERIC: "NUMERIC",
            pyodbc.SQL_SMALLINT: "SMALLINT",
            pyodbc.SQL_INTEGER: "INTEGER",
            pyodbc.SQL_REAL: "REAL",
            pyodbc.SQL_FLOAT: "FLOAT",
            pyodbc.SQL_DOUBLE: "DOUBLE",
            pyodbc.SQL_BIT: "BIT",
            pyodbc.SQL_TINYINT: "TINYINT",
            pyodbc.SQL_BIGINT: "BIGINT",
            pyodbc.SQL_BINARY: "BINARY",
            pyodbc.SQL_VARBINARY: "VARBINARY",
            pyodbc.SQL_LONGVARBINARY: "LONGVARBINARY",
            pyodbc.SQL_TYPE_DATE: "DATE",
            pyodbc.SQL_TYPE_TIME: "TIME",
            pyodbc.SQL_TYPE_TIMESTAMP: "TIMESTAMP",
            pyodbc.SQL_GUID: "GUID",
        }

        return type_map.get(type_code, f"UNKNOWN({type_code})")


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    Get global connection manager instance.

    Returns:
        ConnectionManager instance
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
