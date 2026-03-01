"""
Checks health of bank services (account, payments).
Returns status in table format.
"""
from __future__ import annotations

import os
from typing import Any

import requests


def handler(params: list[dict], body: dict | None) -> dict[str, Any]:
    account_url = os.environ.get("ACCOUNT_SERVICE_URL", "").rstrip("/")
    payments_url = os.environ.get("PAYMENTS_SERVICE_URL", "").rstrip("/")

    results = []
    services = [
        ("account", account_url, "/health"),
        ("payments", payments_url, "/health"),
    ]

    for name, base_url, path in services:
        if not base_url:
            results.append({"service": name, "status": "unknown", "error": "URL not configured"})
            continue
        try:
            r = requests.get(f"{base_url}{path}", timeout=5)
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            status = "ok" if r.status_code == 200 else "error"
            results.append({
                "service": name,
                "status": status,
                "http_status": r.status_code,
                "response": data,
            })
        except requests.RequestException as e:
            results.append({"service": name, "status": "error", "error": str(e)})

    table = _build_health_table(results)
    return {"services": results, "table_summary": table}


def _build_health_table(results: list[dict]) -> str:
    lines = [
        "| Service | Status | Details |",
        "|---------|--------|---------|",
    ]
    for r in results:
        status = r.get("status", "unknown")
        emoji = "✅" if status == "ok" else "❌"
        detail = r.get("error") or str(r.get("response", ""))
        if len(detail) > 40:
            detail = detail[:37] + "..."
        lines.append(f"| {r.get('service', '?')} | {emoji} {status} | {detail} |")
    return "\n".join(lines)


def _params_to_dict(params: list[dict], body: dict | None) -> dict:
    p = {}
    for x in params or []:
        if isinstance(x, dict) and x.get("name"):
            p[x["name"]] = x.get("value")
    return p
