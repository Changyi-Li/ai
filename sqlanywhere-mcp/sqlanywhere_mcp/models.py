"""Pydantic models for SQL Anywhere database schema objects."""

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Response Format Enum
# ============================================================================

class ResponseFormat(str, Enum):
    """Response format options for tool outputs."""
    MARKDOWN = "markdown"
    JSON = "json"


# ============================================================================
# Response Wrapper Models
# ============================================================================

class TableListResponse(BaseModel):
    """Response from list_tables tool."""
    tables: List[TableInfo] = Field(description="List of tables")
    total_count: int = Field(description="Total number of tables found")
    has_more: bool = Field(description="Whether more tables exist beyond the limit")


class ViewListResponse(BaseModel):
    """Response from list_views tool."""
    views: List[ViewInfo] = Field(description="List of views")
    total_count: int = Field(description="Total number of views found")
    has_more: bool = Field(description="Whether more views exist beyond the limit")


class ProcedureListResponse(BaseModel):
    """Response from list_procedures tool."""
    procedures: List[ProcedureInfo] = Field(description="List of procedures")
    total_count: int = Field(description="Total number of procedures found")
    has_more: bool = Field(description="Whether more procedures exist beyond the limit")


class IndexListResponse(BaseModel):
    """Response from list_indexes tool."""
    indexes: List[IndexInfo] = Field(description="List of indexes")
    total_count: int = Field(description="Total number of indexes found")
    has_more: bool = Field(description="Whether more indexes exist beyond the limit")


# ============================================================================
# Input Validation Models
# ============================================================================

class TableQueryInput(BaseModel):
    """Input validation for table-related queries."""
    table_name: str = Field(..., min_length=3, max_length=200, description="Table name with schema prefix")

    @field_validator('table_name')
    def validate_schema_prefix(cls, v):
        """Validate that table_name includes schema prefix."""
        if '.' not in v:
            raise ValueError("Must include schema/owner prefix (e.g., 'monitor.Part', 'dbo.Customers')")
        # Basic SQL injection prevention
        import re
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$", v):
            raise ValueError(f"Invalid table name format: '{v}'")
        return v


class QueryInput(BaseModel):
    """Input validation for SQL queries."""
    query: str = Field(..., min_length=1, max_length=10000, description="SQL SELECT query")

    @field_validator('query')
    def validate_is_select(cls, v):
        """Validate that query starts with SELECT."""
        if not v.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")
        return v


class ColumnsInput(BaseModel):
    """Input validation for column specifications."""
    columns: str = Field(default="*", description="Columns to select")

    @field_validator('columns')
    def validate_column_names(cls, v):
        """Validate column names for SQL injection."""
        if v != "*":
            import re
            col_list = [c.strip() for c in v.split(",")]
            for col in col_list:
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", col):
                    raise ValueError(f"Invalid column name: '{col}'")
        return v


class OrderByInput(BaseModel):
    """Input validation for ORDER BY clauses."""
    order_by: Optional[str] = Field(default=None, description="ORDER BY clause")

    @field_validator('order_by')
    def validate_order_by(cls, v):
        """Validate ORDER BY clause format."""
        if v:
            import re
            pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC))?(,\s*[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC))?)*$"
            if not re.match(pattern, v, re.IGNORECASE):
                raise ValueError(f"Invalid ORDER BY clause: '{v}'")
        return v


class WhereInput(BaseModel):
    """Input validation for WHERE clauses."""
    where: Optional[str] = Field(default=None, description="WHERE clause condition")

    @field_validator('where')
    def validate_where(cls, v):
        """Validate WHERE clause for SQL injection patterns."""
        if v:
            import re
            # Check for dangerous patterns
            if re.search(r";|--|/\*|\*/", v, re.IGNORECASE):
                raise ValueError("Invalid characters in WHERE clause (detected comment or statement separator)")
        return v


# ============================================================================
# Existing Schema Models (unchanged)
# ============================================================================

class ColumnInfo(BaseModel):
    """Information about a table column."""
    name: str = Field(description="Column name")
    type: str = Field(description="Column data type")
    length: Optional[int] = Field(default=None, description="Column length or precision")
    scale: Optional[int] = Field(default=None, description="Scale for numeric types")
    nullable: bool = Field(description="Whether column allows NULL values")
    default_value: Optional[str] = Field(default=None, description="Default value")
    is_primary_key: bool = Field(default=False, description="Whether column is part of primary key")


class PrimaryKeyInfo(BaseModel):
    """Information about a primary key."""
    name: str = Field(description="Primary key constraint name")
    column_names: List[str] = Field(description="Columns in the primary key")


class ForeignKeyInfo(BaseModel):
    """Information about a foreign key."""
    name: str = Field(description="Foreign key constraint name")
    column_names: List[str] = Field(description="Columns in the foreign key")
    referenced_table: str = Field(description="Referenced table name")
    referenced_columns: List[str] = Field(description="Referenced column names")
    on_delete: Optional[str] = Field(default=None, description="ON DELETE action")
    on_update: Optional[str] = Field(default=None, description="ON UPDATE action")


class IndexColumn(BaseModel):
    """Column information within an index."""
    column_name: str = Field(description="Column name")
    order: str = Field(description="Ascending or descending")


class IndexInfo(BaseModel):
    """Information about an index."""
    name: str = Field(description="Index name")
    table_name: str = Field(description="Table name")
    is_unique: bool = Field(description="Whether index is unique")
    is_primary_key: bool = Field(description="Whether this is a primary key index")
    columns: List[IndexColumn] = Field(description="Columns in the index")
    index_type: Optional[str] = Field(default=None, description="Index type")


class CheckConstraint(BaseModel):
    """Information about a check constraint."""
    name: str = Field(description="Constraint name")
    constraint_definition: str = Field(description="Check constraint definition")


class TableInfo(BaseModel):
    """Information about a database table."""
    name: str = Field(description="Table name")
    owner: str = Field(description="Table owner/schema")
    table_type: str = Field(description="TABLE or VIEW")
    row_count: Optional[int] = Field(default=None, description="Estimated row count")
    columns: List[ColumnInfo] = Field(description="Table columns")
    primary_keys: List[PrimaryKeyInfo] = Field(description="Primary key constraints")
    foreign_keys: List[ForeignKeyInfo] = Field(description="Foreign key constraints")
    indexes: List[IndexInfo] = Field(description="Indexes on the table")
    check_constraints: List[CheckConstraint] = Field(description="Check constraints")


class ViewInfo(BaseModel):
    """Information about a database view."""
    name: str = Field(description="View name")
    owner: str = Field(description="View owner/schema")
    definition: Optional[str] = Field(default=None, description="View definition SQL")
    columns: List[ColumnInfo] = Field(default=[], description="View columns")


class ProcedureParameter(BaseModel):
    """Information about a stored procedure parameter."""
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter data type")
    mode: str = Field(description="Parameter mode: IN, OUT, or INOUT")


class ProcedureInfo(BaseModel):
    """Information about a stored procedure or function."""
    name: str = Field(description="Procedure name")
    owner: str = Field(description="Procedure owner/schema")
    procedure_type: str = Field(description="PROCEDURE or FUNCTION")
    parameters: List[ProcedureParameter] = Field(description="Procedure parameters")
    return_type: Optional[str] = Field(default=None, description="Return type for functions")
    definition: Optional[str] = Field(default=None, description="Procedure definition SQL")


class QueryResult(BaseModel):
    """Result of a data query."""
    rows: List[dict] = Field(description="Query result rows")
    row_count: int = Field(description="Number of rows returned")
    columns: List[str] = Field(description="Column names")
    column_types: dict = Field(description="Column name to type mapping")
    execution_time_seconds: float = Field(description="Query execution time in seconds")
    has_more: bool = Field(default=False, description="Whether more rows exist beyond limit")


class DatabaseInfo(BaseModel):
    """Information about the database."""
    database_name: str = Field(description="Database name")
    server_name: str = Field(description="Server name")
    version: str = Field(description="SQL Anywhere version")
    charset: Optional[str] = Field(default=None, description="Database character set")
    collation: Optional[str] = Field(default=None, description="Database collation")
    page_size: Optional[int] = Field(default=None, description="Database page size")
