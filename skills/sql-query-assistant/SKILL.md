---
name: sql-query-assistant
description: Assist users in writing, explaining, and optimizing SQL queries for SQL Anywhere databases. Use when the user needs help with SQL syntax, schema exploration, or understanding specific database structures.
---

# SQL Query Assistant

This skill helps you write, explain, and optimize SQL queries for the SQL Anywhere database. It leverages the `sqlanywhere-mcp` to inspect the database schema and provides domain-specific knowledge about business logic (e.g., enum mappings).

## Capabilities

1.  **Schema Inspection**: Use the `sqlanywhere-mcp` tools (e.g., `sqlanywhere_list_tables`, `sqlanywhere_get_table_details`) to understand the database structure.
2.  **Query Construction**: Write efficient SQL Anywhere queries.
3.  **Business Logic Mapping**: Interpret integer flags as meaningful business enums (e.g., `Part.Type`).

## Tools Available

You have access to the **sqlanywhere-mcp** server. Use these tools to explore the schema before writing queries:

- `sqlanywhere_list_tables`: Find table names and metadata.
- `sqlanywhere_get_table_details`: Get column definitions, keys, and constraints for a table.
- `sqlanywhere_list_views`: List all views in the database.
- `sqlanywhere_get_view_details`: Get metadata for a specific view.
- `sqlanywhere_list_procedures`: List stored procedures and functions.
- `sqlanywhere_get_procedure_details`: Get parameters and types for a stored procedure.
- `sqlanywhere_list_indexes`: Find indexes on tables.
- `sqlanywhere_get_index_details`: Get detailed information about an index.
- `sqlanywhere_get_database_info`: Get database version and connection info.
- `sqlanywhere_execute_query`: Run SELECT queries (read-only) to verify results.
- `sqlanywhere_validate_query`: Check query validity without running it.
- `sqlanywhere_connect`: Verify database connection (usually automatic).

## Domain Knowledge

### Enum Mappings

Some columns use integer values to represent business concepts. Always check `reference/enums.md` for mapping definitions.

- **Part.Type**: Maps integer values (0, 1, 2...) to types like Purchased, Manufactured, etc.

### Common Patterns

- **Translations**: Use the function `ExtensionsUser.CN_GetTranslation(@DynamicPhraseId, @LanguageId)` to retrieve translated text.
  - **Purpose**: Get a description from `monitor.DynamicPhrase` or its translation in `monitor.DynamicPhraseTranslation`.
  - **Parameters**:
    - `@DynamicPhraseId` (bigint): References `monitor.DynamicPhrase`.
    - `@LanguageId` (bigint, optional): References `monitor.LanguageCode`. Use `NULL` to retrieve the default text.
  - **Example**: `ExtensionsUser.CN_GetTranslation(Unit.DescriptionId, NULL)` gets the default unit name.

## Quick Start

1.  **Explore**: "Show me the columns in the monitor.Part table."
2.  **Map**: "What does Part.Type = 1 mean?"
3.  **Query**: "Write a query to get parts and their default units."

## References

- [Enum Definitions](reference/enums.md): Integer to Business Enum mappings.
- [Example Queries](reference/examples/): Directory of specific query examples.
  - [Part Details with Units](reference/examples/part-details-with-units.md): Retrieves Part info (Id, Number, Description, Price, Type) with resolved Unit Code/Name.
