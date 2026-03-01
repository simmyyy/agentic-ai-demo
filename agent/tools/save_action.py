"""
Saves an action to AlertState when user approves and executes (e.g. resume service).
Use to provide context when user asks about past actions.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any

import boto3


TABLE_NAME = os.environ.get("ALERT_STATE_TABLE", "AlertState")
REGION = os.environ.get("AWS_REGION", "us-east-2")


def handler(params: list[dict], body: dict | None) -> dict[str, Any]:
    p = _params_to_dict(params, body)
    service = p.get("service") or p.get("service_name") or ""
    action_type = p.get("action_type") or p.get("actionType") or "resume"
    rationale = p.get("rationale") or p.get("Rationale") or "User approved"
    status = p.get("status") or "EXECUTED"

    if not service:
        return {"error": "service required (account-service or payments-service)", "saved": False}

    action_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    sk = f"{now}#{action_id}"

    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)

    table.put_item(Item={
        "pk": "action",
        "sk": sk,
        "action_id": action_id,
        "service": service,
        "action_type": action_type,
        "rationale": rationale,
        "status": status,
        "created_at": now,
        "executed_at": now,
    })

    return {"saved": True, "action_id": action_id, "service": service, "action_type": action_type}


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
