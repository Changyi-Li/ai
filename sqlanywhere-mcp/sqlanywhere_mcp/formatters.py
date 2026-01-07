"""Markdown formatting utilities for SQL Anywhere MCP server.

Provides consistent formatting functions for all tool outputs.
"""

from typing import List, Dict, Any
from sqlanywhere_mcp.models import (
    TableInfo,
    ViewInfo,
    ProcedureInfo,
    IndexInfo,
    ColumnInfo,
    PrimaryKeyInfo,
    ForeignKeyInfo,
    IndexColumn,
)


# ============================================================================
# Generic Markdown Utilities
# ============================================================================

def format_markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    """
    Format data as a Markdown table.

    Args:
        headers: Column headers
        rows: Table rows (each row is a list of string values)

    Returns:
        Markdown formatted table
    """
    if not rows:
        return "*No data*"

    output = []
    output.append("| " + " | ".join(headers) + " |")
    output.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        # Convert values to strings and handle None
        values = [str(v) if v is not None else "NULL" for v in row]
        output.append("| " + " | ".join(values) + " |")

    return "\n".join(output)


def format_markdown_section(title: str, content: str, level: int = 2) -> str:
    """
    Format a Markdown section with title and content.

    Args:
        title: Section title
        content: Section content
        level: Header level (default: 2 for ##)

    Returns:
        Markdown formatted section
    """
    return f"{'#' * level} {title}\n\n{content}"


# ============================================================================
# Table Formatting
# ============================================================================

def format_table_list_markdown(tables: List[tuple], total_count: int) -> str:
    """
    Format table list as Markdown.

    Args:
        tables: List of (table_name, owner, table_type, row_count) tuples
        total_count: Total number of tables

    Returns:
        Markdown formatted table list
    """
    output = []
    output.append(f"## Tables ({total_count} found)")
    output.append("")
    output.append("| Table Name | Owner | Type | Row Count |")
    output.append("|------------|-------|------|-----------|")

    for table_name, table_owner, table_type, row_count in tables:
        row_count_str = f"{row_count:,}" if row_count else "N/A"
        output.append(f"| {table_name} | {table_owner} | {table_type} | {row_count_str} |")

    return "\n".join(output)


def format_table_details_markdown(
    table_name: str,
    owner: str,
    table_type: str,
    row_count: int,
    columns: List[tuple],
    primary_keys: List[tuple],
    foreign_keys: List[tuple],
    indexes: List[tuple]
) -> str:
    """
    Format table details as Markdown.

    Args:
        table_name: Table name
        owner: Table owner
        table_type: Table type
        row_count: Row count
        columns: List of column tuples
        primary_keys: List of primary key tuples
        foreign_keys: List of foreign key tuples
        indexes: List of index tuples

    Returns:
        Markdown formatted table details
    """
    output = []
    output.append(f"## Table: {owner}.{table_name}")
    output.append(f"**Type**: {table_type}")
    output.append(f"**Row Count**: {row_count:,}" if row_count else "**Row Count**: N/A")
    output.append("")

    # Columns
    if columns:
        output.append(f"### Columns ({len(columns)})")
        output.append("")
        output.append("| Column | Type | Length | Scale | Nullable | Default |")
        output.append("|--------|------|--------|-------|----------|---------|")

        for col in columns:
            col_name, domain_id, width, scale, nulls, default_val = col
            nullable = "YES" if nulls == "Y" else "NO"
            default = default_val if default_val else ""
            output.append(f"| {col_name} | {domain_id} | {width or ''} | {scale or ''} | {nullable} | {default} |")

        output.append("")

    # Primary Keys
    if primary_keys:
        output.append("### Primary Keys")
        output.append("")
        pk_dict = {}
        for pk_name, col_name in primary_keys:
            if pk_name not in pk_dict:
                pk_dict[pk_name] = []
            pk_dict[pk_name].append(col_name)

        for pk_name, cols in pk_dict.items():
            output.append(f"- **{pk_name}**: {', '.join(cols)}")
        output.append("")

    # Foreign Keys
    if foreign_keys:
        output.append("### Foreign Keys")
        output.append("")
        for fk_name, primary_table, primary_key in foreign_keys:
            output.append(f"- **{fk_name}**: → {primary_table}({primary_key})")
        output.append("")

    # Indexes
    if indexes:
        output.append("### Indexes")
        output.append("")
        idx_dict = {}
        for idx_name, unique, col_name, order_val in indexes:
            if idx_name not in idx_dict:
                idx_dict[idx_name] = {"unique": unique, "columns": []}
            idx_dict[idx_name]["columns"].append(f"{col_name} {'ASC' if order_val == 'A' else 'DESC'}")

        for idx_name, idx_info in idx_dict.items():
            unique_str = "Unique " if idx_info["unique"] == "Y" else ""
            cols = ", ".join(idx_info["columns"])
            output.append(f"- **{idx_name}**: ({unique_str}{cols})")
        output.append("")

    return "\n".join(output)


# ============================================================================
# View Formatting
# ============================================================================

def format_view_list_markdown(views: List[tuple], total_count: int) -> str:
    """
    Format view list as Markdown.

    Args:
        views: List of (view_name, owner) tuples
        total_count: Total number of views

    Returns:
        Markdown formatted view list
    """
    output = []
    output.append(f"## Views ({total_count} found)")
    output.append("")
    output.append("| View Name | Owner |")
    output.append("|-----------|-------|")

    for view_name, view_owner in views:
        output.append(f"| {view_name} | {view_owner} |")

    return "\n".join(output)


def format_view_details_markdown(view_name: str, owner: str, columns: List[tuple]) -> str:
    """
    Format view details as Markdown.

    Args:
        view_name: View name
        owner: View owner
        columns: List of column tuples

    Returns:
        Markdown formatted view details
    """
    output = []
    output.append(f"## View: {owner}.{view_name}")
    output.append("")

    if columns:
        output.append(f"### Columns ({len(columns)})")
        output.append("")
        output.append("| Column | Type | Nullable |")
        output.append("|--------|------|----------|")

        for col_name, data_type, nulls in columns:
            nullable = "YES" if nulls == "Y" else "NO"
            output.append(f"| {col_name} | {data_type} | {nullable} |")

    return "\n".join(output)


# ============================================================================
# Procedure Formatting
# ============================================================================

def format_procedure_list_markdown(procedures: List[tuple], total_count: int) -> str:
    """
    Format procedure list as Markdown.

    Args:
        procedures: List of (proc_name, owner) tuples
        total_count: Total number of procedures

    Returns:
        Markdown formatted procedure list
    """
    output = []
    output.append(f"## Procedures & Functions ({total_count} found)")
    output.append("")
    output.append("| Name | Owner |")
    output.append("|------|-------|")

    for proc_name, proc_owner in procedures:
        output.append(f"| {proc_name} | {proc_owner} |")

    return "\n".join(output)


def format_procedure_details_markdown(procedure_name: str, owner: str, parameters: List[tuple]) -> str:
    """
    Format procedure details as Markdown.

    Args:
        procedure_name: Procedure name
        owner: Procedure owner
        parameters: List of parameter tuples

    Returns:
        Markdown formatted procedure details
    """
    output = []
    output.append(f"## Procedure: {owner}.{procedure_name}")
    output.append("")

    if parameters:
        output.append("### Parameters")
        output.append("")
        output.append("| Name | Type | Mode |")
        output.append("|------|------|------|")

        for parm_name, data_type, mode_in, mode_out in parameters:
            if mode_in == 'Y' and mode_out == 'Y':
                mode = 'INOUT'
            elif mode_out == 'Y':
                mode = 'OUT'
            else:
                mode = 'IN'
            output.append(f"| {parm_name} | {data_type} | {mode} |")

        output.append("")
    else:
        output.append("### Parameters")
        output.append("")
        output.append("No parameters found")
        output.append("")

    return "\n".join(output)


# ============================================================================
# Index Formatting
# ============================================================================

def format_index_list_markdown(indexes: List[tuple], total_count: int) -> str:
    """
    Format index list as Markdown.

    Args:
        indexes: List of (idx_name, table_name, unique, owner) tuples
        total_count: Total number of indexes

    Returns:
        Markdown formatted index list
    """
    output = []
    output.append(f"## Indexes ({total_count} found)")
    output.append("")
    output.append("| Index Name | Table | Owner | Unique |")
    output.append("|------------|-------|-------|--------|")

    for idx_name, tbl_name, unique, owner in indexes:
        unique_str = "Yes" if unique == "Y" else "No"
        output.append(f"| {idx_name} | {tbl_name} | {owner} | {unique_str} |")

    return "\n".join(output)


def format_index_details_markdown(
    index_name: str,
    table_name: str,
    owner: str,
    is_unique: bool,
    columns: List[tuple]
) -> str:
    """
    Format index details as Markdown.

    Args:
        index_name: Index name
        table_name: Table name
        owner: Table owner
        is_unique: Whether index is unique
        columns: List of (col_name, order, sequence) tuples

    Returns:
        Markdown formatted index details
    """
    output = []
    output.append(f"## Index: {index_name}")
    output.append(f"**Table**: {owner}.{table_name}")
    output.append(f"**Unique**: {'Yes' if is_unique else 'No'}")
    output.append("")

    if columns:
        output.append("### Columns")
        output.append("")
        output.append("| Column | Order | Sequence |")
        output.append("|--------|-------|----------|")

        for col_name, order_val, seq in columns:
            order_str = "ASC" if order_val == "A" else "DESC"
            output.append(f"| {col_name} | {order_str} | {seq} |")

    return "\n".join(output)


# ============================================================================
# Database Info Formatting
# ============================================================================

def format_database_info_markdown(
    db_name: str,
    db_version: str,
    server_name: str,
    charset: str,
    collation: str,
    page_size: int,
    table_count: int,
    view_count: int,
    proc_count: int
) -> str:
    """
    Format database information as Markdown.

    Args:
        db_name: Database name
        db_version: SQL Anywhere version
        server_name: Server name
        charset: Character set
        collation: Collation
        page_size: Page size
        table_count: Number of tables
        view_count: Number of views
        proc_count: Number of procedures

    Returns:
        Markdown formatted database info
    """
    output = []
    output.append("## Database Information")
    output.append("")
    output.append(f"**Database Name**: {db_name}")
    output.append(f"**SQL Anywhere Version**: {db_version}")
    output.append("")
    output.append("### Connection Information")
    output.append("")
    output.append(f"**Server Name**: {server_name}")
    output.append("")
    output.append("### Database Properties")
    output.append("")
    output.append(f"**Character Set**: {charset}")
    output.append(f"**Collation**: {collation}")
    output.append(f"**Page Size**: {page_size} bytes")
    output.append("")
    output.append("### Database Objects")
    output.append("")
    output.append(f"- **Tables** (authorized): {table_count:,}")
    output.append(f"- **Views** (authorized): {view_count:,}")
    output.append(f"- **Procedures/Functions**: {proc_count:,}")

    return "\n".join(output)


# ============================================================================
# Query Results Formatting
# ============================================================================

def format_query_results_markdown(
    rows: List[Dict[str, Any]],
    row_count: int,
    execution_time: float,
    has_more: bool,
    limit: Optional[int] = None
) -> str:
    """
    Format query results as Markdown.

    Args:
        rows: Query result rows
        row_count: Number of rows returned
        execution_time: Query execution time in seconds
        has_more: Whether more rows exist
        limit: Optional limit that was applied

    Returns:
        Markdown formatted query results
    """
    if not rows:
        return f"## Query Results\n\nNo rows returned.\n\n**Execution time**: {execution_time:.3f} seconds"

    output = []
    output.append("## Query Results")
    output.append("")
    output.append(f"**Rows returned**: {row_count:,}")
    output.append(f"**Execution time**: {execution_time:.3f} seconds")

    if has_more and limit:
        output.append(f"**⚠️ Note**: Result set truncated at {limit} rows (more rows exist)")

    output.append("")

    # Get column names from first row
    columns = list(rows[0].keys())

    # Create table header
    output.append("| " + " | ".join(columns) + " |")
    output.append("| " + " | ".join(["---"] * len(columns)) + " |")

    # Add rows
    for row in rows:
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
