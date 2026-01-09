# Query: Get Part Details with Default Unit Names

This file documents a specific sample query for retrieving part details.

## Description

This query retrieves part information along with its default unit code and name. It demonstrates:

- Joining `Part` -> `PartUnitUsage` -> `Unit`.
- Using the `ExtensionsUser.CN_GetTranslation` function to resolve localized strings.

## SQL Query

```sql
SELECT
    p.Id,
    p.PartNumber,
    p.Description AS PartName,
    ExtensionsUser.CN_GetTranslation(u.CodeId, NULL) AS UnitCode,
    ExtensionsUser.CN_GetTranslation(u.DescriptionId, NULL) AS UnitName,
    p.StandardPrice,
    p.Type
FROM
    monitor.Part p
    INNER JOIN monitor.PartUnitUsage puu ON p.StandardPartUnitUsageId = puu.Id
    INNER JOIN monitor.Unit u ON puu.UnitId = u.Id;
```

## Result Columns

- `Id`: Internal Part identifier.
- `PartNumber`: The visible part number.
- `PartName`: Description of the part.
- `UnitCode`: The code for the default unit (e.g., "PCS", "KG").
- `UnitName`: The full name of the default unit (e.g., "Pieces", "Kilograms").
- `StandardPrice`: The standard cost/price of the part.
- `Type`: The part type (Integer). See `../enums.md` for mapping (e.g., 1 = Manufactured).
