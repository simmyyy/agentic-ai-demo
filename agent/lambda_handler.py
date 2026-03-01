"""
AWS Lambda handler for Bedrock Agent – bank monitoring tools.
Supports both OpenAPI (apiPath) and function-details (function) invocation.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from tools.get_alert_summary import handler as get_alert_summary
from tools.get_bank_services_health import handler as get_bank_services_health
from tools.get_apprunner_service_status import handler as get_apprunner_service_status
from tools.resume_apprunner_service import handler as resume_apprunner_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUICK_ACTION_NAMES = ("action_group_quick_action1", "action_group_quick_action", "quick_action")

TOOL_HANDLERS = {
    "GetAlertSummary": get_alert_summary,
    "getAlertSummary": get_alert_summary,
    "/getAlertSummary": get_alert_summary,
    "GetBankServicesHealth": get_bank_services_health,
    "getBankServicesHealth": get_bank_services_health,
    "/getBankServicesHealth": get_bank_services_health,
    "GetAppRunnerServiceStatus": get_apprunner_service_status,
    "getAppRunnerServiceStatus": get_apprunner_service_status,
    "/getAppRunnerServiceStatus": get_apprunner_service_status,
    "ResumeAppRunnerService": resume_apprunner_service,
    "resumeAppRunnerService": resume_apprunner_service,
    "/resumeAppRunnerService": resume_apprunner_service,
}


def _extract_params(event: dict) -> tuple[list[dict], dict | None]:
    params = event.get("parameters") or []
    body = event.get("requestBody")
    return params, body


def _params_to_dict(params: list[dict], body: dict | None) -> dict[str, Any]:
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


def _infer_tool_from_params(params: list[dict], body: dict | None) -> str | None:
    p = _params_to_dict(params, body)
    if p.get("service_name") or p.get("serviceName"):
        if "resume" in str(p).lower() or p.get("action") == "resume":
            return "ResumeAppRunnerService"
        return "GetAppRunnerServiceStatus"
    if p.get("hours") is not None or p.get("Hours") is not None:
        return "GetAlertSummary"
    return "GetBankServicesHealth"


def _build_openapi_response(event: dict, body: dict, status: int = 200) -> dict:
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", "POST"),
            "httpStatusCode": status,
            "responseBody": {
                "application/json": {"body": json.dumps(body)},
            },
        },
        "sessionAttributes": event.get("sessionAttributes") or {},
        "promptSessionAttributes": event.get("promptSessionAttributes") or {},
    }


def _build_function_response(event: dict, body: dict, state: str = "SUCCESS") -> dict:
    func_resp = {
        "responseBody": {"TEXT": {"body": json.dumps(body)}},
    }
    if state != "SUCCESS":
        func_resp["responseState"] = state
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "function": event.get("function", ""),
            "functionResponse": func_resp,
        },
        "sessionAttributes": event.get("sessionAttributes") or {},
        "promptSessionAttributes": event.get("promptSessionAttributes") or {},
    }


def lambda_handler(event: dict, context: Any) -> dict:
    logger.info(
        "Bedrock invocation: apiPath=%s function=%s actionGroup=%s",
        event.get("apiPath"),
        event.get("function"),
        event.get("actionGroup"),
    )
    try:
        api_path = event.get("apiPath", "").strip("/") or event.get("apiPath")
        func_name = event.get("function", "")
        tool_key = api_path or func_name

        if not tool_key:
            err_body = {"error": "Missing apiPath or function", "message": "Invalid invocation"}
            if "function" in event:
                return _build_function_response(event, err_body, "FAILURE")
            return _build_openapi_response(event, err_body, 400)

        params, body = _extract_params(event)

        if tool_key in QUICK_ACTION_NAMES:
            inferred = _infer_tool_from_params(params, body)
            if inferred:
                tool_key = inferred
                logger.info("Inferred tool: %s", tool_key)
            else:
                err_body = {"error": "Unknown tool", "message": "Could not infer tool from parameters"}
                if "function" in event:
                    return _build_function_response(event, err_body, "FAILURE")
                return _build_openapi_response(event, err_body, 404)

        handler_fn = TOOL_HANDLERS.get(tool_key) or TOOL_HANDLERS.get("/" + tool_key)
        if not handler_fn:
            err_body = {"error": "Unknown tool", "tool": tool_key}
            if "function" in event:
                return _build_function_response(event, err_body, "FAILURE")
            return _build_openapi_response(event, err_body, 404)

        result = handler_fn(params, body)

        if "function" in event:
            return _build_function_response(event, result)
        return _build_openapi_response(event, result)

    except ValueError as e:
        err_body = {"error": "ValidationError", "message": str(e)}
        if event.get("function"):
            return _build_function_response(event, err_body, "REPROMPT")
        return _build_openapi_response(event, err_body, 400)
    except Exception as e:
        logger.exception("Tool execution failed: %s", e)
        err_body = {"error": "InternalError", "message": str(e)}
        if event.get("function"):
            return _build_function_response(event, err_body, "FAILURE")
        return _build_openapi_response(event, err_body, 500)
