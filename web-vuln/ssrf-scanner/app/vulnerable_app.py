"""
SSRF Vulnerable Demonstration Application

This module provides a FastAPI web application containing intentionally vulnerable
routes that illustrate various Server-Side Request Forgery (SSRF) scenarios:
1. In-band SSRF via remote resource fetching.
2. Blind SSRF via webhook subscription.
3. Path-based metadata proxying (AWS/GCP metadata access).

THIS APPLICATIONS IS FOR EDUCATIONAL USE ONLY IN CONTROLLED ENVIRONMENTS.
"""

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import Response, JSONResponse
import httpx
import logging
from pydantic import BaseModel, HttpUrl

app = FastAPI(
    title="SSRF Vulnerable Lab Application",
    description="Educational playground demonstrating vulnerable server-side fetching configurations.",
    version="1.0.0"
)

# Standard logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ssrf_lab.vulnerable_app")


# =====================================================================
# VULNERABLE ROUTE 1: In-Band SSRF (Remote Image Proxy)
# =====================================================================
# This endpoint accepts ANY URL parameter and fetches it directly using
# an unconfigured HTTP client.
#
# Threat Vector:
# An attacker can pass internal network addresses (e.g. http://localhost:8080/admin,
# http://192.168.1.1/) to scan internal assets or read private data.
# =====================================================================

@app.get("/fetch-image")
async def fetch_image(url: str = Query(..., description="Remote image URL to proxy")):
    logger.info("Vulnerable Route: Fetching URL: %s", url)
    
    try:
        # VULNERABILITY: No scheme validation, no IP validation, follows redirects automatically.
        async with httpx.AsyncClient(follow_redirects=True, timeout=3.0) as client:
            response = await client.get(url)
            
        # Return the raw response body and headers directly to the caller (In-band disclosure)
        content_type = response.headers.get("content-type", "application/octet-stream")
        return Response(content=response.content, media_type=content_type)
        
    except httpx.RequestError as exc:
        # Disclosing detailed network error logs helps attackers map internal ports (Error-based SSRF)
        raise HTTPException(
            status_code=502,
            detail=f"Error executing server-side request: {str(exc)}"
        )


# =====================================================================
# VULNERABLE ROUTE 2: Blind SSRF (Webhook Registration)
# =====================================================================
# Users register a URL to receive async event notifications. The server
# triggers requests in the background.
#
# Threat Vector:
# The server initiates connections to private hosts or internal services
# without reporting success or failure to the client. This is used for
# internal port scanning or triggering service endpoints.
# =====================================================================

class WebhookSubscription(BaseModel):
    # Using HttpUrl model enforces basic syntax parsing but does NOT block
    # private subnets or prevent DNS rebinding.
    callback_url: str
    event_type: str

async def trigger_webhook_background(url: str):
    logger.info("Blind SSRF: Dispatching event webhook payload to: %s", url)
    try:
        # VULNERABILITY: Background worker connects to private IP space.
        async with httpx.AsyncClient(timeout=3.0) as client:
            # Send mock event payload
            await client.post(url, json={"event": "test_event", "status": "triggered"})
    except Exception as exc:
        # Errors are logged internally but not disclosed to the client.
        # However, the connection attempt to the target host still occurs.
        logger.error("Failed to deliver webhook in background: %s", str(exc))

@app.post("/webhook-subscribe")
async def subscribe_webhook(sub: WebhookSubscription, background_tasks: BackgroundTasks):
    # Register subscription (normally stored in database)
    logger.info("Vulnerable Route: Webhook subscription registered for: %s", sub.callback_url)
    
    # Trigger an immediate test callback asynchronously (Blind SSRF entry point)
    background_tasks.add_task(trigger_webhook_background, sub.callback_url)
    
    return {"status": "Subscription registered", "message": "Verification callback triggered in background"}


# =====================================================================
# VULNERABLE ROUTE 3: Path-Based Cloud Metadata Proxy
# =====================================================================
# This endpoint appends a user-provided path to the link-local metadata address.
#
# Threat Vector:
# An attacker can access AWS IMDSv1 credentials or GCP metadata by supplying
# specific path directories like 'latest/meta-data/iam/security-credentials/'.
# =====================================================================

AWS_METADATA_BASE = "http://169.254.169.254/"

@app.get("/cloud-proxy")
async def cloud_proxy(path: str = Query(..., description="Path segment to retrieve from cloud proxy")):
    # Construct complete URL
    target_url = f"{AWS_METADATA_BASE}{path.lstrip('/')}"
    logger.info("Vulnerable Route: Cloud metadata proxy requested target: %s", target_url)
    
    try:
        # VULNERABILITY: Direct connection to cloud provider metadata service (IMDSv1).
        async with httpx.AsyncClient(timeout=2.0) as client:
            # Note: For AWS IMDSv1, no special headers are required.
            # For GCP/Azure, custom headers like "Metadata-Flavor: Google" are usually checked,
            # but unvalidated proxies might pass headers through if configured loosely.
            response = await client.get(target_url)
            
        return Response(content=response.content, media_type="text/plain")
        
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to metadata host: {str(exc)}"
        )
