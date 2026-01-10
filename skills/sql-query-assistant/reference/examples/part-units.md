# Query: Get Parts with Their Units

This file documents a query for retrieving parts and all their associated units, including conversion factors.

## Description

This query retrieves parts and their units, including:

- Basic part details (ID, number, name)
- Unit code and name (localized)
- Conversion factor (relation between alternative unit and standard unit)
- Default unit flag
- Filter for non-removed units only

It demonstrates:

- Joining `Part` -> `PartUnitUsage` -> `Unit` for all unit relationships
- Using `ExtensionsUser.CN_GetTranslation` function to resolve localized strings (both unit code and description)
- Filtering by `PartUnitUsage.IsRemoved` to exclude deleted units
- Using LEFT JOIN to include parts even if they have no units

## SQL Query

```sql
SELECT
    p.Id AS PartId,
    p.PartNumber,
    p.Description AS PartName,
    pu.ConversionFactor,
    ExtensionsUser.CN_GetTranslation(u.CodeId, NULL) AS UnitCode,
    ExtensionsUser.CN_GetTranslation(u.DescriptionId, NULL) AS UnitName,
    u.IsDefault AS IsDefaultUnit
FROM monitor.Part p
LEFT JOIN monitor.PartUnitUsage pu ON p.Id = pu.PartId
LEFT JOIN monitor.Unit u ON pu.UnitId = u.Id
WHERE pu.IsRemoved = 0
ORDER BY p.PartNumber;
```

## Result Columns

### Part Information

- `PartId`: Internal Part identifier.
- `PartNumber`: The visible part number.
- `PartName`: Description of part.

### Unit Information

- `ConversionFactor`: Conversion factor showing the relation between alternative unit and standard unit. The factor is entered as "standard unit divided with alternative unit".
- `UnitCode`: The code for the unit (e.g., "件", "kg", "m").
- `UnitName`: The full name of the unit (e.g., "单位", "Kilo", "米").
- `IsDefaultUnit`: Boolean flag indicating if this is the default unit for the part.

## Join Path

```
Part (p)
├── LEFT JOIN PartUnitUsage (pu) ON p.Id = pu.PartId
│   └── LEFT JOIN Unit (u) ON pu.UnitId = u.Id
```

## Filter Notes

- `WHERE pu.IsRemoved = 0` filters out units that have been marked as removed.

## Notes

- Uses LEFT JOINs to include parts even if they don't have units assigned.
- The `ExtensionsUser.CN_GetTranslation` function retrieves localized strings from `monitor.DynamicPhrase` system.
- `u.CodeId` provides the short unit code (abbreviation).
- `u.DescriptionId` provides the full unit name.
