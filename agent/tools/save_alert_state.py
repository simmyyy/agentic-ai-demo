"""
Saves alert snapshot and context to AlertState table after fetching alerts.
Call after GetAlertSummary to track first_seen, last_seen, and enable actionable analysis.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import boto3


TABLE_NAME = os.environ.get("ALERT_STATE_TABLE", "AlertState")
REGION = os.environ.get("AWS_REGION", "us-east-2")


def handler(params: list[dict], body: dict | None) -> dict[str, Any]:
    p = _params_to_dict(params, body)
    minutes = p.get("minutes") or p.get("Minutes")
    if minutes is not None:
        try:
            minutes = int(minutes) if isinstance(minutes, str) and minutes.isdigit() else int(float(minutes))
            hours = max(1 / 60, minutes / 60)
        except (ValueError, TypeError):
            hours = 24
    else:
        hours_val = p.get("hours") or p.get("Hours") or "24"
        try:
            hours = float(hours_val) if "." in str(hours_val) else int(hours_val)
        except (ValueError, TypeError):
            hours = 24
        if hours <= 0:
            hours = 24

    # Optional: agent's assessment of which types are actionable/not
    agent_actionable = p.get("agent_actionable") or p.get("agentActionable") or []
    agent_not_actionable = p.get("agent_not_actionable") or p.get("agentNotActionable") or []
    if isinstance(agent_actionable, str):
        agent_actionable = [x.strip() for x in agent_actionable.split(",") if x.strip()]
    elif not isinstance(agent_actionable, list):
        agent_actionable = []
    if isinstance(agent_not_actionable, str):
        agent_not_actionable = [x.strip() for x in agent_not_actionable.split(",") if x.strip()]
    elif not isinstance(agent_not_actionable, list):
        agent_not_actionable = []

    # Get current summary (same logic as get_alert_summary)
    from tools.get_alert_summary import _query_dynamo
    try:
        data = _query_dynamo(hours)
    except Exception as e:
        return {"error": str(e), "saved": False}

    by_type = data.get("by_warning_type", {})
    by_service = data.get("by_service", {})
    total = data.get("total", 0)
    seen_types = set(by_type.keys()) if by_type else set()

    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
    now = datetime.utcnow().isoformat()

    # Get existing snapshot to compute first_seen
    try:
        existing = table.get_item(Key={"pk": "snapshot", "sk": "alerts"})
        item = existing.get("Item")
        first_seen = item.get("first_seen_at", now) if item else now
    except Exception:
        first_seen = now

    # Save snapshot (agent can include actionable/not-actionable assessment)
    table.put_item(Item={
        "pk": "snapshot",
        "sk": "alerts",
        "seen_alert_types": list(seen_types),
        "counts_by_type": by_type,
        "counts_by_service": by_service,
        "total": total,
        "hours": hours,
        "first_seen_at": first_seen,
        "last_seen_at": now,
        "updated_at": now,
        "agent_actionable": agent_actionable,
        "agent_not_actionable": agent_not_actionable,
    })

    # Update context
    table.put_item(Item={
        "pk": "context",
        "sk": "current",
        "last_summary": {"total": total, "by_type": by_type, "by_service": by_service},
        "last_updated": now,
        "last_hours": hours,
    })

    return {"saved": True, "first_seen_at": first_seen, "last_seen_at": now, "total": total}


def _params_to_dict(params: list[dict], body: dict | None) -> dict:
    p = {}
    for x in params or []:
        if isinstance(x, dict) and x.get("name"):
            p[x["name"]] = x.get("value")
    if body and isinstance(body, dict):
        props = body.get("content", {}).get("application/json", {}).get("properties", [])
        if isinstance(props, list):
            for x in props:
                if isinstance(x, dict) and x.get("name"):
                    p[x["name"]] = x.get("value", p.get(x["name"]))
        elif isinstance(props, dict):
            p.update(props)
    return p
