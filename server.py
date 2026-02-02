#!/usr/bin/env python3
"""
MCP Server for sc-stms-api Staging Environment

This server exposes tools for debugging and interacting with the 
sc-stms-api staging service from Cursor AI.
"""

import os
import json
import logging
from typing import Any
from mcp.server.fastmcp import FastMCP
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("sc-stms-api")

# Configuration from environment variables
STAGING_URL = os.getenv("STMS_STAGING_URL", "https://stms-api.noonstg.partners")
STAGING_COOKIE = os.getenv("STMS_STAGING_COOKIE", "")


def get_client() -> httpx.Client:
    """Create an authenticated HTTP client for staging API calls."""
    return httpx.Client(
        base_url=STAGING_URL,
        headers={
            "Cookie": STAGING_COOKIE,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=30.0,
        verify=True,
    )


def format_response(response: httpx.Response) -> dict:
    """Format API response for display."""
    try:
        data = response.json()
        return {
            "status_code": response.status_code,
            "data": data,
        }
    except Exception as e:
        return {
            "status_code": response.status_code,
            "error": str(e),
            "raw_text": response.text[:1000] if response.text else None,
        }


# ============================================================================
# USER TOOLS
# ============================================================================

@mcp.tool()
def whoami() -> dict:
    """
    Get the current authenticated user context.
    Returns business_unit, idp_user_code, and username.
    """
    with get_client() as client:
        response = client.get("/user/whoami")
        return format_response(response)

@mcp.tool()
def give_access_to_user(idp_user_code: str, entity_type: str, entity_code: str, scope_type: str = "default", scope_code: str = None) -> dict:
    """
    Give access to a user for a specific entity.
    """
    with get_client() as client:
        response = client.post("/access-control/access-requests", json={"action": "create", "idp_user_code": idp_user_code, "entity": {"entity_type": entity_type, "entity_code": entity_code}, "scope": {"scope_type": "default", "scope_code": None}, "reason": "Access granted by MCP server"})
        return format_response(response)

if __name__ == "__main__":
    mcp.run()
