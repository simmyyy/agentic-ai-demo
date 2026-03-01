"""
Gets recent incidents from Incidents table.
Use for context when user asks about past incidents.
"""
from __future__ import annotations

import os
from typing import Any

import boto3


TABLE_NAME = os.environ.get("INCIDENTS_TABLE", "Incidents")
REGION = os.environ.get("AWS_REGION", "us-east-2")


def handler(params: list[dict], body: dict | None) -> dict[str, Any]:
    p = _params_to_dict(params, body)
    limit_val = p.get("limit") or p.get("Limit") or "10"
    fetch_all = p.get("fetch_all") or p.get("fetchAll") or p.get("all")
    fetch_all = str(fetch_all).lower() in ("true", "1", "yes", "all")

    if fetch_all:
        limit = None  # no limit, fetch all
    else:
        limit = int(limit_val) if str(limit_val).isdigit() else 10

    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)

    try:
        items = []
        kwargs = {
            "KeyConditionExpression": "pk = :pk",
            "ExpressionAttributeValues": {":pk": "incident"},
            "ScanIndexForward": False,
        }
        if limit is not None:
            kwargs["Limit"] = limit * 2

        while True:
            r = table.query(**kwargs)
            batch = r.get("Items", [])
            if limit is not None:
                items.extend(batch[: limit - len(items)])
            else:
                items.extend(batch)

            if limit is not None and len(items) >= limit:
                items = items[:limit]
                break
            lek = r.get("LastEvaluatedKey")
            if not lek:
                break
            kwargs["ExclusiveStartKey"] = lek

        items = items[:limit] if limit is not None else items
    except Exception as e:
        return {"error": str(e), "incidents": []}

    return {"incidents": items, "count": len(items)}


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
