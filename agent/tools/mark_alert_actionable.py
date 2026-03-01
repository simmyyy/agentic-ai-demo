"""
Marks an alert type as actionable or non-actionable (user override).
Call when user says "mark this alert as actionable" or "mark this alert as non-actionable".
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
    alert_type = p.get("alert_type") or p.get("alertType") or ""
    status_raw = (p.get("status") or p.get("Status") or "actionable").lower()
    if "non" in status_raw or status_raw == "not_actionable":
        status = "non-actionable"
    else:
        status = "actionable"

    if not alert_type:
        return {"error": "alert_type required (e.g. timeout, error_rate, latency_high)", "saved": False}

    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
    now = datetime.utcnow().isoformat()

    try:
        existing = table.get_item(Key={"pk": "user_markings", "sk": "all"})
        markings = dict(existing.get("Item", {}).get("markings", {}))
    except Exception:
        markings = {}

    markings[alert_type] = status
    table.put_item(Item={
        "pk": "user_markings",
        "sk": "all",
        "markings": markings,
        "updated_at": now,
    })

    return {"saved": True, "alert_type": alert_type, "status": status}


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
