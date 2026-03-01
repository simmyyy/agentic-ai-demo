"""Payments service – FastAPI with alert endpoints."""
import socket
import uuid
from datetime import datetime, timedelta
from typing import Literal

import boto3
from fastapi import FastAPI, HTTPException, Query

app = FastAPI()

SERVICE_NAME = "payments"
TABLE_NAME = "AlertAggregates"
REGION = "us-east-2"
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

WARNING_TYPES = [
    ("timeout", 30),
    ("error_rate", 25),
    ("latency_high", 20),
    ("connection_refused", 10),
    ("oom", 8),
    ("cpu_high", 7),
]


@app.get("/health")
def health():
    return {"status": "ok", "service": "payments"}


@app.get("/payments/status/{payment_id}")
def get_status(payment_id: str):
    return {"payment_id": payment_id, "status": "completed"}


# --- Alert endpoints ---


@app.get("/agent/summary")
def alert_summary(hours: Literal[12, 24] = Query(12, description="12 or 24")):
    """Alert summary for the last 12h or 24h (from all services)."""
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


def _alert_item(sk: str, service: str, warning_type: str, ts: datetime) -> dict:
    return {
        "pk": "alert",
        "sk": sk,
        "service": service,
        "host": socket.gethostname(),
        "warning_type": warning_type,
        "timestamp": ts.isoformat(),
    }


@app.post("/agent/generate-one")
def generate_one_alert(warning_type: str | None = None):
    """Generates one unique alert from this service (payments)."""
    try:
        now = datetime.utcnow()
        ts = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        sk = f"{ts}#{uuid.uuid4().hex[:8]}"
        wtype = warning_type or WARNING_TYPES[hash(sk) % len(WARNING_TYPES)][0]

        item = _alert_item(sk, SERVICE_NAME, wtype, now)
        table.put_item(Item=item)
        return {"status": "created", "alert": item}
    except Exception as e:
        err = f"{type(e).__name__}: {str(e)}"
        if hasattr(e, "response"):
            err += f" | {e.response.get('Error', {})}"
        raise HTTPException(status_code=500, detail=err)


@app.post("/agent/generate-bulk")
def generate_bulk_alerts(
    count: int = Query(200, ge=1, le=200, description="Number of alerts (max 200)"),
):
    """Generates up to 200 alerts from this service (payments), various types."""
    try:
        now = datetime.utcnow()
        weights = [w for _, w in WARNING_TYPES]
        total_w = sum(weights)

        for i in range(count):
            ts_dt = now - timedelta(seconds=i)
            ts = ts_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            sk = f"{ts}#{uuid.uuid4().hex[:8]}"

            r = (i * 31) % total_w
            cumul = 0
            wtype = WARNING_TYPES[0][0]
            for wt, w in WARNING_TYPES:
                cumul += w
                if r < cumul:
                    wtype = wt
                    break

            item = _alert_item(sk, SERVICE_NAME, wtype, ts_dt)
            table.put_item(Item=item)

        return {"status": "created", "count": count, "service": SERVICE_NAME, "host": socket.gethostname()}
    except Exception as e:
        err = f"{type(e).__name__}: {str(e)}"
        if hasattr(e, "response"):
            err += f" | {e.response.get('Error', {})}"
        raise HTTPException(status_code=500, detail=err)
