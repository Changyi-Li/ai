"""Schema discovery tools for SQL Anywhere database."""

import pyodbc
import json
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
    ResponseFormat,
    TableListResponse,
    ViewListResponse,
    ProcedureListResponse,
    IndexListResponse,
)
from sqlanywhere_mcp.db import get_connection_manager
from sqlanywhere_mcp.errors import DatabaseNotFoundError
from sqlanywhere_mcp import formatters


def list_tables(
    owner: Optional[str] = None,
    limit: int = 100,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
    """
    List all tables in the database.

    Uses modern SQL Anywhere system views (SYS.SYSTAB) with security filtering.

    Args:
        owner: Filter by schema/owner (optional)
        limit: Maximum number of tables to return
        response_format: Output format (markdown or json)

    Returns:
        Formatted table list in requested format
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

        # Format output based on response_format
        if response_format == ResponseFormat.JSON:
            # Convert to Pydantic models and return JSON
            table_models = []
            for table_name, table_owner, table_type, row_count in tables:
                table_models.append(
                    TableInfo(
                        name=table_name,
                        owner=table_owner,
                        table_type=table_type,
                        row_count=row_count,
                        columns=[],
                        primary_keys=[],
                        foreign_keys=[],
                        indexes=[],
                        check_constraints=[]
                    )
                )

            response = TableListResponse(
                tables=table_models,
                total_count=len(table_models),
                has_more=False
            )
            return response.model_dump_json(indent=2)
        else:
            # Use formatter for markdown
            return formatters.format_table_list_markdown(tables, len(tables))

    finally:
        cursor.close()


def get_table_details(
    table_name: str,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
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

        # Extract table info
        table_name_result = table_info[0]
        owner_name = table_info[1]
        table_type = table_info[2]
        row_count = table_info[3]

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

        columns_data = cursor.fetchall()

        # Build ColumnInfo models
        column_models = []
        for col in columns_data:
            col_name, domain_id, width, scale, nulls, default_val = col
            column_models.append(
                ColumnInfo(
                    name=col_name,
                    type=domain_id,
                    length=width,
                    scale=scale,
                    nullable=(nulls == "Y"),
                    default_value=default_val,
                    is_primary_key=False  # Will update below
                )
            )

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

        pkeys_data = cursor.fetchall()

        # Build PrimaryKeyInfo models and mark primary key columns
        pk_models = []
        pk_columns = set()
        pk_dict = {}
        for pk_name, col_name in pkeys_data:
            if pk_name not in pk_dict:
                pk_dict[pk_name] = []
            pk_dict[pk_name].append(col_name)
            pk_columns.add(col_name)

        for pk_name, cols in pk_dict.items():
            pk_models.append(
                PrimaryKeyInfo(
                    name=pk_name,
                    column_names=cols
                )
            )

        # Update is_primary_key flag in columns
        for col in column_models:
            if col.name in pk_columns:
                col.is_primary_key = True

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

        fkeys_data = cursor.fetchall()

        # Build ForeignKeyInfo models
        fk_models = []
        for fk_name, primary_table, primary_key in fkeys_data:
            fk_models.append(
                ForeignKeyInfo(
                    name=fk_name,
                    column_names=[],  # Simplified - would need additional query
                    referenced_table=primary_table,
                    referenced_columns=[],  # Simplified
                    on_delete=None,
                    on_update=None
                )
            )

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

        indexes_data = cursor.fetchall()

        # Build IndexInfo models
        idx_models = []
        idx_dict = {}
        for idx_name, unique, col_name, order_val in indexes_data:
            if idx_name not in idx_dict:
                idx_dict[idx_name] = {"unique": unique, "columns": []}
            idx_dict[idx_name]["columns"].append(
                IndexColumn(
                    column_name=col_name,
                    order="ASC" if order_val == "A" else "DESC"
                )
            )

        for idx_name, idx_info in idx_dict.items():
            idx_models.append(
                IndexInfo(
                    name=idx_name,
                    table_name=table_name,
                    is_unique=(idx_info["unique"] == "Y"),
                    is_primary_key=False,  # Would need additional check
                    columns=idx_info["columns"],
                    index_type=None
                )
            )

        # Format output based on response_format
        if response_format == ResponseFormat.JSON:
            # Build complete TableInfo model
            table_model = TableInfo(
                name=table_name_result,
                owner=owner_name,
                table_type=table_type,
                row_count=row_count,
                columns=column_models,
                primary_keys=pk_models,
                foreign_keys=fk_models,
                indexes=idx_models,
                check_constraints=[]  # Not implemented yet
            )
            return table_model.model_dump_json(indent=2)
        else:
            # Use formatter for markdown
            return formatters.format_table_details_markdown(
                table_name=table_name_result,
                owner=owner_name,
                table_type=table_type,
                row_count=row_count,
                columns=columns_data,
                primary_keys=pkeys_data,
                foreign_keys=fkeys_data,
                indexes=indexes_data
            )

    finally:
        cursor.close()


def list_views(
    owner: Optional[str] = None,
    limit: int = 100,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
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

        # Format output based on response_format
        if response_format == ResponseFormat.JSON:
            # Convert to Pydantic models and return JSON
            view_models = []
            for view_name, view_owner in views:
                view_models.append(
                    ViewInfo(
                        name=view_name,
                        owner=view_owner,
                        definition=None
                    )
                )

            response = ViewListResponse(
                views=view_models,
                total_count=len(view_models),
                has_more=False
            )
            return response.model_dump_json(indent=2)
        else:
            # Use formatter for markdown
            return formatters.format_view_list_markdown(views, len(views))

    finally:
        cursor.close()


def get_view_details(
    view_name: str,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
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

        # Extract view info
        view_name_result = view_info[0]
        owner_name = view_info[1]

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
        columns_data = cursor.fetchall()

        # Build ColumnInfo models
        column_models = []
        for col_name, data_type, nulls in columns_data:
            column_models.append(
                ColumnInfo(
                    name=col_name,
                    type=data_type,
                    length=None,
                    scale=None,
                    nullable=(nulls == "Y"),
                    default_value=None,
                    is_primary_key=False
                )
            )

        # Format output based on response_format
        if response_format == ResponseFormat.JSON:
            # Build ViewInfo model with columns
            view_model = ViewInfo(
                name=view_name_result,
                owner=owner_name,
                definition=None,  # Would need additional query
                columns=column_models
            )
            return view_model.model_dump_json(indent=2)
        else:
            # Use formatter for markdown
            return formatters.format_view_details_markdown(
                view_name=view_name_result,
                owner=owner_name,
                columns=columns_data
            )

    finally:
        cursor.close()


def list_procedures(
    owner: Optional[str] = None,
    limit: int = 100,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
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

        # Format output based on response_format
        if response_format == ResponseFormat.JSON:
            # Convert to Pydantic models and return JSON
            proc_models = []
            for proc_name, proc_owner in procedures:
                proc_models.append(
                    ProcedureInfo(
                        name=proc_name,
                        owner=proc_owner,
                        procedure_type="PROCEDURE",  # Simplified
                        parameters=[],
                        return_type=None,
                        definition=None
                    )
                )

            response = ProcedureListResponse(
                procedures=proc_models,
                total_count=len(proc_models),
                has_more=False
            )
            return response.model_dump_json(indent=2)
        else:
            # Use formatter for markdown
            return formatters.format_procedure_list_markdown(procedures, len(procedures))

    finally:
        cursor.close()


def get_procedure_details(
    procedure_name: str,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
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

        # Extract procedure info
        proc_name_result = proc_info[0]
        owner_name = proc_info[1]

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
        params_data = cursor.fetchall()

        # Build ProcedureParameter models
        param_models = []
        for parm_name, data_type, mode_in, mode_out in params_data:
            # Determine parameter mode
            if mode_in == 'Y' and mode_out == 'Y':
                mode = 'INOUT'
            elif mode_out == 'Y':
                mode = 'OUT'
            else:
                mode = 'IN'

            param_models.append(
                ProcedureParameter(
                    name=parm_name,
                    type=data_type,
                    mode=mode
                )
            )

        # Format output based on response_format
        if response_format == ResponseFormat.JSON:
            # Build ProcedureInfo model
            proc_model = ProcedureInfo(
                name=proc_name_result,
                owner=owner_name,
                procedure_type="PROCEDURE",  # Simplified - would need additional query
                parameters=param_models,
                return_type=None,  # Functions only - would need additional query
                definition=None  # Would need additional query
            )
            return proc_model.model_dump_json(indent=2)
        else:
            # Use formatter for markdown
            return formatters.format_procedure_details_markdown(
                procedure_name=proc_name_result,
                owner=owner_name,
                parameters=params_data
            )

    finally:
        cursor.close()


def list_indexes(
    table_name: Optional[str] = None,
    limit: int = 100,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
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

        # Format output based on response_format
        if response_format == ResponseFormat.JSON:
            # Convert to Pydantic models and return JSON
            index_models = []
            for idx_name, tbl_name, unique, owner in indexes:
                index_models.append(
                    IndexInfo(
                        name=idx_name,
                        table_name=tbl_name,
                        is_unique=(unique == "Y"),
                        is_primary_key=False,  # Simplified
                        columns=[],
                        index_type=None
                    )
                )

            response = IndexListResponse(
                indexes=index_models,
                total_count=len(index_models),
                has_more=False
            )
            return response.model_dump_json(indent=2)
        else:
            # Use formatter for markdown
            return formatters.format_index_list_markdown(indexes, len(indexes))

    finally:
        cursor.close()


def get_index_details(
    index_name: str,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
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

        # Extract index info
        index_name_result = index_info[0]
        is_unique = index_info[1]
        table_name_result = index_info[2]
        owner_name = index_info[3]

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
        columns_data = cursor.fetchall()

        # Build IndexColumn models
        column_models = []
        for col_name, order_val, seq in columns_data:
            column_models.append(
                IndexColumn(
                    column_name=col_name,
                    order="ASC" if order_val == "A" else "DESC"
                )
            )

        # Format output based on response_format
        if response_format == ResponseFormat.JSON:
            # Build IndexInfo model
            index_model = IndexInfo(
                name=index_name_result,
                table_name=table_name_result,
                is_unique=(is_unique == "Y"),
                is_primary_key=False,  # Would need additional check
                columns=column_models,
                index_type=None
            )
            return index_model.model_dump_json(indent=2)
        else:
            # Use formatter for markdown
            return formatters.format_index_details_markdown(
                index_name=index_name_result,
                table_name=table_name_result,
                owner=owner_name,
                is_unique=(is_unique == "Y"),
                columns=columns_data
            )

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
