# Grant Field Value Combinations

## Standard Field Types

| Type | Date | Text | Value | selectedValues | possibleValues | Decimal | Implemented |
|------|------|------|-------|----------------|----------------|---------|-------------|
| denmarkStatisticMappingTargetGroup | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| denmarkStatisticRareDisability | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| denmarkStatisticMultipleDisabilityBooleanUnit | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| denmarkStatisticMappingPrimaryTargetGroup | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| denmarkStatisticMappingOtherTargetGroups | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| payor | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| invoiceLines | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| plannedDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| workflowRequestedDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| workflowApprovedDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| orderedDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| entryDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| serviceDelivery | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| billingStartDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| billingEndDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| followUpDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| denmarkStatisticMappingOffer | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| denmarkStatisticMappingDecisive | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| piece | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| price | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | 🔄 |
| utilisation | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | 🔄 |
| billingFactor | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | 🔄 |
| functionalLevel | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| personReference | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| orderReference | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| accountString | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| klMapping | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| denmarkStatisticMapping | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| denmarkStatisticMappingNursingArea | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| denmarkStatisticMappingPreventiveMeasure | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| denmarkStatisticMappingSpecialNeedChildrenGrant | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| supplementaryInformation | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| description | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| rejectedDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| removedDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| cancelledDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| renouncedDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| basketGrantEndDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| orderGrantEndDate | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

## Special Cases

These field types require custom handling due to their complex data structures:

| Type | Date | Text | Value | selectedValues | possibleValues | Decimal | Implemented |
|------|------|------|-------|----------------|----------------|---------|-------------|
| paragraph | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| debtorContact | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| actingMunicipality | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| payingMunicipality | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| repetition | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| financialAccount | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| supplier | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| resourceCount | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| visitatedDurationInMinutes | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| listPrice | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| supplierPrice | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| localPrice | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| staticFinancialAccount | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| kmdSag | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

