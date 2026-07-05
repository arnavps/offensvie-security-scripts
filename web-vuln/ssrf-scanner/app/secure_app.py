"""
SSRF Secure Demonstration Application

This module provides a secure counterpart to the vulnerable FastAPI application.
It integrates:
1. Scheme, port, and hostname validation at the endpoint layer.
2. The DNSRebindingSafeAsyncTransport client at the outbound network layer.
3. Clean, error-safe response handling preventing detailed network leakage.
4. Structured logging to feed detection telemetry pipelines.

THIS APPLICATION DEMONSTRATES SECURE SYSTEM DESIGN PRINCIPLES.
"""

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import Response, JSONResponse
import httpx
import logging
import time
from pydantic import BaseModel
from lib.validator import SSRFValidator
from app.middleware import get_safe_async_client

app = FastAPI(
    title="SSRF Secure Lab Application",
    description="Educational playground demonstrating secure server-side fetching configurations.",
    version="1.0.0"
)

# Standard logging configuration (Configured to output security logs clearly)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ssrf_lab.secure_app")

# Initialize central security validator
validator = SSRFValidator(
    allowed_schemes={"http", "https"},
    allowed_ports={80, 443},
    block_private_ips=True
)


def log_security_event(event_type: str, url: str, outcome: str, details: str):
    """
    Emits structured security log data suitable for SIEM alerts.
    """
    event = {
        "timestamp": time.time(),
        "event_type": event_type,
        "url": url,
        "outcome": outcome,
        "details": details
    }
    logger.warning(
        "SECURITY AUDIT [%s] - URL: %s - OUTCOME: %s - DETAILS: %s",
        event_type, url, outcome, details,
        extra={"security_telemetry": event}
    )


# =====================================================================
# SECURE ROUTE 1: In-Band SSRF Mitigation (Remote Image Proxy)
# =====================================================================
# This endpoint uses our SSRF-safe HTTP client which blocks private IP space
# and prevents DNS Rebinding attacks.
# =====================================================================

@app.get("/fetch-image")
async def fetch_image(url: str = Query(..., description="Remote image URL to proxy")):
    logger.info("Secure Route: Request to fetch image from: %s", url)
    
    # 1. Immediate validation check before initiating connection
    is_valid, reason = validator.validate_url(url)
    if not is_valid:
        log_security_event("SSRF_ATTEMPT_BLOCKED", url, "BLOCKED", reason)
        raise HTTPException(
            status_code=400,
            detail="The requested URL is invalid or prohibited by security policy."
        )
        
    try:
        # 2. Use our secure client equipped with DNS Rebinding protection
        async with get_safe_async_client(validator) as client:
            # The client handles URL rewriting and DNS enforcement automatically.
            # Redirects are disabled by default (follow_redirects=False) in get_safe_async_client.
            response = await client.get(url)
            
        if response.status_code != 200:
            return JSONResponse(
                status_code=response.status_code,
                content={"message": "Remote server returned an error response."}
            )

        content_type = response.headers.get("content-type", "application/octet-stream")
        return Response(content=response.content, media_type=content_type)
        
    except httpx.ConnectError as exc:
        # Log the detailed error locally for debugging and SIEM detection
        logger.error("Outbound connection blocked or failed: %s", str(exc))
        log_security_event("OUTBOUND_CONNECTION_FAILED", url, "FAILED", str(exc))
        
        # Return a generic error to the client to prevent port-scanning information disclosure
        raise HTTPException(
            status_code=502,
            detail="Failed to retrieve the requested resource."
        )
    except Exception as exc:
        logger.critical("Unexpected error during image fetch: %s", str(exc))
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred."
        )


# =====================================================================
# SECURE ROUTE 2: Blind SSRF Mitigation (Webhook Registration)
# =====================================================================
# Webhook registrations are validated at submission time and executed
# using the secure HTTP client in the background worker.
# =====================================================================

class WebhookSubscription(BaseModel):
    callback_url: str
    event_type: str

async def trigger_secure_webhook_background(url: str):
    logger.info("Secure Webhook delivery: Initiating callback to: %s", url)
    
    # Validation occurs again in the worker to defend against configuration changes
    is_valid, reason = validator.validate_url(url)
    if not is_valid:
        log_security_event("BLIND_SSRF_WORKER_BLOCKED", url, "BLOCKED", reason)
        return

    try:
        async with get_safe_async_client(validator) as client:
            await client.post(url, json={"event": "test_event", "status": "secure"})
            logger.info("Secure Webhook delivered successfully to: %s", url)
    except Exception as exc:
        logger.error("Secure background webhook delivery failed: %s", str(exc))


@app.post("/webhook-subscribe")
async def subscribe_webhook(sub: WebhookSubscription, background_tasks: BackgroundTasks):
    logger.info("Secure Route: Webhook subscription attempt for: %s", sub.callback_url)
    
    # Validate the URL before accepting the registration
    is_valid, reason = validator.validate_url(sub.callback_url)
    if not is_valid:
        log_security_event("SSRF_WEBHOOK_REGISTRATION_BLOCKED", sub.callback_url, "REJECTED", reason)
        raise HTTPException(
            status_code=400,
            detail="The provided callback URL is not allowed by the security policy."
        )
        
    # Queue the webhook delivery task safely
    background_tasks.add_task(trigger_secure_webhook_background, sub.callback_url)
    
    return {"status": "Subscription registered", "message": "Verification callback queued."}


# =====================================================================
# SECURE ROUTE 3: Hardened Cloud Metadata Access
# =====================================================================
# The secure application does NOT expose proxy routing to internal or cloud
# metadata subnets under any circumstances.
# =====================================================================

@app.get("/cloud-proxy")
async def cloud_proxy(path: str = Query(..., description="Path segment")):
    # Secure application strictly prohibits direct proxying to local ranges
    # or link-local cloud metadata addresses.
    log_security_event(
        "PROHIBITED_ENDPOINT_ACCESS",
        f"metadata-proxy://{path}",
        "BLOCKED",
        "Direct cloud metadata proxying is completely disabled in the secure build."
    )
    raise HTTPException(
        status_code=403,
        detail="Access to the cloud metadata service proxy is prohibited by security architecture."
    )
