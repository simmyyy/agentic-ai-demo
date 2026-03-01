# Agentic AI Demo

Bank monitoring demo: **App Runner** services + **DynamoDB** + **Bedrock Agent** with Lambda tools.

## Overview

| Component | Description |
|-----------|-------------|
| **Services** | `account-service`, `payments-service` – FastAPI on App Runner, write alerts to DynamoDB |
| **DynamoDB** | `AlertAggregates` – stores alerts (pk, sk, service, warning_type, host, timestamp) |
| **Agent** | AWS Bedrock Agent – conversational assistant for monitoring |
| **Tools** | Lambda: GetAlertSummary, GetBankServicesStatus, SaveAlertState, GetActionableAlerts, MarkAlertActionable, ResumeAppRunnerService, SaveAction, GetActions, GetIncidents |

## Agent Workflow

1. **Get alert summary** – GetAlertSummary → SaveAlertState (tracks first_seen, last_seen).
2. **Which alerts are actionable** – GetActionableAlerts (per-type status). User can "mark as actionable" / "mark as non-actionable" → MarkAlertActionable.
3. **Check bank services** – GetBankServicesStatus (Health API + App Runner merged). Before resume, GetActions for past context.
4. **Resume service** – User confirms → ResumeAppRunnerService → SaveAction (logs action).
5. **Past actions/incidents** – GetActions, GetIncidents (read-only).

## Demo Prompts

Use these prompts during the demo:

1. **Show me alerts summary for last 24 hours**
2. **Are there any actionable alerts?**
3. **How are the banking services today?**
4. **Check again banking services**
5. **Yes, please, resume the service**

## Setup (summary)

- **ECR**: `agentic-demo/account-service`, `agentic-demo/payments-service`
- **DynamoDB**: `AlertAggregates`, `AlertState`, `Incidents` (pk, sk) in `us-east-2`
- **App Runner**: Both services, port 8000, Instance role with DynamoDB access
- **Lambda**: Deploy `agent/lambda_full_x86.zip`, set env vars, add DynamoDB + App Runner permissions
- **Bedrock**: Create agent, add action groups from `agent/action_group_bank_1.json` through `action_group_bank_6.json`, paste `agent/agent_instructions.md`

```bash
./scripts/setup-instance-role.sh          # App Runner Instance role
./scripts/setup-tables.sh                 # AlertState, Incidents tables
./scripts/setup-lambda-role.sh <role>     # Lambda permissions
./scripts/push-ecr.sh                     # Build & deploy services
```

See `agent/README.md`, `agent/LAMBDA_SETUP.md`, `agent/DYNAMODB_SCHEMA.md` for details.

## Alert API

| Endpoint | Description |
|----------|-------------|
| `GET /agent/summary?hours=12\|24` | Alert summary |
| `POST /agent/generate-one` | Create one alert |
| `POST /agent/generate-bulk?count=200` | Create up to 200 alerts |
