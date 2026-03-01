"""
Determines which alerts are actionable.
DEFAULT: All alerts are actionable. Only non-actionable if user explicitly marked via MarkAlertActionable.
"""
from __future__ import annotations

from typing import Any

from tools.get_alert_summary import _query_dynamo
from tools.get_alert_state import handler as get_alert_state


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

    try:
        summary_data = _query_dynamo(hours)
        state_data = get_alert_state(params, body)
    except Exception as e:
        return {"error": str(e), "actionable": None}

    user_markings = dict(state_data.get("user_markings", {}))
    current_types = set(summary_data.get("by_warning_type", {}).keys())
    total = summary_data.get("total", 0)

    # DEFAULT: all actionable. Only non-actionable if user explicitly marked.
    by_type_status = {}
    for wtype in current_types:
        if user_markings.get(wtype) == "non-actionable":
            by_type_status[wtype] = "non-actionable"
        else:
            by_type_status[wtype] = "actionable"

    actionable_types = [t for t, s in by_type_status.items() if s == "actionable"]
    non_actionable_types = [t for t, s in by_type_status.items() if s == "non-actionable"]
    overall_actionable = len(actionable_types) > 0
    investigation_needed = overall_actionable

    if total == 0:
        return {
            "actionable": False,
            "reason": "No alerts in the period.",
            "investigation_needed": False,
            "by_type_status": {},
            "summary": summary_data,
        }

    return {
        "actionable": overall_actionable,
        "reason": f"Actionable: {actionable_types}. Non-actionable: {non_actionable_types}." if by_type_status else "No alerts.",
        "investigation_needed": investigation_needed,
        "by_type_status": by_type_status,
        "actionable_types": actionable_types,
        "non_actionable_types": non_actionable_types,
        "summary": summary_data,
    }


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
