"""Schema discovery tools for SQL Anywhere database."""

import pyodbc
from typing import Optional, List
from mcp import Tool
from sqlanywhere_mcp.models import (
    TableInfo,
    ColumnInfo,
    PrimaryKeyInfo,
    ForeignKeyInfo,
    IndexInfo,
    IndexColumn,
    CheckConstraint,
    ViewInfo,
    ProcedureInfo,
    ProcedureParameter,
    DatabaseInfo,
)
from sqlanywhere_mcp.db import get_connection_manager
from sqlanywhere_mcp.errors import DatabaseNotFoundError


def list_tables(owner: Optional[str] = None, limit: int = 100) -> str:
    """
    List all tables in the database.

    Uses modern SQL Anywhere system views (SYS.SYSTAB) with security filtering.

    Args:
        owner: Filter by schema/owner (optional)
        limit: Maximum number of tables to return

    Returns:
        Markdown formatted table list
    """
    cm = get_connection_manager()
    conn = cm.connect()
    cursor = conn.cursor()

    try:
        # Build the authorized users filter
        authorized_users = cm._authorized_users
        users_filter = ",".join(["?" for _ in authorized_users])

        # Query SYS.SYSTAB system view for table information
        # SECURITY: Only expose tables created by authorized users
        if owner:
            query = f"""
                SELECT t.table_name, u.user_name AS owner_name, t.table_type_str, t.count
                FROM SYS.SYSTAB t
                JOIN SYS.SYSUSER u ON t.creator = u.user_id
                WHERE u.user_name = ?
                  AND t.table_type_str = 'BASE'
                  AND u.user_name IN ({users_filter})
                ORDER BY t.table_name
            """
            params = [owner] + authorized_users
            cursor.execute(query, params)
        else:
            query = f"""
                SELECT t.table_name, u.user_name AS owner_name, t.table_type_str, t.count
                FROM SYS.SYSTAB t
                JOIN SYS.SYSUSER u ON t.creator = u.user_id
                WHERE t.table_type_str = 'BASE'
                  AND u.user_name IN ({users_filter})
                ORDER BY t.table_name
            """
            cursor.execute(query, authorized_users)

        tables = cursor.fetchmany(limit)

        # Format output
        output = []
        output.append(f"## Tables ({len(tables)} found)")
        output.append("")
        output.append("| Table Name | Owner | Type | Row Count |")
        output.append("|------------|-------|------|-----------|")

        for table_name, table_owner, table_type, row_count in tables:
            row_count_str = f"{row_count:,}" if row_count else "N/A"
            output.append(f"| {table_name} | {table_owner} | {table_type} | {row_count_str} |")

        return "\n".join(output)

    finally:
        cursor.close()


def get_table_details(table_name: str) -> str:
    """
    Get comprehensive metadata for a specific table.

    Uses modern SQL Anywhere system views with security filtering.

    Args:
        table_name: Name of the table

    Returns:
        Markdown formatted table details
    """
    cm = get_connection_manager()
    conn = cm.connect()
    cursor = conn.cursor()

    try:
        # Get table basic info with security filter
        authorized_users = cm._authorized_users
        users_filter = ",".join(["?" for _ in authorized_users])

        cursor.execute(
            f"""
            SELECT t.table_name, u.user_name AS owner_name, t.table_type_str, t.count
            FROM SYS.SYSTAB t
            JOIN SYS.SYSUSER u ON t.creator = u.user_id
            WHERE t.table_name = ?
              AND u.user_name IN ({users_filter})
            """,
            [table_name] + authorized_users,
        )
        table_info = cursor.fetchone()

        if not table_info:
            raise DatabaseNotFoundError("table", table_name)

        output = []
        output.append(f"## Table: {table_info[1]}.{table_info[0]}")
        output.append(f"**Type**: {table_info[2]}")
        output.append(f"**Row Count**: {table_info[3]:,}" if table_info[3] else "**Row Count**: N/A")
        output.append("")

        # Get columns using SYS.SYSTABCOL with security filter
        cursor.execute(
            f"""
            SELECT
                sc.column_name,
                d.domain_name AS data_type,
                sc.width,
                sc.scale,
                sc.nulls,
                sc."default" AS default_value
            FROM SYS.SYSTABCOL sc
            JOIN SYS.SYSDOMAIN d ON sc.domain_id = d.domain_id
            JOIN SYS.SYSTAB t ON sc.table_id = t.table_id
            JOIN SYS.SYSUSER u ON t.creator = u.user_id
            WHERE t.table_name = ?
              AND u.user_name IN ({users_filter})
            ORDER BY sc.column_id
            """,
            [table_name] + authorized_users,
        )

        columns = cursor.fetchall()
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

        # Get primary keys using SYS.SYSIDX (index_category = 1)
        cursor.execute(
            f"""
            SELECT i.index_name, stc.column_name
            FROM SYS.SYSIDX i
            JOIN SYS.SYSIDXCOL ic ON i.index_id = ic.index_id AND i.table_id = ic.table_id
            JOIN SYS.SYSTABCOL stc ON ic.table_id = stc.table_id AND ic.column_id = stc.column_id
            JOIN SYS.SYSTAB t ON i.table_id = t.table_id
            JOIN SYS.SYSUSER u ON t.creator = u.user_id
            WHERE t.table_name = ?
              AND i.index_category = 1
              AND u.user_name IN ({users_filter})
            ORDER BY i.index_name, ic.sequence
            """,
            [table_name] + authorized_users,
        )

        pkeys = cursor.fetchall()
        if pkeys:
            output.append("### Primary Keys")
            output.append("")
            # Group by index name
            pk_dict = {}
            for pk_name, col_name in pkeys:
                if pk_name not in pk_dict:
                    pk_dict[pk_name] = []
                pk_dict[pk_name].append(col_name)

            for pk_name, cols in pk_dict.items():
                output.append(f"- **{pk_name}**: {', '.join(cols)}")
            output.append("")

        # Get foreign keys using SYS.SYSFKEY
        cursor.execute(
            f"""
            SELECT
                fi.index_name AS foreign_key_name,
                pt.table_name AS primary_table_name,
                pi.index_name AS primary_key_name
            FROM SYS.SYSFKEY fk
            JOIN SYS.SYSTAB ft ON fk.foreign_table_id = ft.table_id
            JOIN SYS.SYSTAB pt ON fk.primary_table_id = pt.table_id
            JOIN SYS.SYSIDX fi ON fk.foreign_index_id = fi.index_id AND fk.foreign_table_id = fi.table_id
            JOIN SYS.SYSIDX pi ON fk.primary_index_id = pi.index_id AND fk.primary_table_id = pi.table_id
            JOIN SYS.SYSUSER u ON ft.creator = u.user_id
            WHERE ft.table_name = ?
              AND u.user_name IN ({users_filter})
            ORDER BY fi.index_name
            """,
            [table_name] + authorized_users,
        )

        fkeys = cursor.fetchall()
        if fkeys:
            output.append("### Foreign Keys")
            output.append("")
            for fk_name, primary_table, primary_key in fkeys:
                output.append(f"- **{fk_name}**: → {primary_table}({primary_key})")
            output.append("")

        # Get indexes using SYS.SYSIDX
        cursor.execute(
            f"""
            SELECT i.index_name, i."unique", stc.column_name, ic."order"
            FROM SYS.SYSIDX i
            JOIN SYS.SYSIDXCOL ic ON i.index_id = ic.index_id AND i.table_id = ic.table_id
            JOIN SYS.SYSTABCOL stc ON ic.table_id = stc.table_id AND ic.column_id = stc.column_id
            JOIN SYS.SYSTAB t ON i.table_id = t.table_id
            JOIN SYS.SYSUSER u ON t.creator = u.user_id
            WHERE t.table_name = ?
              AND u.user_name IN ({users_filter})
            ORDER BY i.index_name, ic.sequence
            """,
            [table_name] + authorized_users,
        )

        indexes = cursor.fetchall()
        if indexes:
            output.append("### Indexes")
            output.append("")
            # Group by index name
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

    finally:
        cursor.close()


def list_views(owner: Optional[str] = None, limit: int = 100) -> str:
    """
    List all views in the database.

    Uses modern SQL Anywhere system views (SYS.SYSTAB) with security filtering.

    Args:
        owner: Filter by schema/owner (optional)
        limit: Maximum number of views to return

    Returns:
        Markdown formatted view list
    """
    cm = get_connection_manager()
    conn = cm.connect()
    cursor = conn.cursor()

    try:
        # Build the authorized users filter
        authorized_users = cm._authorized_users
        users_filter = ",".join(["?" for _ in authorized_users])

        # Query SYS.SYSTAB for views (table_type = 21 = View)
        # SECURITY: Only expose views created by authorized users
        if owner:
            query = f"""
                SELECT t.table_name AS view_name, u.user_name AS owner_name
                FROM SYS.SYSTAB t
                JOIN SYS.SYSUSER u ON t.creator = u.user_id
                WHERE u.user_name = ?
                  AND t.table_type_str = 'VIEW'
                  AND u.user_name IN ({users_filter})
                ORDER BY t.table_name
            """
            cursor.execute(query, [owner] + authorized_users)
        else:
            query = f"""
                SELECT t.table_name AS view_name, u.user_name AS owner_name
                FROM SYS.SYSTAB t
                JOIN SYS.SYSUSER u ON t.creator = u.user_id
                WHERE t.table_type_str = 'VIEW'
                  AND u.user_name IN ({users_filter})
                ORDER BY t.table_name
            """
            cursor.execute(query, authorized_users)

        views = cursor.fetchmany(limit)

        output = []
        output.append(f"## Views ({len(views)} found)")
        output.append("")
        output.append("| View Name | Owner |")
        output.append("|-----------|-------|")

        for view_name, view_owner in views:
            output.append(f"| {view_name} | {view_owner} |")

        return "\n".join(output)

    finally:
        cursor.close()


def get_view_details(view_name: str) -> str:
    """
    Get detailed information about a specific view.

    Args:
        view_name: Name of the view

    Returns:
        Markdown formatted view details
    """
    cm = get_connection_manager()
    conn = cm.connect()
    cursor = conn.cursor()

    try:
        authorized_users = cm._authorized_users
        users_filter = ",".join(["?" for _ in authorized_users])

        query = f"""
            SELECT t.table_name, u.user_name AS owner_name
            FROM SYS.SYSTAB t
            JOIN SYS.SYSUSER u ON t.creator = u.user_id
            WHERE t.table_name = ?
              AND t.table_type_str = 'VIEW'
              AND u.user_name IN ({users_filter})
        """

        cursor.execute(query, [view_name] + authorized_users)
        view_info = cursor.fetchone()

        if not view_info:
            raise DatabaseNotFoundError("view", view_name)

        output = []
        output.append(f"## View: {view_info[1]}.{view_info[0]}")
        output.append("")

        # Get columns using SYS.SYSTABCOL with SYS.SYSDOMAIN
        col_query = f"""
            SELECT sc.column_name, d.domain_name AS data_type, sc.nulls
            FROM SYS.SYSTABCOL sc
            JOIN SYS.SYSDOMAIN d ON sc.domain_id = d.domain_id
            JOIN SYS.SYSTAB t ON sc.table_id = t.table_id
            JOIN SYS.SYSUSER u ON t.creator = u.user_id
            WHERE t.table_name = ?
              AND t.table_type_str = 'VIEW'
              AND u.user_name IN ({users_filter})
            ORDER BY sc.column_id
        """

        cursor.execute(col_query, [view_name] + authorized_users)
        columns = cursor.fetchall()

        if columns:
            output.append(f"### Columns ({len(columns)})")
            output.append("")
            output.append("| Column | Type | Nullable |")
            output.append("|--------|------|----------|")

            for col_name, data_type, nulls in columns:
                nullable = "YES" if nulls == "Y" else "NO"
                output.append(f"| {col_name} | {data_type} | {nullable} |")

        return "\n".join(output)

    finally:
        cursor.close()


def list_procedures(owner: Optional[str] = None, limit: int = 100) -> str:
    """
    List all stored procedures and functions.

    Args:
        owner: Filter by schema/owner (optional)
        limit: Maximum number of procedures to return

    Returns:
        Markdown formatted procedure list
    """
    cm = get_connection_manager()
    conn = cm.connect()
    cursor = conn.cursor()

    try:
        authorized_users = cm._authorized_users
        users_filter = ",".join(["?" for _ in authorized_users])

        # Build WHERE clause first
        where_clause = f"WHERE u.user_name IN ({users_filter})"
        params = authorized_users

        if owner:
            where_clause += " AND u.user_name = ?"
            params = authorized_users + [owner]

        query = f"""
            SELECT TOP {limit} p.proc_name, u.user_name AS owner_name
            FROM SYS.SYSPROCEDURE p
            JOIN SYS.SYSUSER u ON p.creator = u.user_id
            {where_clause}
            ORDER BY p.proc_name
        """

        cursor.execute(query, params)
        procedures = cursor.fetchall()

        output = []
        output.append(f"## Procedures & Functions ({len(procedures)} found)")
        output.append("")
        output.append("| Name | Owner |")
        output.append("|------|-------|")

        for proc_name, proc_owner in procedures:
            output.append(f"| {proc_name} | {proc_owner} |")

        return "\n".join(output)

    finally:
        cursor.close()


def get_procedure_details(procedure_name: str) -> str:
    """
    Get detailed information about a specific procedure.

    Args:
        procedure_name: Name of the procedure

    Returns:
        Markdown formatted procedure details
    """
    cm = get_connection_manager()
    conn = cm.connect()
    cursor = conn.cursor()

    try:
        authorized_users = cm._authorized_users
        users_filter = ",".join(["?" for _ in authorized_users])

        query = f"""
            SELECT p.proc_name, u.user_name AS owner_name
            FROM SYS.SYSPROCEDURE p
            JOIN SYS.SYSUSER u ON p.creator = u.user_id
            WHERE p.proc_name = ?
              AND u.user_name IN ({users_filter})
        """

        cursor.execute(query, [procedure_name] + authorized_users)
        proc_info = cursor.fetchone()

        if not proc_info:
            raise DatabaseNotFoundError("procedure", procedure_name)

        output = []
        output.append(f"## Procedure: {proc_info[1]}.{proc_info[0]}")
        output.append("")

        # Get parameters using SYS.SYSPROCPARM with SYS.SYSDOMAIN for data types
        param_query = f"""
            SELECT
                pp.parm_name,
                d.domain_name AS data_type,
                pp.parm_mode_in,
                pp.parm_mode_out
            FROM SYS.SYSPROCPARM pp
            JOIN SYS.SYSDOMAIN d ON pp.domain_id = d.domain_id
            JOIN SYS.SYSPROCEDURE p ON pp.proc_id = p.proc_id
            JOIN SYS.SYSUSER u ON p.creator = u.user_id
            WHERE p.proc_name = ?
              AND u.user_name IN ({users_filter})
              AND pp.parm_type = 0
            ORDER BY pp.parm_id
        """

        cursor.execute(param_query, [procedure_name] + authorized_users)
        params = cursor.fetchall()

        if params:
            output.append("### Parameters")
            output.append("")
            output.append("| Name | Type | Mode |")
            output.append("|------|------|------|")

            for parm_name, data_type, mode_in, mode_out in params:
                # Determine parameter mode
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

    finally:
        cursor.close()


def list_indexes(table_name: Optional[str] = None, limit: int = 100) -> str:
    """
    List all indexes in the database.

    Args:
        table_name: Filter by specific table (optional)
        limit: Maximum number of indexes to return

    Returns:
        Markdown formatted index list
    """
    cm = get_connection_manager()
    conn = cm.connect()
    cursor = conn.cursor()

    try:
        authorized_users = cm._authorized_users
        users_filter = ",".join(["?" for _ in authorized_users])

        # Build WHERE clause first
        where_clause = f"WHERE u.user_name IN ({users_filter})"
        params = authorized_users

        if table_name:
            where_clause += " AND t.table_name = ?"
            params = authorized_users + [table_name]

        query = f"""
            SELECT TOP {limit} i.index_name, t.table_name, i."unique", u.user_name AS owner_name
            FROM SYS.SYSIDX i
            JOIN SYS.SYSTAB t ON i.table_id = t.table_id
            JOIN SYS.SYSUSER u ON t.creator = u.user_id
            {where_clause}
            ORDER BY t.table_name, i.index_name
        """

        cursor.execute(query, params)
        indexes = cursor.fetchall()

        output = []
        output.append(f"## Indexes ({len(indexes)} found)")
        output.append("")
        output.append("| Index Name | Table | Owner | Unique |")
        output.append("|------------|-------|-------|--------|")

        for idx_name, tbl_name, unique, owner in indexes:
            unique_str = "Yes" if unique == "Y" else "No"
            output.append(f"| {idx_name} | {tbl_name} | {owner} | {unique_str} |")

        return "\n".join(output)

    finally:
        cursor.close()


def get_index_details(index_name: str) -> str:
    """
    Get detailed information about a specific index.

    Args:
        index_name: Name of the index

    Returns:
        Markdown formatted index details
    """
    cm = get_connection_manager()
    conn = cm.connect()
    cursor = conn.cursor()

    try:
        authorized_users = cm._authorized_users
        users_filter = ",".join(["?" for _ in authorized_users])

        query = f"""
            SELECT i.index_name, i."unique", t.table_name, u.user_name AS owner_name
            FROM SYS.SYSIDX i
            JOIN SYS.SYSTAB t ON i.table_id = t.table_id
            JOIN SYS.SYSUSER u ON t.creator = u.user_id
            WHERE i.index_name = ?
              AND u.user_name IN ({users_filter})
        """

        cursor.execute(query, [index_name] + authorized_users)
        index_info = cursor.fetchone()

        if not index_info:
            raise DatabaseNotFoundError("index", index_name)

        output = []
        output.append(f"## Index: {index_info[0]}")
        output.append(f"**Table**: {index_info[3]}.{index_info[2]}")
        output.append(f"**Unique**: {'Yes' if index_info[1] == 'Y' else 'No'}")
        output.append("")

        # Get index columns using SYS.SYSIDXCOL
        col_query = f"""
            SELECT stc.column_name, ic."order", ic.sequence
            FROM SYS.SYSIDXCOL ic
            JOIN SYS.SYSIDX i ON ic.table_id = i.table_id AND ic.index_id = i.index_id
            JOIN SYS.SYSTABCOL stc ON ic.table_id = stc.table_id AND ic.column_id = stc.column_id
            JOIN SYS.SYSTAB t ON i.table_id = t.table_id
            JOIN SYS.SYSUSER u ON t.creator = u.user_id
            WHERE i.index_name = ?
              AND u.user_name IN ({users_filter})
            ORDER BY ic.sequence
        """

        cursor.execute(col_query, [index_name] + authorized_users)
        columns = cursor.fetchall()

        if columns:
            output.append("### Columns")
            output.append("")
            output.append("| Column | Order | Sequence |")
            output.append("|--------|-------|----------|")

            for col_name, order_val, seq in columns:
                order_str = "ASC" if order_val == "A" else "DESC"
                output.append(f"| {col_name} | {order_str} | {seq} |")

        return "\n".join(output)

    finally:
        cursor.close()


def get_database_info() -> str:
    """
    Get database metadata and connection information.

    Returns:
        Markdown formatted database information
    """
    cm = get_connection_manager()
    conn = cm.connect()
    cursor = conn.cursor()

    try:
        output = []
        output.append("## Database Information")
        output.append("")

        # Get database property
        cursor.execute("SELECT PROPERTY('Name'), PROPERTY('ProductVersion')")
        db_info = cursor.fetchone()
        output.append(f"**Database Name**: {db_info[0]}")
        output.append(f"**SQL Anywhere Version**: {db_info[1]}")
        output.append("")

        # Get connection info
        output.append("### Connection Information")
        output.append("")
        output.append(f"**Server Name**: {conn.getinfo(pyodbc.SQL_SERVER_NAME)}")
        output.append(f"**Database Name**: {conn.getinfo(pyodbc.SQL_DATABASE_NAME)}")
        output.append(f"**DBMS Name**: {conn.getinfo(pyodbc.SQL_DBMS_NAME)}")
        output.append(f"**DBMS Version**: {conn.getinfo(pyodbc.SQL_DBMS_VER)}")
        output.append("")

        # Get database properties
        cursor.execute("""
            SELECT
                PROPERTY('Charset'),
                PROPERTY('Collation'),
                PROPERTY('PageSize')
        """)

        props = cursor.fetchone()
        output.append("### Database Properties")
        output.append("")
        output.append(f"**Character Set**: {props[0]}")
        output.append(f"**Collation**: {props[1]}")
        output.append(f"**Page Size**: {props[2]} bytes")
        output.append("")

        # Count tables (filtered by authorized users)
        authorized_users = cm._authorized_users
        users_filter = ",".join(["?" for _ in authorized_users])

        cursor.execute(f"""
            SELECT COUNT(*)
            FROM SYS.SYSTAB t
            JOIN SYS.SYSUSER u ON t.creator = u.user_id
            WHERE t.table_type_str = 'BASE'
              AND u.user_name IN ({users_filter})
        """, authorized_users)
        table_count = cursor.fetchone()[0]

        # Count views (filtered by authorized users)
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM SYS.SYSTAB t
            JOIN SYS.SYSUSER u ON t.creator = u.user_id
            WHERE t.table_type_str = 'VIEW'
              AND u.user_name IN ({users_filter})
        """, authorized_users)
        view_count = cursor.fetchone()[0]

        # Count procedures (filtered by authorized users)
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM SYS.SYSPROCEDURE p
            JOIN SYS.SYSUSER u ON p.creator = u.user_id
            WHERE u.user_name IN ({users_filter})
        """, authorized_users)
        proc_count = cursor.fetchone()[0]

        output.append("### Database Objects")
        output.append("")
        output.append(f"- **Tables** (authorized): {table_count:,}")
        output.append(f"- **Views** (authorized): {view_count:,}")
        output.append(f"- **Procedures/Functions**: {proc_count:,}")

        return "\n".join(output)

    finally:
        cursor.close()
