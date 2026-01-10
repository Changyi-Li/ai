# Query: Get Part Details with Unit, Product Group, Traceability, and Inspection

This file documents a comprehensive query for retrieving part details including unit, product group, traceability, and inspection information.

## Description

This query retrieves comprehensive part information including:

- Basic part details (ID, number, name, type, price)
- Default unit (code and name)
- Product group (number and name)
- Traceability settings (mode, best-before date settings)
- Inspection type settings

It demonstrates:

- Joining `Part` -> `PartUnitUsage` -> `Unit` for unit information
- Joining `Part` -> `ProductGroup` for product group
- Using `ExtensionsUser.CN_GetTranslation` function to resolve localized strings
- Using CASE statements to map integer enums to readable names

## SQL Query

```sql
SELECT
    p.Id,
    p.PartNumber,
    p.Description AS PartName,
    p.Type,
    p.StandardPrice,
    ExtensionsUser.CN_GetTranslation(u.CodeId, NULL) AS UnitCode,
    ExtensionsUser.CN_GetTranslation(u.DescriptionId, NULL) AS UnitName,
    pg.Number AS ProductGroupNumber,
    ExtensionsUser.CN_GetTranslation(pg.DescriptionId, NULL) AS ProductGroupName,
    p.TraceabilityMode,
    CASE p.TraceabilityMode
        WHEN 0 THEN 'None'
        WHEN 1 THEN 'Batch'
        WHEN 2 THEN 'Individual'
        WHEN 4 THEN 'IndividualOnlyWithdrawal'
        ELSE 'Unknown'
    END AS TraceabilityModeName,
    p.UseBestBeforeDate,
    p.SuggestBestBeforeDate,
    CASE p.SuggestBestBeforeDate
        WHEN 0 THEN 'No'
        WHEN 1 THEN 'AddDays'
        WHEN 2 THEN 'ShortestFromReportedMaterial'
        ELSE 'Unknown'
    END AS SuggestBestBeforeDateName,
    p.ReceivingInspectionType,
    CASE p.ReceivingInspectionType
        WHEN 0 THEN 'None'
        WHEN 1 THEN 'Always'
        WHEN 2 THEN 'VariableInspection'
        ELSE 'Unknown'
    END AS ReceivingInspectionTypeName
FROM
    monitor.Part p
    LEFT JOIN monitor.PartUnitUsage puu ON p.StandardPartUnitUsageId = puu.Id
    LEFT JOIN monitor.Unit u ON puu.UnitId = u.Id
    LEFT JOIN monitor.ProductGroup pg ON p.ProductGroupId = pg.Id;
```

## Result Columns

### Basic Part Information

- `Id`: Internal Part identifier.
- `PartNumber`: The visible part number.
- `PartName`: Description of part.
- `Type`: The part type (Integer). See `../enums.md` for mapping.
  - 0 = Purchased
  - 1 = Manufactured
  - 2 = Fictitious
  - 5 = Service
  - 6 = Subcontract
- `StandardPrice`: The standard cost/price of part.

### Unit Information

- `UnitCode`: The code for the default unit (e.g., "件", "kg").
- `UnitName`: The full name of the default unit (e.g., "单位", "Kilo").

### Product Group Information

- `ProductGroupNumber`: Product group number code.
- `ProductGroupName`: Product group description.

### Traceability Information

- `TraceabilityMode`: Traceability mode (Integer).
- `TraceabilityModeName`: Human-readable traceability mode.
  - None: No traceability.
  - Batch: Batch number required for all transactions.
  - Individual: Serial number required for all transactions.
  - IndividualOnlyWithdrawal: Serial number required only on withdrawal (purchased parts).
- `UseBestBeforeDate`: Boolean flag indicating if best-before date is used.
- `SuggestBestBeforeDate`: Best-before date suggestion method (Integer).
- `SuggestBestBeforeDateName`: Human-readable suggestion method.
  - No: No date suggested; manual entry required.
  - AddDays: Adds fixed days from settings.
  - ShortestFromReportedMaterial: Uses shortest best-before date from withdrawn material.

### Inspection Information

- `ReceivingInspectionType`: Receiving inspection type (Integer).
- `ReceivingInspectionTypeName`: Human-readable inspection type.
  - None: No receiving inspection.
  - Always: Receiving inspection applied always.
  - VariableInspection: Variable inspection based on settings.

## Join Path

```
Part (p)
├── LEFT JOIN PartUnitUsage (puu) ON p.StandardPartUnitUsageId = puu.Id
│   └── LEFT JOIN Unit (u) ON puu.UnitId = u.Id
└── LEFT JOIN ProductGroup (pg) ON p.ProductGroupId = pg.Id
```

## Notes

- Uses LEFT JOINs to include parts even if they don't have units or product groups assigned.
- The `ExtensionsUser.CN_GetTranslation` function retrieves localized strings from the `monitor.DynamicPhrase` system.
- CASE statements provide human-readable enum names.
