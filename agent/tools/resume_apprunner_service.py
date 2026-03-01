"""
Resumes (unpause) an App Runner service.
Requires user confirmation – agent invokes only after acceptance.
"""
from __future__ import annotations

import os
from typing import Any

import boto3


def handler(params: list[dict], body: dict | None) -> dict[str, Any]:
    p = _params_to_dict(params, body)
    service_name = p.get("service_name") or p.get("serviceName") or ""
    if not service_name:
        return {"error": "service_name required (account-service or payments-service)"}

    if service_name not in ("account-service", "payments-service"):
        return {"error": f"Invalid service_name: {service_name}. Use account-service or payments-service."}

    region = os.environ.get("AWS_REGION", "us-east-2")
    client = boto3.client("apprunner", region_name=region)

    try:
        resp = client.list_services()
        arn = None
        for s in resp.get("ServiceSummaryList", []):
            if s.get("ServiceName") == service_name:
                arn = s.get("ServiceArn")
                break
        if not arn:
            return {"error": f"Service {service_name} not found in App Runner"}

        client.resume_service(ServiceArn=arn)
        return {
            "status": "resumed",
            "service": service_name,
            "message": f"Service {service_name} has been resumed. Operation is asynchronous – may take 1–2 minutes.",
        }
    except Exception as e:
        return {"error": str(e)}


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
