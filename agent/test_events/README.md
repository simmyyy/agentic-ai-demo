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
| `GetAlertSummary.json` | GetAlertSummary | 24h window – requires `ACCOUNT_SERVICE_URL` |
| `GetAlertSummary_12h.json` | GetAlertSummary | 12h window |
| `GetBankServicesHealth.json` | GetBankServicesHealth | Requires both service URLs |
| `GetAppRunnerServiceStatus.json` | GetAppRunnerServiceStatus | Needs `apprunner:ListServices`, `apprunner:DescribeService` |
| `ResumeAppRunnerService.json` | ResumeAppRunnerService | Resumes account-service – **actually resumes!** |
| `ResumeAppRunnerService_payments.json` | ResumeAppRunnerService | Resumes payments-service |

## Prerequisites

- **GetAlertSummary**: Lambda role needs DynamoDB permissions (Query on AlertAggregates). No service URL needed – reads directly from DynamoDB.
- **GetBankServicesHealth**: Set `ACCOUNT_SERVICE_URL` and `PAYMENTS_SERVICE_URL` in Lambda env vars
- **GetAppRunnerServiceStatus**, **ResumeAppRunnerService**: Lambda role needs App Runner permissions (see `LAMBDA_SETUP.md`)
