"""
Fetches App Runner service status (account-service, payments-service).
Checks whether service is RUNNING or PAUSED.
"""
from __future__ import annotations

import os
from typing import Any

import boto3


def handler(params: list[dict], body: dict | None) -> dict[str, Any]:
    region = os.environ.get("AWS_REGION", "us-east-2")
    client = boto3.client("apprunner", region_name=region)

    service_names = ["account-service", "payments-service"]
    results = []

    for name in service_names:
        try:
            resp = client.list_services()
            svc_list = resp.get("ServiceSummaryList", [])
            arn = None
            for s in svc_list:
                if s.get("ServiceName") == name:
                    arn = s.get("ServiceArn")
                    break
            if not arn:
                results.append({"service": name, "status": "not_found", "arn": None})
                continue

            desc = client.describe_service(ServiceArn=arn)
            svc = desc.get("Service", {})
            status = svc.get("Status", "UNKNOWN")
            results.append({
                "service": name,
                "status": status,
                "arn": arn,
                "service_url": svc.get("ServiceUrl", ""),
            })
        except Exception as e:
            results.append({"service": name, "status": "error", "error": str(e)})

    table = _build_status_table(results)
    paused = [r for r in results if r.get("status") == "PAUSED"]
    return {
        "services": results,
        "table_summary": table,
        "paused_services": [r["service"] for r in paused],
        "recommendation": f"I can resume service(s): {', '.join(p['service'] for p in paused)}. User must accept." if paused else "All services are running.",
    }


def _build_status_table(results: list[dict]) -> str:
    lines = [
        "| Service | Status | URL |",
        "|---------|--------|-----|",
    ]
    for r in results:
        status = r.get("status", "?")
        emoji = "🟢" if status == "RUNNING" else "⏸️" if status == "PAUSED" else "❓"
        url = r.get("service_url", "-") or "-"
        lines.append(f"| {r.get('service', '?')} | {emoji} {status} | {url} |")
    return "\n".join(lines)
