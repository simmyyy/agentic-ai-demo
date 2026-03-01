"""
Gets current alert state (snapshot, context, recent actions) from AlertState table.
Used for actionable analysis and action history context.
"""
from __future__ import annotations

import os
from typing import Any

import boto3


TABLE_NAME = os.environ.get("ALERT_STATE_TABLE", "AlertState")
REGION = os.environ.get("AWS_REGION", "us-east-2")


def handler(params: list[dict], body: dict | None) -> dict[str, Any]:
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)

    snapshot = {}
    context = {}
    actions = []

    try:
        r = table.get_item(Key={"pk": "snapshot", "sk": "alerts"})
        snapshot = r.get("Item", {})
    except Exception:
        pass

    try:
        r = table.get_item(Key={"pk": "context", "sk": "current"})
        context = r.get("Item", {})
    except Exception:
        pass

    user_markings = {}
    try:
        r = table.get_item(Key={"pk": "user_markings", "sk": "all"})
        user_markings = r.get("Item", {}).get("markings", {})
    except Exception:
        pass

    try:
        r = table.query(
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={":pk": "action"},
            Limit=20,
            ScanIndexForward=False,
        )
        actions = r.get("Items", [])
    except Exception:
        pass

    return {
        "snapshot": snapshot,
        "context": context,
        "user_markings": user_markings,
        "recent_actions": actions,
    }
