"""
Gets action history from AlertState.
Use when user asks about past actions – provide context "I've already performed similar actions."
"""
from __future__ import annotations

import os
from typing import Any

import boto3


TABLE_NAME = os.environ.get("ALERT_STATE_TABLE", "AlertState")
REGION = os.environ.get("AWS_REGION", "us-east-2")


def handler(params: list[dict], body: dict | None) -> dict[str, Any]:
    p = _params_to_dict(params, body)
    limit = p.get("limit") or p.get("Limit") or "10"
    limit = int(limit) if str(limit).isdigit() else 10
    service = p.get("service") or p.get("service_name")

    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)

    try:
        fetch_limit = min(limit, 50) * 3 if service else min(limit, 50)
        r = table.query(
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={":pk": "action"},
            Limit=fetch_limit,
            ScanIndexForward=False,
        )
        actions = r.get("Items", [])
        if service:
            actions = [a for a in actions if a.get("service") == service][:limit]
        else:
            actions = actions[:limit]
    except Exception as e:
        return {"error": str(e), "actions": []}

    return {"actions": actions, "count": len(actions)}


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
