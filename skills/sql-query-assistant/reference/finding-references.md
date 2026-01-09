# Finding Referencing Tables

To find all tables that reference a specific table (e.g., find tables referencing SupplierPartLink):

## Using Index Search

Use `sqlanywhere_list_indexes` with the table name as search parameter to find foreign key relationships:

```bash
# Example: Find all indexes referencing SupplierPartLink
sqlanywhere_list_indexes(search="SupplierPartLink")
```

This returns all indexes with names containing "SupplierPartLink". Analyze the results:

1. **Self-references** (ignore these): Tables named `SupplierPartLink*` that reference themselves
2. **Foreign key indexes**: Look for indexes with patterns like:
   - `bk_OtherTable_SupplierPartLinkId`: Indicates `OtherTable.SupplierPartLinkId` references `SupplierPartLink`
   - `fk_OtherTable_SupplierPartLinkId`: Indicates foreign key constraint

## Workflow

1. **Search indexes**: `sqlanywhere_list_indexes(search="TableName")`
2. **Filter results**: Exclude self-referencing tables (those starting with the search table name)
3. **Examine candidate tables**: Use `sqlanywhere_get_table_details` to confirm the foreign key relationship
