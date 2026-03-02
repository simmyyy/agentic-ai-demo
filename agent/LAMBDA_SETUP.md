# Lambda Setup – Permissions and Test Events

## 1. Lambda Execution Role – IAM Permissions

The Lambda needs:

- **DynamoDB** – `AlertAggregates` (alerts), `AlertState` (snapshot, actions, context), `Incidents` (incident log)
- **App Runner API** – for `GetAppRunnerServiceStatus` and `ResumeAppRunnerService`
- **Outbound HTTP** – for `GetBankServicesHealth` (calls App Runner URLs)

Create tables first: `./scripts/setup-tables.sh`

### Where to add permissions

1. AWS Console → **IAM** → **Roles**
2. Find the role used by your Lambda (e.g. `bank-agent-lambda-role` or the default `lambda-*` role)
3. **Add permissions** → **Create inline policy** (or attach a managed policy)

### Policy to add

**Policy name:** `BankAgentLambdaPolicy`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:Query",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:BatchGetItem",
        "dynamodb:DescribeTable"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-2:YOUR_ACCOUNT_ID:table/AlertAggregates",
        "arn:aws:dynamodb:us-east-2:YOUR_ACCOUNT_ID:table/AlertState",
        "arn:aws:dynamodb:us-east-2:YOUR_ACCOUNT_ID:table/Incidents"
      ]
    },
    {
      "Sid": "AppRunnerAccess",
      "Effect": "Allow",
      "Action": [
        "apprunner:ListServices",
        "apprunner:DescribeService",
        "apprunner:ResumeService"
      ],
      "Resource": "*"
    }
  ]
}
```

Replace `YOUR_ACCOUNT_ID` with your AWS account ID (or use `*` for the account).

### Summary

| Permission | Used by | Purpose |
|------------|---------|---------|
| `dynamodb:Query` | GetAlertSummary | Query alerts by time range |
| `dynamodb:GetItem`, `BatchGetItem`, `DescribeTable` | GetAlertSummary | Fallback / pagination |
| `apprunner:ListServices` | GetAppRunnerServiceStatus, ResumeAppRunnerService | List services to find ARN |
| `apprunner:DescribeService` | GetAppRunnerServiceStatus | Get RUNNING/PAUSED status |
| `apprunner:ResumeService` | ResumeAppRunnerService | Resume paused service |

---

## 2. Bedrock Invoking Lambda (required)

Bedrock needs permission to invoke your Lambda. Add a **resource-based policy**:

### AWS CLI

```bash
aws lambda add-permission \
  --function-name BankAIAgentTools \
  --statement-id bedrock-invoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com
```

### Lambda Console

1. Lambda → **BankAIAgentTools** → **Configuration** → **Permissions**
2. **Resource-based policy statements** → **Add permissions**
3. Principal: `bedrock.amazonaws.com`
4. Action: `lambda:InvokeFunction`

---

## 3. Lambda Environment Variables

In Lambda → **Configuration** → **Environment variables**:

| Key | Value | Required |
|-----|-------|----------|
| `ALERT_TABLE_NAME` | `AlertAggregates` | No (default) |
| `ALERT_STATE_TABLE` | `AlertState` | No (default) |
| `INCIDENTS_TABLE` | `Incidents` | No (default) |
| `AWS_REGION` | `us-east-2` | No (default) |
| `ACCOUNT_SERVICE_URL` | `https://xxx.us-east-2.awsapprunner.com` | Yes (for GetBankServicesHealth) |
| `PAYMENTS_SERVICE_URL` | `https://yyy.us-east-2.awsapprunner.com` | Yes (for GetBankServicesHealth) |

**Note:** `GetBankServicesStatus` uses App Runner API `service_url` for health checks (not env vars), so no URL mix-up. `GetBankServicesHealth` (legacy) still uses env vars.
