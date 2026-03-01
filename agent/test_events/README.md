# Lambda Test Events

Use these JSON files to test the Lambda in the AWS Console.

## How to use

1. Open your Lambda in AWS Console
2. Go to **Test** tab
3. **Create new test event** or **Configure test event**
4. Event name: e.g. `GetAlertSummary`
5. Paste the JSON from the corresponding file
6. **Save** and **Test**

## Test events

| File | Function | Notes |
|------|----------|-------|
| `GetAlertSummary.json` | GetAlertSummary | 24h window |
| `GetAlertSummary_12h.json` | GetAlertSummary | 12h window |
| `GetBankServicesHealth.json` | GetBankServicesHealth | Requires both service URLs |
| `GetAppRunnerServiceStatus.json` | GetAppRunnerServiceStatus | App Runner permissions |
| `ResumeAppRunnerService.json` | ResumeAppRunnerService | **Actually resumes!** |
| `ResumeAppRunnerService_payments.json` | ResumeAppRunnerService | Resumes payments-service |
| `SaveAlertState.json` | SaveAlertState | Requires AlertState table |
| `GetActionableAlerts.json` | GetActionableAlerts | Requires AlertState |
| `SaveAction.json` | SaveAction | Requires AlertState |
| `SaveIncident.json` | SaveIncident | Requires Incidents table |
| `MarkAlertActionable.json` | MarkAlertActionable | Mark timeout as actionable |
| `MarkAlertNonActionable.json` | MarkAlertActionable | Mark timeout as non-actionable |

## Prerequisites

- **Tables**: Run `./scripts/setup-tables.sh` to create AlertState and Incidents
- **Lambda env**: `ALERT_STATE_TABLE`, `INCIDENTS_TABLE` (optional, default names)
- **Permissions**: See `LAMBDA_SETUP.md`
