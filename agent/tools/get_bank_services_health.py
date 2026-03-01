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
        ("account-service", account_url, "/health"),
        ("payments-service", payments_url, "/health"),
    ]

    for name, base_url, path in services:
        full_url = f"{base_url}{path}" if base_url else ""
        if not base_url:
            results.append({
                "service": name,
                "status": "unknown",
                "status_display": "NOT CONFIGURED",
                "error": "URL not configured",
                "url_host": "-",
            })
            continue
        try:
            r = requests.get(full_url, timeout=5)
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            status = "ok" if r.status_code == 200 else "error"
            results.append({
                "service": name,
                "status": status,
                "status_display": "OK" if status == "ok" else "SERVICE DOWN",
                "http_status": r.status_code,
                "response": data,
                "url_host": _host_from_url(full_url),
            })
        except requests.RequestException as e:
            results.append({
                "service": name,
                "status": "error",
                "status_display": "SERVICE DOWN",
                "error": str(e),
                "url_host": _host_from_url(full_url),
            })

    table = _build_health_table(results)
    return {"services": results, "table_summary": table}


def _host_from_url(url: str) -> str:
    """Extract host from URL for debugging (e.g. https://abc.awsapprunner.com/health -> abc.awsapprunner.com)."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc or "-"
    except Exception:
        return "-"


def _build_health_table(results: list[dict]) -> str:
    lines = [
        "| Service | Health API | URL Host | Details |",
        "|---------|------------|----------|---------|",
    ]
    for r in results:
        status = r.get("status", "unknown")
        display = r.get("status_display", "OK" if status == "ok" else "SERVICE DOWN")
        emoji = "✅" if status == "ok" else "🔴"
        url_host = r.get("url_host", "-")
        detail = r.get("error") or str(r.get("response", ""))
        if len(detail) > 35:
            detail = detail[:32] + "..."
        lines.append(f"| {r.get('service', '?')} | {emoji} {display} | {url_host} | {detail} |")
    return "\n".join(lines)


def _params_to_dict(params: list[dict], body: dict | None) -> dict:
    p = {}
    for x in params or []:
        if isinstance(x, dict) and x.get("name"):
            p[x["name"]] = x.get("value")
    return p
