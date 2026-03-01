# Bank Monitoring Agent – AWS Bedrock

AI agent for monitoring bank services (account, payments): alert summary, health check, App Runner status, resuming paused services.

## Structure

```
agent/
├── tools/                    # Lambda tools
│   ├── get_alert_summary.py
│   ├── get_bank_services_health.py
│   ├── get_apprunner_service_status.py
│   └── resume_apprunner_service.py
├── lambda_handler.py
├── build_full.zip.sh         # Build zip (Mac → Linux)
├── action_group_bank_1.json  # GetAlertSummary, GetBankServicesStatus
├── action_group_bank_2.json  # ResumeAppRunnerService (requireConfirmation: ENABLED)
├── agent_instructions.md    # Bedrock Agent instructions
└── requirements.txt
```

## Build Lambda (Mac → Linux)

```bash
cd agent
./build_full.zip.sh amd64
```

Creates `lambda_full_x86.zip` – upload to Lambda (runtime Python 3.12).

## Lambda Permissions

The Lambda execution role needs DynamoDB + App Runner permissions. See **[LAMBDA_SETUP.md](LAMBDA_SETUP.md)** for details.

Quick setup (from repo root):
```bash
# 1. Lambda execution role (DynamoDB + App Runner)
./scripts/setup-lambda-role.sh <your-lambda-role-name>

# 2. Allow Bedrock to invoke Lambda (required!)
aws lambda add-permission --function-name <LAMBDA_NAME> --statement-id bedrock-invoke --action lambda:InvokeFunction --principal bedrock.amazonaws.com
```
Find role name: Lambda → Configuration → Permissions → Execution role.
Find agent ID: Bedrock → Agents → your agent.

## Lambda Configuration

**Environment variables:**
- `ALERT_TABLE_NAME` – DynamoDB table (default: `AlertAggregates`)
- `AWS_REGION` – us-east-2 (default)
- `ACCOUNT_SERVICE_URL`, `PAYMENTS_SERVICE_URL` – for GetBankServicesStatus (health check)

**Lambda IAM role** – permissions:
- `dynamodb:Query`, `dynamodb:GetItem` on `AlertAggregates` (GetAlertSummary)
- `apprunner:ListServices`, `apprunner:DescribeService`, `apprunner:ResumeService`
- (optional) VPC/outbound to App Runner if in VPC

## Bedrock Agent Configuration

1. **Create Agent** in AWS Bedrock (Agents → Create agent).

2. **Action Groups 1–6** – `action_group_bank_1.json` through `action_group_bank_6.json`:
   - Same Lambda for all
   - Import each JSON (max 3 functions per group).

4. **Instructions** – copy the contents of `agent_instructions.md` into the agent's "Instructions" field.

## Action Groups (max 3 functions per group)

| Group | Functions |
|-------|-----------|
| action_group_bank_1 | GetAlertSummary, GetBankServicesStatus |
| action_group_bank_2 | ResumeAppRunnerService (requires confirmation) |
| action_group_bank_3 | SaveAlertState, GetAlertState, GetActionableAlerts |
| action_group_bank_4 | SaveAction, GetActions, GetIncidents |
| action_group_bank_5 | SaveIncident |
| action_group_bank_6 | MarkAlertActionable |
