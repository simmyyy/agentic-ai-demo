"""
Combined bank services status: Health API (/health) + App Runner status.
Returns ONE merged table – no agent interpretation needed. Each service row is independent.
"""
from __future__ import annotations

from typing import Any

from tools.get_bank_services_health import handler as get_health
from tools.get_apprunner_service_status import handler as get_apprunner


def handler(params: list[dict], body: dict | None) -> dict[str, Any]:
    health_result = get_health(params, body)
    apprunner_result = get_apprunner(params, body)

    health_by_svc = {r["service"]: r for r in health_result.get("services", [])}
    apprunner_by_svc = {r["service"]: r for r in apprunner_result.get("services", [])}

    services = ["account-service", "payments-service"]
    rows = []
    for svc in services:
        h = health_by_svc.get(svc, {})
        ar = apprunner_by_svc.get(svc, {})

        health_status = h.get("status_display", "-")
        health_emoji = "✅" if h.get("status") == "ok" else "🔴"
        apprunner_status = ar.get("status", "-")
        apprunner_emoji = "🟢" if apprunner_status == "RUNNING" else "⏸️" if apprunner_status == "PAUSED" else "❓"
        url_host = h.get("url_host", "-")

        notes = ""
        if apprunner_status == "PAUSED":
            notes = "Service paused – can resume"
        elif h.get("status") != "ok" and h.get("error"):
            notes = str(h.get("error", ""))[:40]

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
