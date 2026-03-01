# Agentic AI Demo

Bank monitoring demo: **App Runner** services + **DynamoDB** + **Bedrock Agent** with Lambda tools.

## Overview

| Component | Description |
|-----------|-------------|
| **Services** | `account-service`, `payments-service` – FastAPI on App Runner, write alerts to DynamoDB |
| **DynamoDB** | `AlertAggregates` – stores alerts (pk, sk, service, warning_type, host, timestamp) |
| **Agent** | AWS Bedrock Agent – conversational assistant for monitoring |
| **Tools** | Lambda: GetAlertSummary, GetBankServicesHealth, GetAppRunnerServiceStatus, ResumeAppRunnerService |

## Agent Workflow

1. **Get alert summary** – User asks for alerts → agent calls GetAlertSummary (reads DynamoDB directly) → returns table (total, by service, by type).
2. **Check bank services** – User asks about service status → agent calls GetBankServicesHealth + GetAppRunnerServiceStatus → returns health and RUNNING/PAUSED status.
3. **Investigate why services are down** – Agent uses summary + status to reason: if PAUSED → propose resume; if health fails → report which service is unreachable.
4. **Resume service** – User confirms → agent calls ResumeAppRunnerService (requires confirmation).

## Example Prompts

```
Give me a summary of alerts from the last 24 hours.
```

```
Check the status of our bank services.
```

```
Why are the bank services down? Can you investigate?
```

```
Show me alert statistics and then check if account and payments are healthy.
```

## Setup (summary)

- **ECR**: `agentic-demo/account-service`, `agentic-demo/payments-service`
- **DynamoDB**: Table `AlertAggregates` (pk, sk) in `us-east-2`
- **App Runner**: Both services, port 8000, Instance role with DynamoDB access
- **Lambda**: Deploy `agent/lambda_full_x86.zip`, set env vars, add DynamoDB + App Runner permissions
- **Bedrock**: Create agent, add action groups from `agent/action_group_bank_*.json`, paste `agent/agent_instructions.md`

```bash
./scripts/setup-instance-role.sh          # App Runner Instance role
./scripts/setup-lambda-role.sh <role>     # Lambda permissions
./scripts/push-ecr.sh                     # Build & deploy services
```

See `agent/README.md` and `agent/LAMBDA_SETUP.md` for details.

## Alert API

| Endpoint | Description |
|----------|-------------|
| `GET /agent/summary?hours=12\|24` | Alert summary |
| `POST /agent/generate-one` | Create one alert |
| `POST /agent/generate-bulk?count=200` | Create up to 200 alerts |
