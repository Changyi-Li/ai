# Enum Mappings

In the database, several columns use integer values to represent specific business states or types. Use these maps to interpret data or write precise `WHERE` clauses.

## Monitor Schema

### FormTemplate Table (`monitor.FormTemplate`)

**Column**: `ControlDataType`

| Integer Value | Enum Name     | Description                   |
| :------------ | :------------ | :---------------------------- |
| 0             | Maintenance   | Maintenance form template.    |
| 1             | MeasuringData | Measuring data form template. |

**Column**: `FormTemplateUsageType` (Bitmask)

| Integer Value | Enum Name     | Description                     |
| :------------ | :------------ | :------------------------------ |
| 0             | None          | Default value.                  |
| 1             | Manufacturing | Form applied for manufacturing. |
| 2             | Purchase      | Form applied for purchase.      |

### FormTemplateRows Table (`monitor.FormTemplateRows`)

**Column**: `Type`

| Integer Value | Enum Name | Description          |
| :------------ | :-------- | :------------------- |
| 0             | Decimal   | Decimal value type.  |
| 1             | Text      | Text value type.     |
| 2             | CheckBox  | CheckBox value type. |
| 3             | Date      | Date value type.     |

### MeasuringTemplate Table (`monitor.MeasuringTemplate`)

**Column**: `Type` (Bitmask)

| Integer Value | Enum Name     | Description                     |
| :------------ | :------------ | :------------------------------ |
| 0             | None          | Default value.                  |
| 1             | Manufacturing | Form applied for manufacturing. |
| 2             | Purchase      | Form applied for purchase.      |

### Part Table (`monitor.Part`)

**Column**: `Type`

| Integer Value | Enum Name    | Description                                    |
| :------------ | :----------- | :--------------------------------------------- |
| 0             | Purchased    | Bought from vendors.                           |
| 1             | Manufactured | Produced in-house.                             |
| 2             | Fictitious   | Non-physical (kits/modules). No stock or logs. |
| 5             | Service      | Services (freight, labor) handled as parts.    |
| 6             | Subcontract  | For subcontracting operations.                 |

**Column**: `TraceabilityMode`

| Integer Value | Enum Name                | Description                                                  |
| :------------ | :----------------------- | :----------------------------------------------------------- |
| 0             | None                     | No traceability.                                             |
| 1             | Batch                    | Batch number required for all transactions.                  |
| 2             | Individual               | Serial number required for all transactions.                 |
| 4             | IndividualOnlyWithdrawal | Serial number required only on withdrawal (purchased parts). |

**Column**: `SuggestBestBeforeDate`

| Integer Value | Enum Name                    | Description                                             |
| :------------ | :--------------------------- | :------------------------------------------------------ |
| 0             | No                           | No date suggested; manual entry required.               |
| 1             | AddDays                      | Adds fixed days from settings.                          |
| 2             | ShortestFromReportedMaterial | Uses shortest best-before date from withdrawn material. |

**Column**: `Status`

| Integer Value | Enum Name   | Description                                             |
| :------------ | :---------- | :------------------------------------------------------ |
| 1             | Quote       | Quote stage; no orders allowed.                         |
| 2             | Prototype   | Prototype stage.                                        |
| 3             | New         | New part.                                               |
| 4             | Normal      | Standard active part.                                   |
| 5             | NewRevision | New revision.                                           |
| 6             | PhasingOut  | Being replaced; affects net requirements.               |
| 9             | Expired     | Obsolete; replacement logic applies.                    |
| 99            | Inactive    | Blocked from all new orders, modifications, and lookup. |

**Column**: `BlockedStatus`

| Integer Value | Enum Name | Description                        |
| :------------ | :-------- | :--------------------------------- |
| 0             | None      | No block or notification.          |
| 1             | Message   | Display notification with message. |
| 2             | Blocked   | Block with cause text.             |

**Column**: `BlockedContextType` (Bitmask)

| Integer Value | Enum Name                    | Description                        |
| :------------ | :--------------------------- | :--------------------------------- |
| 0             | None                         | No context.                        |
| 1             | RegisterManufacturingOrder   | Register manufacturing order.      |
| 2             | RegisterPurchaseOrder        | Register purchase order.           |
| 4             | RegisterCustomerOrder        | Register customer order.           |
| 8             | ReportManufacturingOrder     | Report manufacturing order.        |
| 16            | ReportPurchaseOrder          | Report purchase order.             |
| 32            | ReportCustomerOrder          | Report customer order.             |
| 64            | WithdrawalManufacturingOrder | Withdrawal on manufacturing order. |
| 128           | Preparation                  | Preparation.                       |
| 256           | ConfigurationSelection       | Product configurator selection.    |
| 512           | RegisterAgreement            | Register agreement.                |
| 1024          | RegisterBlanketOrderPurchase | Register blanket purchase order.   |
| 2048          | RegisterBlanketOrderSales    | Register blanket sales order.      |
| 4096          | RegisterQuote                | Register quote.                    |

**Column**: `ReceivingInspectionType`

| Integer Value | Enum Name          | Description                            |
| :------------ | :----------------- | :------------------------------------- |
| 0             | None               | No receiving inspection.               |
| 1             | Always             | Receiving inspection applied always.   |
| 2             | VariableInspection | Variable inspection based on settings. |
