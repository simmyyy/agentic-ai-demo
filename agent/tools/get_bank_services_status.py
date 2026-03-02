"""
Combined bank services status: Health API (/health) + App Runner status.
Uses App Runner service_url for health checks – no env var mix-up. Each service row is independent.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests

from tools.get_apprunner_service_status import handler as get_apprunner


def handler(params: list[dict], body: dict | None) -> dict[str, Any]:
    # 1. Get App Runner status – includes service_url per service (source of truth)
    apprunner_result = get_apprunner(params, body)
    apprunner_by_svc = {r["service"]: r for r in apprunner_result.get("services", [])}

    # 2. Health check using App Runner URLs (not env vars – avoids swap/mix-up)
    services = ["account-service", "payments-service"]
    rows = []
    for svc in services:
        ar = apprunner_by_svc.get(svc, {})
        apprunner_status = ar.get("status", "-")
        apprunner_emoji = "🟢" if apprunner_status == "RUNNING" else "⏸️" if apprunner_status == "PAUSED" else "❓"

        raw_url = (ar.get("service_url") or "").strip().rstrip("/")
        if raw_url and not raw_url.startswith("http"):
            raw_url = f"https://{raw_url}"
        base_url = raw_url
        url_host = urlparse(base_url).netloc if base_url else "-"

        # Health check – use URL from App Runner (correct per service)
        if not base_url:
            health_emoji = "🔴"
            health_status = "NO URL"
            notes = "App Runner URL not found"
        else:
            try:
                r = requests.get(f"{base_url}/health", timeout=5)
                ok = r.status_code == 200
                health_emoji = "✅" if ok else "🔴"
                health_status = "OK" if ok else "SERVICE DOWN"
                notes = ""
                if apprunner_status == "PAUSED":
                    notes = "Service paused – can resume"
                elif not ok:
                    notes = f"HTTP {r.status_code}"[:30]
            except requests.RequestException as e:
                health_emoji = "🔴"
                health_status = "SERVICE DOWN"
                notes = str(e)[:40]

        rows.append({
            "service": svc,
            "health_api": f"{health_emoji} {health_status}",
            "app_runner": f"{apprunner_emoji} {apprunner_status}",
            "url_host": url_host,
            "notes": notes,
        })

    table = _build_merged_table(rows)
    paused = [r["service"] for r in rows if "PAUSED" in r.get("app_runner", "")]
    all_ok = all("✅" in r.get("health_api", "") and "🟢" in r.get("app_runner", "") for r in rows)

    return {
        "services": rows,
        "table_summary": table,
        "all_ok": all_ok,
        "paused_services": paused,
        "recommendation": f"I can resume: {', '.join(paused)}. User must accept." if paused else "All services running.",
    }


def _build_merged_table(rows: list[dict]) -> str:
    lines = [
        "| Service | Health API | App Runner | URL Host | Notes |",
        "|---------|------------|------------|----------|-------|",
    ]
    for r in rows:
        svc = r.get("service", "?")
        health = r.get("health_api", "-")
        apprunner = r.get("app_runner", "-")
        url_host = r.get("url_host", "-")
        notes = (r.get("notes") or "-")[:30]
        lines.append(f"| {svc} | {health} | {apprunner} | {url_host} | {notes} |")
    return "\n".join(lines)
