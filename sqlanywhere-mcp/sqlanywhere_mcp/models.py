"""Pydantic models for SQL Anywhere database schema objects.

Models are organized by tool/functionality:
- Common models (used across multiple tools)
- Table tools (list_tables, get_table_details)
- View tools (list_views, get_view_details)
- Procedure tools (list_procedures, get_procedure_details)
- Index tools (list_indexes, get_index_details)
- Query tools (execute_query, query_builder, validate_query)
"""

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ============================================================================
# Common Models
# ============================================================================

class ResponseFormat(str, Enum):
    """Response format options for tool outputs."""
    MARKDOWN = "markdown"
    JSON = "json"


# ============================================================================
# Table Tools Models
# ============================================================================

# Input Models
class ListTablesInput(BaseModel):
    """Input model for list_tables operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    owner: Optional[str] = Field(default=None, description="Filter by owner (e.g., 'monitor', 'dbo')", min_length=1, max_length=200)
    search: Optional[str] = Field(default=None, description="Search for tables by name substring", min_length=1, max_length=200)
    limit: int = Field(default=100, description="Maximum number of tables to return", ge=1, le=10000)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

    @field_validator('owner', 'search')
    @classmethod
    def validate_owner_or_search(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that only owner or search is provided, not both."""
        if v is not None and not v.strip():
            raise ValueError("Cannot be empty string")
        # Check mutual exclusion in model_validator
        return v

    @model_validator(mode='after')
    def validate_mutually_exclusive(self) -> 'ListTablesInput':
        """Validate that owner and search are not both provided."""
        if self.owner is not None and self.search is not None:
            raise ValueError("Cannot specify both 'owner' and 'search' parameters. Use one or the other.")
        return self


class GetTableDetailsInput(BaseModel):
    """Input model for get_table_details operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    table_name: str = Field(..., description="Table name (e.g., 'Part', 'monitor.Part') - Accepts both formats", min_length=1, max_length=200)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

    @field_validator('table_name')
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        """Validate that table_name is not empty after stripping."""
        if not v or not v.strip():
            raise ValueError("Table name cannot be empty")
        return v


# Output/Response Models
class ColumnInfo(BaseModel):
    """Information about a table column."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    name: str = Field(description="Column name")
    type: str = Field(description="Column data type")
    length: Optional[int] = Field(default=None, description="Column length or precision")
    scale: Optional[int] = Field(default=None, description="Scale for numeric types")
    nullable: bool = Field(description="Whether column allows NULL values")
    default_value: Optional[str] = Field(default=None, description="Default value")
    is_primary_key: bool = Field(default=False, description="Whether column is part of primary key")


class PrimaryKeyInfo(BaseModel):
    """Information about a primary key."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    name: str = Field(description="Primary key constraint name")
    column_names: List[str] = Field(description="Columns in the primary key")


class ForeignKeyInfo(BaseModel):
    """Information about a foreign key."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    name: str = Field(description="Foreign key constraint name")
    column_names: List[str] = Field(description="Columns in the foreign key")
    referenced_table: str = Field(description="Referenced table name")
    referenced_columns: List[str] = Field(description="Referenced column names")
    on_delete: Optional[str] = Field(default=None, description="ON DELETE action")
    on_update: Optional[str] = Field(default=None, description="ON UPDATE action")


class IndexColumn(BaseModel):
    """Column information within an index."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    column_name: str = Field(description="Column name")
    order: str = Field(description="Ascending or descending")


class IndexInfo(BaseModel):
    """Information about an index."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    name: str = Field(description="Index name")
    table_name: str = Field(description="Table name")
    is_unique: bool = Field(description="Whether index is unique")
    is_primary_key: bool = Field(description="Whether this is a primary key index")
    columns: List[IndexColumn] = Field(description="Columns in the index")
    index_type: Optional[str] = Field(default=None, description="Index type")


class CheckConstraint(BaseModel):
    """Information about a check constraint."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    name: str = Field(description="Constraint name")
    constraint_definition: str = Field(description="Check constraint definition")


class TableInfo(BaseModel):
    """Information about a database table."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    name: str = Field(description="Table name")
    owner: str = Field(description="Table owner")
    table_type: str = Field(description="TABLE or VIEW")
    row_count: Optional[int] = Field(default=None, description="Estimated row count")
    columns: List[ColumnInfo] = Field(description="Table columns")
    primary_keys: List[PrimaryKeyInfo] = Field(description="Primary key constraints")
    foreign_keys: List[ForeignKeyInfo] = Field(description="Foreign key constraints")
    indexes: List[IndexInfo] = Field(description="Indexes on the table")
    check_constraints: List[CheckConstraint] = Field(description="Check constraints")


class TableListResponse(BaseModel):
    """Response from list_tables tool."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    tables: List[TableInfo] = Field(description="List of tables")
    total_count: int = Field(description="Total number of tables found")
    has_more: bool = Field(description="Whether more tables exist beyond the limit")


# ============================================================================
# View Tools Models
# ============================================================================

# Input Models
class ListViewsInput(BaseModel):
    """Input model for list_views operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    owner: Optional[str] = Field(default=None, description="Filter by owner (e.g., 'monitor', 'dbo')", min_length=1, max_length=200)
    search: Optional[str] = Field(default=None, description="Search for views by name substring", min_length=1, max_length=200)
    limit: int = Field(default=100, description="Maximum number of views to return", ge=1, le=10000)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

    @field_validator('owner', 'search')
    @classmethod
    def validate_owner_or_search(cls, v: Optional[str]) -> Optional[str]:
        """Validate that only owner or search is provided, not both."""
        if v is not None and not v.strip():
            raise ValueError("Cannot be empty string")
        return v

    @model_validator(mode='after')
    def validate_mutually_exclusive(self) -> 'ListViewsInput':
        """Validate that owner and search are not both provided."""
        if self.owner is not None and self.search is not None:
            raise ValueError("Cannot specify both 'owner' and 'search' parameters. Use one or the other.")
        return self


class GetViewDetailsInput(BaseModel):
    """Input model for get_view_details operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    view_name: str = Field(..., description="View name (e.g., 'CustomerView', 'monitor.CustomerView') - Accepts both formats", min_length=1, max_length=200)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

    @field_validator('view_name')
    @classmethod
    def validate_view_name(cls, v: str) -> str:
        """Validate that view_name is not empty after stripping."""
        if not v or not v.strip():
            raise ValueError("View name cannot be empty")
        return v


# Output/Response Models
class ViewInfo(BaseModel):
    """Information about a database view."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    name: str = Field(description="View name")
    owner: str = Field(description="View owner")
    definition: Optional[str] = Field(default=None, description="View definition SQL")
    columns: List[ColumnInfo] = Field(default=[], description="View columns")


class ViewListResponse(BaseModel):
    """Response from list_views tool."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    views: List[ViewInfo] = Field(description="List of views")
    total_count: int = Field(description="Total number of views found")
    has_more: bool = Field(description="Whether more views exist beyond the limit")


# ============================================================================
# Procedure Tools Models
# ============================================================================

# Input Models
class ListProceduresInput(BaseModel):
    """Input model for list_procedures operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    owner: Optional[str] = Field(default=None, description="Filter by owner (e.g., 'monitor', 'dbo', 'sys')", min_length=1, max_length=200)
    search: Optional[str] = Field(default=None, description="Search for procedures by name substring", min_length=1, max_length=200)
    limit: int = Field(default=100, description="Maximum number of procedures to return", ge=1, le=10000)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

    @field_validator('owner', 'search')
    @classmethod
    def validate_owner_or_search(cls, v: Optional[str]) -> Optional[str]:
        """Validate that only owner or search is provided, not both."""
        if v is not None and not v.strip():
            raise ValueError("Cannot be empty string")
        return v

    @model_validator(mode='after')
    def validate_mutually_exclusive(self) -> 'ListProceduresInput':
        """Validate that owner and search are not both provided."""
        if self.owner is not None and self.search is not None:
            raise ValueError("Cannot specify both 'owner' and 'search' parameters. Use one or the other.")
        return self


class GetProcedureDetailsInput(BaseModel):
    """Input model for get_procedure_details operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    procedure_name: str = Field(..., description="Procedure name (e.g., 'GetUser', 'monitor.GetUser') - Accepts both formats", min_length=1, max_length=200)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

    @field_validator('procedure_name')
    @classmethod
    def validate_procedure_name(cls, v: str) -> str:
        """Validate that procedure_name is not empty after stripping."""
        if not v or not v.strip():
            raise ValueError("Procedure name cannot be empty")
        return v


# Output/Response Models
class ProcedureParameter(BaseModel):
    """Information about a stored procedure parameter."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter data type")
    mode: str = Field(description="Parameter mode: IN, OUT, or INOUT")


class ProcedureInfo(BaseModel):
    """Information about a stored procedure or function."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    name: str = Field(description="Procedure name")
    owner: str = Field(description="Procedure owner")
    procedure_type: str = Field(description="PROCEDURE or FUNCTION")
    parameters: List[ProcedureParameter] = Field(description="Procedure parameters")
    return_type: Optional[str] = Field(default=None, description="Return type for functions")
    definition: Optional[str] = Field(default=None, description="Procedure definition SQL")


class ProcedureListResponse(BaseModel):
    """Response from list_procedures tool."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    procedures: List[ProcedureInfo] = Field(description="List of procedures")
    total_count: int = Field(description="Total number of procedures found")
    has_more: bool = Field(description="Whether more procedures exist beyond the limit")


# ============================================================================
# Index Tools Models
# ============================================================================

# Input Models
class ListIndexesInput(BaseModel):
    """Input model for list_indexes operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    table_name: Optional[str] = Field(default=None, description="Filter by table name (e.g., 'Part', 'Customers')", min_length=1, max_length=200)
    limit: int = Field(default=100, description="Maximum number of indexes to return", ge=1, le=10000)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

    @field_validator('table_name')
    @classmethod
    def validate_table_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate that table_name is not empty after stripping if provided."""
        if v is not None and not v.strip():
            raise ValueError("Table name cannot be empty")
        return v


class GetIndexDetailsInput(BaseModel):
    """Input model for get_index_details operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    index_name: str = Field(..., description="Index name (e.g., 'Part_PK', 'idx_customer_email')", min_length=1, max_length=200)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


# Output/Response Models
class IndexListResponse(BaseModel):
    """Response from list_indexes tool."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    indexes: List[IndexInfo] = Field(description="List of indexes")
    total_count: int = Field(description="Total number of indexes found")
    has_more: bool = Field(description="Whether more indexes exist beyond the limit")


# ============================================================================
# Query Tools Models
# ============================================================================

# Input Models
class ExecuteQueryInput(BaseModel):
    """Input model for execute_query operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    query: str = Field(..., description="SQL SELECT query to execute", min_length=1, max_length=10000)
    limit: Optional[int] = Field(default=None, description="Maximum rows to return (default: 1000, max: 10000)", ge=1, le=10000)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

    @field_validator('query')
    @classmethod
    def validate_is_select(cls, v: str) -> str:
        """Validate that query starts with SELECT."""
        if not v.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")
        return v


class QueryBuilderInput(BaseModel):
    """Input model for query_builder operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    table_name: str = Field(..., description="Table name with owner prefix (REQUIRED)", min_length=3, max_length=200)
    columns: str = Field(default="*", description="Columns to select (default: '*')", max_length=1000)
    where: Optional[str] = Field(default=None, description="WHERE clause condition", max_length=2000)
    order_by: Optional[str] = Field(default=None, description="ORDER BY clause", max_length=500)
    limit: Optional[int] = Field(default=None, description="Row limit (default: 100, max: 10000)", ge=1, le=10000)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

    @field_validator('table_name')
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        """Validate that table_name includes owner prefix."""
        if '.' not in v:
            raise ValueError("Must include owner prefix (e.g., 'monitor.Part', 'dbo.Customers')")
        return v

    @field_validator('columns')
    @classmethod
    def validate_columns(cls, v: str) -> str:
        """Validate column names for SQL injection."""
        if v != "*":
            import re
            col_list = [c.strip() for c in v.split(",")]
            for col in col_list:
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", col):
                    raise ValueError(f"Invalid column name: '{col}'")
        return v

    @field_validator('where')
    @classmethod
    def validate_where(cls, v: Optional[str]) -> Optional[str]:
        """Validate WHERE clause for SQL injection patterns."""
        if v:
            import re
            if re.search(r";|--|/\*|\*/", v, re.IGNORECASE):
                raise ValueError("Invalid characters in WHERE clause (detected comment or statement separator)")
        return v

    @field_validator('order_by')
    @classmethod
    def validate_order_by(cls, v: Optional[str]) -> Optional[str]:
        """Validate ORDER BY clause format."""
        if v:
            import re
            pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC))?(,\s*[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC))?)*$"
            if not re.match(pattern, v, re.IGNORECASE):
                raise ValueError(f"Invalid ORDER BY clause: '{v}'")
        return v


class ValidateQueryInput(BaseModel):
    """Input model for validate_query operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    query: str = Field(..., description="SQL query to validate", min_length=1, max_length=10000)

    @field_validator('query')
    @classmethod
    def validate_is_select(cls, v: str) -> str:
        """Validate that query starts with SELECT."""
        if not v.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")
        return v


# Output/Response Models
class QueryResult(BaseModel):
    """Result of a data query."""
    model_config = ConfigDict(
        validate_assignment=True
    )
    rows: List[dict] = Field(description="Query result rows")
    row_count: int = Field(description="Number of rows returned")
    columns: List[str] = Field(description="Column names")
    column_types: dict = Field(description="Column name to type mapping")
    execution_time_seconds: float = Field(description="Query execution time in seconds")
    has_more: bool = Field(default=False, description="Whether more rows exist beyond limit")


# ============================================================================
# Database Info Models
# ============================================================================

class DatabaseInfo(BaseModel):
    """Information about the database."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    database_name: str = Field(description="Database name")
    server_name: str = Field(description="Server name")
    version: str = Field(description="SQL Anywhere version")
    charset: Optional[str] = Field(default=None, description="Database character set")
    collation: Optional[str] = Field(default=None, description="Database collation")
    page_size: Optional[int] = Field(default=None, description="Database page size")
