# DynamoDB Schema – AlertState & Incidents

Create tables: `./scripts/setup-tables.sh`

## AlertState Table (pk, sk)

| pk | sk | Purpose |
|----|-----|---------|
| `snapshot` | `alerts` | Current alert snapshot |
| `context` | `current` | Current context (last_summary, etc.) |
| `action` | `<timestamp>#<uuid>` | One row per action |

### snapshot#alerts
- `seen_alert_types` (List) – alert types seen
- `counts_by_type` (Map)
- `counts_by_service` (Map)
- `total`, `hours`
- `first_seen_at`, `last_seen_at`, `updated_at`

### user_markings#all
- `markings` (Map) – `{"timeout": "actionable", "error_rate": "non-actionable"}` (user overrides)
- `updated_at`

### context#current
- `last_summary` (Map)
- `last_updated`, `last_hours`

### action#<timestamp>#<uuid>
- `action_id`, `service`, `action_type`, `rationale`
- `status` (PENDING/APPROVED/EXECUTED)
- `created_at`, `executed_at`

## Incidents Table (pk, sk)

| pk | sk | Purpose |
|----|-----|---------|
| `incident` | `<timestamp>#<uuid>` | One row per incident |

### incident#<timestamp>#<uuid>
- `incident_id`, `status` (OPEN/RESOLVED)
- `opened_at`, `resolved_at`
- `service`, `severity`, `summary`
- `customer_impact`, `root_cause_hypotheses` (List)
- `actions` (List), `alert_stats` (Map)
- `created_by` ("agent" | "admin")
