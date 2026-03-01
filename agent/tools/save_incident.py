"""
Saves an incident to Incidents table when user agrees after completing a task.
Call after asking "Do you want to save this event to the incident log?"
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any

import boto3


TABLE_NAME = os.environ.get("INCIDENTS_TABLE", "Incidents")
REGION = os.environ.get("AWS_REGION", "us-east-2")


def handler(params: list[dict], body: dict | None) -> dict[str, Any]:
    p = _params_to_dict(params, body)
    incident_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    sk = f"{now}#{incident_id}"

    service = p.get("service") or "unknown"
    severity = p.get("severity") or "medium"
    summary = p.get("summary") or p.get("Summary") or "Incident logged by agent"
    customer_impact = p.get("customer_impact") or p.get("customerImpact") or ""
    root_cause = p.get("root_cause") or p.get("rootCause") or ""
    actions_taken = p.get("actions_taken") or p.get("actionsTaken") or []
    alert_stats = p.get("alert_stats") or p.get("alertStats") or {}

    if isinstance(actions_taken, str):
        actions_taken = [{"description": actions_taken}]

    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)

    item = {
        "pk": "incident",
        "sk": sk,
        "incident_id": incident_id,
        "status": "OPEN",
        "opened_at": now,
        "resolved_at": None,
        "service": service,
        "severity": severity,
        "summary": summary,
        "customer_impact": customer_impact,
        "root_cause_hypotheses": [root_cause] if root_cause else [],
        "actions": actions_taken,
        "alert_stats": alert_stats,
        "created_by": "agent",
    }

    table.put_item(Item=item)

    return {
        "saved": True,
        "incident_id": incident_id,
        "status": "OPEN",
        "summary": summary,
    }


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
