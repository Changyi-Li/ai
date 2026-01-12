# Measuring Form Template Details with Rows

Retrieves comprehensive Measuring FormTemplate information including selection rows and measuring form template rows with type-specific default values.

## Description

This query joins `FormTemplate`, `FormTemplateSelectionRow`, `FormTemplateRow`, and `Unit` tables to retrieve:

- Measuring form template metadata (id, code, name, control data type, usage type)
- Selection row information (id, name, row index)
- Measuring form template row details (id, type, name, unit, tolerances, set points, mandatory, row index)
- **Type-specific default values**: Uses CASE statement to select from different columns based on `RowType`

## Query

```sql
SELECT
    ft.Id,
    ft.Code,
    ExtensionsUser.CN_GetTranslation(ft.DescriptionId, NULL) AS FormTemplateName,
    ft.ControlDataType,
    CASE ft.ControlDataType
        WHEN 0 THEN 'Maintenance'
        WHEN 1 THEN 'MeasuringData'
        ELSE 'Unknown'
    END AS ControlDataTypeName,
    ft.FormTemplateUsageType,
    ftsr.Id AS SelectionRowId,
    ExtensionsUser.CN_GetTranslation(ftsr.DescriptionId, NULL) AS SelectionRowName,
    ftsr.RowIndex AS SelectionRowIndex,
    ftr.Id AS RowId,
    ftr.Type AS [RowType],
    CASE ftr.Type
        WHEN 0 THEN 'Decimal'
        WHEN 1 THEN 'Text'
        WHEN 2 THEN 'CheckBox'
        WHEN 3 THEN 'Date'
        ELSE 'Unknown'
    END AS RowTypeName,
    ExtensionsUser.CN_GetTranslation(ftr.DescriptionId, NULL) AS RowName,
    ExtensionsUser.CN_GetTranslation(u.CodeId, NULL) AS RowUnitCode,
    ftr.MinValue AS RowMinTolerance,
    ftr.MaxValue AS RowMaxTolerance,
    ftr.Value AS RowSetPoint,
    ftr.LowerBoundary AS RowMinSetPoint,
    ftr.UpperBoundary AS RowMaxSetPoint,
    ftr.Mandatory AS RowMandatory,
    ftr.RowIndex AS RowIndex,
    CASE
        WHEN ftr.Type = 0 THEN CAST(ftr.Number AS nvarchar)        -- Decimal
        WHEN ftr.Type = 1 THEN ftr.TextValue                       -- Text
        WHEN ftr.Type = 2 THEN CAST(ftr.Checkbox AS nvarchar)       -- CheckBox
        WHEN ftr.Type = 3 THEN CAST(ftr.DateTimeValue AS nvarchar)   -- Date
        ELSE NULL
    END AS RowDefaultValue
FROM monitor.FormTemplate ft
LEFT JOIN monitor.FormTemplateSelectionRow ftsr ON ft.Id = ftsr.FormTemplateId
LEFT JOIN monitor.FormTemplateRow ftr ON ftsr.Id = ftr.FormTemplateSelectionRowId
LEFT JOIN monitor.Unit u ON ftr.UnitId = u.Id
ORDER BY ft.Code, ftsr.RowIndex, ftr.RowIndex
```

## Column Descriptions

### Measuring FormTemplate Columns

- `Id`: Measuring form template primary key
- `Code`: Template code (unique)
- `FormTemplateName`: Translated template name
- `ControlDataType`: Control data type (Integer).
- `ControlDataTypeName`: Human-readable control data type.
  - Maintenance: Maintenance form template.
  - MeasuringData: Measuring data form template.
- `FormTemplateUsageType`: Usage type bitmask (see enums.md)

### Selection Row Columns

- `SelectionRowId`: Selection row primary key
- `SelectionRowName`: Translated selection row name
- `SelectionRowIndex`: Display order within template

### Measuring Form Template Row Columns

- `RowId`: Row primary key
- `RowType`: Type of row (Integer).
- `RowTypeName`: Human-readable row type.
  - Decimal: Decimal value type.
  - Text: Text value type.
  - CheckBox: CheckBox value type.
  - Date: Date value type.
- `RowName`: Translated row name
- `RowUnitCode`: Unit code if applicable
- `RowMinTolerance`: Minimum tolerance value
- `RowMaxTolerance`: Maximum tolerance value
- `RowSetPoint`: Target/expected value
- `RowMinSetPoint`: Minimum acceptable value
- `RowMaxSetPoint`: Maximum acceptable value
- `RowMandatory`: Whether input is required
- `RowIndex`: Display order within selection row
- `RowDefaultValue`: Type-specific default value (see mapping below)

## Default Value Mapping

The `RowDefaultValue` column uses a CASE statement to select the appropriate source column based on `RowType`:

| RowType | Type Name | Source Column   | Example Output        |
| :------ | :-------- | :-------------- | :-------------------- |
| 0       | Decimal   | `Number`        | "1.00000000"          |
| 1       | Text      | `TextValue`     | NULL or text string   |
| 2       | CheckBox  | `Checkbox`      | "0" or "1"            |
| 3       | Date      | `DateTimeValue` | "2024-01-15 10:30:00" |

## Notes

- Uses `LEFT JOIN` to include measuring form templates even without selection rows
- Uses `LEFT JOIN` to include selection rows even without measuring form template rows
- `ExtensionsUser.CN_GetTranslation()` retrieves translated descriptions; use `NULL` for default language
- Column aliases use `[RowType]` bracket notation to avoid SQL reserved keyword conflicts
- Default values are cast to `nvarchar` for consistent output type across different row types
- CASE statements provide human-readable enum names for `ControlDataType` and `RowType`
