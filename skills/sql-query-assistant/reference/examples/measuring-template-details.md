# Measuring Template with Form Template Details

Retrieves comprehensive MeasuringTemplate information including its associated FormTemplate, selection rows, and template rows with type-specific default values.

## Description

This query starts from `MeasuringTemplate` and joins to `FormTemplate`, `FormTemplateSelectionRow`, `FormTemplateRow`, and `Unit` tables to retrieve:

- Measuring template metadata (id, code, name, frequency, type, intervals)
- Associated form template details (id, code, name, control data type, usage type)
- Selection row information (id, name, row index)
- Template row details (id, type, name, unit, tolerances, set points, mandatory, row index)
- **Type-specific default values**: Uses CASE statement to select from different columns based on `RowType`

## Query

```sql
SELECT
    mt.Id,
    mt.Code,
    ExtensionsUser.CN_GetTranslation(mt.DescriptionId, NULL) AS MeasuringTemplateName,
    mt.MeasuringFrequency,
    mt.Type,
    CASE mt.Type
        WHEN 0 THEN 'None'
        WHEN 1 THEN 'Manufacturing'
        WHEN 2 THEN 'Purchase'
        WHEN 3 THEN 'Manufacturing, Purchase'
        ELSE 'Unknown'
    END AS MeasuringTypeName,
    mt.FrequencyText,
    mt.IntervalAmount,
    mt.Interval,
    ft.Id AS FormTemplateId,
    ft.Code AS FormTemplateCode,
    ExtensionsUser.CN_GetTranslation(ft.DescriptionId, NULL) AS FormTemplateName,
    ft.ControlDataType,
    CASE ft.ControlDataType
        WHEN 0 THEN 'Maintenance'
        WHEN 1 THEN 'MeasuringData'
        ELSE 'Unknown'
    END AS ControlDataTypeName,
    ft.FormTemplateUsageType,
    CASE ft.FormTemplateUsageType
        WHEN 0 THEN 'None'
        WHEN 1 THEN 'Manufacturing'
        WHEN 2 THEN 'Purchase'
        WHEN 3 THEN 'Manufacturing, Purchase'
        ELSE 'Unknown'
    END AS FormTemplateUsageTypeName,
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
    CASE ftr.Type
        WHEN 0 THEN CAST(ftr.Number AS nvarchar)
        WHEN 1 THEN ftr.TextValue
        WHEN 2 THEN CAST(ftr.Checkbox AS nvarchar)
        WHEN 3 THEN CAST(ftr.DateTimeValue AS nvarchar)
        ELSE NULL
    END AS RowDefaultValue
FROM monitor.MeasuringTemplate mt
LEFT JOIN monitor.FormTemplate ft ON mt.FormTemplateId = ft.Id
LEFT JOIN monitor.FormTemplateSelectionRow ftsr ON ft.Id = ftsr.FormTemplateId
LEFT JOIN monitor.FormTemplateRow ftr ON ftsr.Id = ftr.FormTemplateSelectionRowId
LEFT JOIN monitor.Unit u ON ftr.UnitId = u.Id
ORDER BY mt.Code, ft.Code, ftsr.RowIndex, ftr.RowIndex;
```

## Column Descriptions

### Measuring Template Columns

- `Id`: Measuring template primary key
- `Code`: Template code (unique)
- `MeasuringTemplateName`: Translated measuring template name
- `MeasuringFrequency`: Frequency value
- `Type`: Type bitmask (Integer)
- `MeasuringTypeName`: Human-readable type name (decoded bitmask)
  - None: Default value
  - Manufacturing: Form applied for manufacturing
  - Purchase: Form applied for purchase
  - Manufacturing, Purchase: Both manufacturing and purchase (bitmask 1 + 2)
- `FrequencyText`: Frequency description text
- `IntervalAmount`: Interval amount value
- `Interval`: Interval type value

### Form Template Columns

- `FormTemplateId`: Associated form template primary key
- `FormTemplateCode`: Form template code
- `FormTemplateName`: Translated form template name
- `ControlDataType`: Control data type (Integer)
- `ControlDataTypeName`: Human-readable control data type
  - Maintenance: Maintenance form template
  - MeasuringData: Measuring data form template
- `FormTemplateUsageType`: Usage type bitmask (Integer)
- `FormTemplateUsageTypeName`: Human-readable usage type name (decoded bitmask)
  - None: Default value
  - Manufacturing: Form applied for manufacturing
  - Purchase: Form applied for purchase
  - Manufacturing, Purchase: Both manufacturing and purchase (bitmask 1 + 2)

### Selection Row Columns

- `SelectionRowId`: Selection row primary key
- `SelectionRowName`: Translated selection row name
- `SelectionRowIndex`: Display order within template

### Template Row Columns

- `RowId`: Row primary key
- `RowType`: Type of row (Integer)
- `RowTypeName`: Human-readable row type
  - Decimal: Decimal value type
  - Text: Text value type
  - CheckBox: CheckBox value type
  - Date: Date value type
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

## Join Path

```
MeasuringTemplate (mt)
├── LEFT JOIN FormTemplate (ft) ON mt.FormTemplateId = ft.Id
│   └── LEFT JOIN FormTemplateSelectionRow (ftsr) ON ft.Id = ftsr.FormTemplateId
│       └── LEFT JOIN FormTemplateRow (ftr) ON ftsr.Id = ftr.FormTemplateSelectionRowId
│           └── LEFT JOIN Unit (u) ON ftr.UnitId = u.Id
```

## Notes

- Query starts from `MeasuringTemplate` as the primary table
- Uses `LEFT JOIN` to include measuring templates even without form templates
- Uses `LEFT JOIN` to include form templates even without selection rows
- Uses `LEFT JOIN` to include selection rows even without template rows
- `ExtensionsUser.CN_GetTranslation()` retrieves translated descriptions; use `NULL` for default language
- Column aliases use `[RowType]` bracket notation to avoid SQL reserved keyword conflicts
- Default values are cast to `nvarchar` for consistent output type across different row types
- CASE statements provide human-readable enum names for bitmask columns (`MeasuringTemplate.Type`, `FormTemplate.FormTemplateUsageType`)
- Bitmask values: 1 (Manufacturing), 2 (Purchase), 3 (Both = 1 + 2)
