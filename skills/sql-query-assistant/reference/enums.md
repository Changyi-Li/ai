# Enum Mappings

In the database, several columns use integer values to represent specific business states or types. Use these maps to interpret data or write precise `WHERE` clauses.

## Monitor Schema

### Part Table (`monitor.Part`)

**Column**: `Type`

| Integer Value | Enum Name    | Description                                                                   |
| :------------ | :----------- | :---------------------------------------------------------------------------- |
| 0             | Purchased    | For parts bought from vendors. Supports net requirement or physical planning. |
| 1             | Manufactured | For parts produced in-house. Supports net requirement or physical planning.   |
| 2             | Fictitious   | Non-physical parts (kits, modules). No stock updates or transaction logs.     |
| 5             | Service      | For services (freight, alloy costs, labor) handled as parts.                  |
| 6             | Subcontract  | Automatically created for subcontracting operations in the BOM/routing.       |
