"""
Fetches alert summary directly from DynamoDB.
Works even when App Runner services are down.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

import boto3


TABLE_NAME = os.environ.get("ALERT_TABLE_NAME", "AlertAggregates")
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
        if hours < 1 / 60:
            hours = 1 / 60

    try:
        data = _query_dynamo(hours)
    except Exception as e:
        return {"error": str(e), "summary": None}

    total = data.get("total", 0)
    by_service = data.get("by_service", {})
    by_type = data.get("by_warning_type", {})
    by_host = data.get("by_host", {})

    summary = {
        "hours": data.get("hours", hours),
        "total_alerts": total,
        "by_service": by_service,
        "by_warning_type": by_type,
        "by_host": by_host,
        "table_summary": _build_table_summary(total, by_service, by_type, by_host, hours),
    }
    return {"summary": summary, "raw": data}


def _query_dynamo(hours: float) -> dict:
    """Query DynamoDB AlertAggregates table directly."""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)

    now = datetime.utcnow()
    since = now - timedelta(hours=hours)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%S")
    until_str = now.strftime("%Y-%m-%dT%H:%M:%S")

    resp = table.query(
        KeyConditionExpression="pk = :pk AND sk BETWEEN :since AND :until",
        ExpressionAttributeValues={
            ":pk": "alert",
            ":since": since_str,
            ":until": until_str + ".999~",
        },
    )
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp:
        resp = table.query(
            KeyConditionExpression="pk = :pk AND sk BETWEEN :since AND :until",
            ExpressionAttributeValues={
                ":pk": "alert",
                ":since": since_str,
                ":until": until_str + ".999~",
            },
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))

    by_service = {}
    by_type = {}
    by_host = {}
    for item in items:
        svc = item.get("service", "unknown")
        wtype = item.get("warning_type", "unknown")
        host = item.get("host", "unknown")
        by_service[svc] = by_service.get(svc, 0) + 1
        by_type[wtype] = by_type.get(wtype, 0) + 1
        by_host[host] = by_host.get(host, 0) + 1

    return {
        "hours": hours,
        "total": len(items),
        "by_service": by_service,
        "by_warning_type": by_type,
        "by_host": by_host,
    }


def _build_table_summary(total: int, by_service: dict, by_type: dict, by_host: dict, hours: float) -> str:
    """Build markdown-style table for agent to display."""
    if hours < 1:
        period = f"Last {int(hours * 60)}min"
    else:
        period = f"Last {hours}h" if hours == int(hours) else f"Last {hours}h"
    lines = [
        "| Metric | Value |",
        "|--------|-------|",
        f"| **Total alerts** | {total} |",
        f"| **Period** | {period} |",
        "",
        "**By service:**",
    ]
    for svc, cnt in sorted(by_service.items(), key=lambda x: -x[1]):
        lines.append(f"- {svc}: {cnt}")
    lines.extend(["", "**By alert type:**"])
    for wtype, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
        lines.append(f"- {wtype}: {cnt}")
    if by_host:
        lines.extend(["", "**By host:**"])
        for host, cnt in sorted(by_host.items(), key=lambda x: -x[1])[:5]:
            lines.append(f"- {host}: {cnt}")
    return "\n".join(lines)


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
