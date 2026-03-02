# Agentic AI Demo

Bank monitoring demo: **App Runner** services + **DynamoDB** + **Bedrock Agent** with Lambda tools.

## Directory Structure

```
agentic-ai-demo/
├── agent/                    # Bedrock Agent & Lambda tools
│   ├── tools/                # Lambda tool implementations (invoked by Bedrock)
│   ├── action_group_bank_*.json   # Action group definitions for Bedrock
│   ├── agent_instructions.md     # Agent system prompt / instructions
│   ├── lambda_handler.py         # Lambda entry point, routes to tools
│   ├── DYNAMODB_SCHEMA.md        # AlertState, Incidents table schema
│   ├── LAMBDA_SETUP.md           # Lambda permissions, env vars
│   └── test_events/              # Sample test payloads for Lambda
├── services/                 # FastAPI microservices (App Runner)
│   ├── account/              # account-service
│   └── payments/             # payments-service
├── README.md
├── requirements.txt          # boto3 (local dev)
└── .gitignore
```

### `agent/` – Bedrock Agent & Lambda

| Path | Purpose |
|------|---------|
| `agent_instructions.md` | System prompt for the Bedrock agent – workflows, formatting rules, tool usage |
| `lambda_handler.py` | AWS Lambda handler – receives Bedrock invocations, dispatches to tool handlers |
| `action_group_bank_1.json` | GetAlertSummary, GetBankServicesStatus |
| `action_group_bank_2.json` | ResumeAppRunnerService (requires confirmation) |
| `action_group_bank_3.json` | SaveAlertState, GetAlertState, GetActionableAlerts |
| `action_group_bank_4.json` | SaveAction, GetActions, GetIncidents |
| `action_group_bank_5.json` | SaveIncident |
| `action_group_bank_6.json` | MarkAlertActionable |
| `DYNAMODB_SCHEMA.md` | Schema for AlertState and Incidents tables |
| `LAMBDA_SETUP.md` | IAM permissions, env vars, Bedrock invoke setup |
| `README.md` | Agent-specific docs, build steps |

### `agent/tools/` – Lambda tools

| Tool | Purpose |
|------|---------|
| `get_alert_summary.py` | Query alerts from DynamoDB AlertAggregates table |
| `get_bank_services_status.py` | Combined health check + App Runner status (uses App Runner URLs) |
| `get_bank_services_health.py` | Health check via HTTP /health (uses env vars) |
| `get_apprunner_service_status.py` | App Runner RUNNING/PAUSED status |
| `save_alert_state.py` | Save alert snapshot to AlertState after GetAlertSummary |
| `get_alert_state.py` | Get current alert state, context, user markings |
| `get_actionable_alerts.py` | Which alerts are actionable vs non-actionable |
| `mark_alert_actionable.py` | User marks alert type as actionable/non-actionable |
| `resume_apprunner_service.py` | Resume paused App Runner service |
| `save_action.py` | Log action (e.g. resume) to AlertState |
| `get_actions.py` | Get action history |
| `save_incident.py` | Save incident to Incidents table |
| `get_incidents.py` | Get incidents (read-only) |

### `agent/test_events/` – Sample payloads

JSON files for testing Lambda tools locally (e.g. `GetAlertSummary.json`, `SaveAlertState.json`).

### `services/` – FastAPI microservices

| Service | Purpose |
|---------|---------|
| `account/main.py` | account-service – FastAPI with /health, /account/balance, alert endpoints |
| `payments/main.py` | payments-service – FastAPI with /health, /payments/status, alert endpoints |

Both services write alerts to DynamoDB and expose `/agent/summary`, `/agent/generate-one`, `/agent/generate-bulk` for demo data.

### Root files

| File | Purpose |
|------|---------|
| `requirements.txt` | boto3 (for local Lambda dev/test) |
| `.gitignore` | Ignore zip files, build artifacts, credentials |

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

**Important:** If you see swapped/wrong service status (e.g. payments DOWN when account is paused, or two separate "Health API" and "App Runner" tables), the agent is using old tools. In Bedrock → Agent → Action groups, ensure **action_group_bank_1** has **only** GetAlertSummary and GetBankServicesStatus. Remove GetBankServicesHealth and GetAppRunnerServiceStatus if present. Then rebuild Lambda (`cd agent && ./build_full.zip.sh amd64`) and redeploy.

## Alert API

| Endpoint | Description |
|----------|-------------|
| `GET /agent/summary?hours=12\|24` | Alert summary |
| `POST /agent/generate-one` | Create one alert |
| `POST /agent/generate-bulk?count=200` | Create up to 200 alerts |
