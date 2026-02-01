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

@mcp.tool()
def get_user_profile(idp_user_code: str) -> dict:
    """
    Get detailed profile information for a user.
    
    Args:
        idp_user_code: The IDP user code (e.g., 'stg-xxx@idp.noon.partners')
    """
    with get_client() as client:
        response = client.get(f"/user/{idp_user_code}/profile")
        return format_response(response)


@mcp.tool()
def get_user_by_code(idp_user_code: str) -> dict:
    """
    Get user details by IDP user code.
    
    Args:
        idp_user_code: The IDP user code to look up
    """
    with get_client() as client:
        response = client.post(
            "/user/idp_user_code/",
            json={"idp_user_code": idp_user_code}
        )
        return format_response(response)


@mcp.tool()
def list_users(
    facility_code: str = None,
    designation_code: str = None,
    search: str = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """
    List users with optional filters.
    
    Args:
        facility_code: Filter by facility code (optional)
        designation_code: Filter by designation code (optional)
        search: Search term for user name/email (optional)
        page: Page number (default 1)
        page_size: Results per page (default 20)
    """
    payload = {
        "page": page,
        "page_size": page_size,
    }
    if facility_code:
        payload["facility_code"] = facility_code
    if designation_code:
        payload["designation_code"] = designation_code
    if search:
        payload["search"] = search
    
    with get_client() as client:
        response = client.post("/user/list", json=payload)
        return format_response(response)


# ============================================================================
# ACCESS CONTROL TOOLS
# ============================================================================

@mcp.tool()
def get_user_permissions() -> dict:
    """
    Get all permissions (direct and group-based) for the current user.
    """
    with get_client() as client:
        response = client.post("/access-control/users/permissions", json={})
        return format_response(response)


@mcp.tool()
def get_user_access(idp_user_code: str) -> dict:
    """
    Get current and historical access permissions for a specific user.
    
    Args:
        idp_user_code: The IDP user code
    """
    with get_client() as client:
        response = client.post(
            "/access-control/users/access",
            json={"idp_user_code": idp_user_code}
        )
        return format_response(response)


@mcp.tool()
def check_has_access(entity_type: str, entity_code: str, scope_type: str = None, scope_code: str = None) -> dict:
    """
    Check if the current user has access to a specific entity/scope.
    
    Args:
        entity_type: Type of entity (e.g., 'permission', 'role')
        entity_code: Code of the entity
        scope_type: Type of scope (optional, e.g., 'facility')
        scope_code: Code of scope (optional)
    """
    payload = {
        "entity_type": entity_type,
        "entity_code": entity_code,
    }
    if scope_type:
        payload["scope_type"] = scope_type
    if scope_code:
        payload["scope_code"] = scope_code
    
    with get_client() as client:
        response = client.post("/access-control/users/has-access", json=payload)
        return format_response(response)


@mcp.tool()
def get_flattened_permissions(idp_user_code: str) -> dict:
    """
    Get flattened permissions view for a user (shows all effective permissions).
    
    Args:
        idp_user_code: The IDP user code
    """
    with get_client() as client:
        response = client.post(
            "/access-control/users/flattened-permissions",
            json={"idp_user_code": idp_user_code}
        )
        return format_response(response)


@mcp.tool()
def get_pending_access_requests() -> dict:
    """
    Get pending access requests waiting for approval (for current user as approver).
    """
    with get_client() as client:
        response = client.post(
            "/access-control/users/approver/pending/access-requests",
            json={}
        )
        return format_response(response)


@mcp.tool()
def get_access_request_history(
    idp_user_code: str = None,
    status: str = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """
    Get filtered history of access requests.
    
    Args:
        idp_user_code: Filter by user (optional)
        status: Filter by status - 'pending', 'approved', 'rejected', 'cancelled' (optional)
        page: Page number (default 1)
        page_size: Results per page (default 20)
    """
    payload = {"page": page, "page_size": page_size}
    if idp_user_code:
        payload["idp_user_code"] = idp_user_code
    if status:
        payload["status"] = status
    
    with get_client() as client:
        response = client.post("/access-control/users/access-requests", json=payload)
        return format_response(response)


# ============================================================================
# EVENT QUEUE TOOLS
# ============================================================================

@mcp.tool()
def push_event(event_type: str, payload: dict) -> dict:
    """
    Push an event to the event queue (admin only).
    
    Args:
        event_type: Type of event (e.g., 'user_created', 'user_updated')
        payload: Event payload as a dictionary
    """
    with get_client() as client:
        response = client.post(
            "/events/push",
            json={"event_type": event_type, "payload": payload}
        )
        return format_response(response)


@mcp.tool()
def trigger_cdm_sync() -> dict:
    """
    Trigger CDM ID sync for active users (admin only).
    """
    with get_client() as client:
        response = client.post("/trigger_cdm_id_sync", json={})
        return format_response(response)


# ============================================================================
# DROPDOWN/REFERENCE DATA TOOLS
# ============================================================================

@mcp.tool()
def get_dropdowns() -> dict:
    """
    Get all dropdown/reference values (facilities, designations, vendors, etc.).
    """
    with get_client() as client:
        response = client.get("/dropdowns")
        return format_response(response)


# ============================================================================
# SHIFT & ROSTER TOOLS
# ============================================================================

@mcp.tool()
def list_shifts(
    facility_code: str = None,
    shift_type: str = None,
    page: int = 1,
    page_size: int = 50
) -> dict:
    """
    List shifts with optional filters.
    
    Args:
        facility_code: Filter by facility (optional)
        shift_type: Filter by shift type (optional)
        page: Page number (default 1)
        page_size: Results per page (default 50)
    """
    payload = {"page": page, "page_size": page_size}
    if facility_code:
        payload["facility_code"] = facility_code
    if shift_type:
        payload["shift_type"] = shift_type
    
    with get_client() as client:
        response = client.post("/shifts", json=payload)
        return format_response(response)


@mcp.tool()
def get_roster(
    facility_code: str,
    start_date: str,
    end_date: str,
    designation_code: str = None
) -> dict:
    """
    Get roster data for a facility and date range.
    
    Args:
        facility_code: The facility code
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        designation_code: Filter by designation (optional)
    """
    payload = {
        "facility_code": facility_code,
        "start_date": start_date,
        "end_date": end_date,
    }
    if designation_code:
        payload["designation_code"] = designation_code
    
    with get_client() as client:
        response = client.post("/roster", json=payload)
        return format_response(response)


# ============================================================================
# REPORT TOOLS
# ============================================================================

@mcp.tool()
def list_reports() -> dict:
    """
    Get list of available report types.
    """
    with get_client() as client:
        response = client.get("/reports")
        return format_response(response)


@mcp.tool()
def get_report(report_name: str, format: str = "json") -> dict:
    """
    Get a specific report by name.
    
    Args:
        report_name: Name of the report
        format: Output format - 'json', 'csv', or 'tsv' (default 'json')
    """
    with get_client() as client:
        headers = {}
        if format == "csv":
            headers["Accept"] = "text/csv"
        elif format == "tsv":
            headers["Accept"] = "text/tab-separated-values"
        
        response = client.get(f"/reports/{report_name}", headers=headers)
        
        if format in ("csv", "tsv"):
            return {
                "status_code": response.status_code,
                "data": response.text[:5000],  # Limit output size
            }
        return format_response(response)


# ============================================================================
# ONBOARDING/OFFBOARDING TOOLS
# ============================================================================

@mcp.tool()
def get_onboarding_tasks(
    facility_code: str = None,
    status: str = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """
    Get onboarding tasks dashboard.
    
    Args:
        facility_code: Filter by facility (optional)
        status: Filter by status (optional)
        page: Page number (default 1)
        page_size: Results per page (default 20)
    """
    payload = {"page": page, "page_size": page_size}
    if facility_code:
        payload["facility_code"] = facility_code
    if status:
        payload["status"] = status
    
    with get_client() as client:
        response = client.post("/dashboard/onboarding/tasks", json=payload)
        return format_response(response)


@mcp.tool()
def get_offboarding_tasks(
    facility_code: str = None,
    status: str = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """
    Get offboarding tasks dashboard.
    
    Args:
        facility_code: Filter by facility (optional)
        status: Filter by status (optional)
        page: Page number (default 1)
        page_size: Results per page (default 20)
    """
    payload = {"page": page, "page_size": page_size}
    if facility_code:
        payload["facility_code"] = facility_code
    if status:
        payload["status"] = status
    
    with get_client() as client:
        response = client.post("/dashboard/offboarding/tasks", json=payload)
        return format_response(response)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@mcp.tool()
def health_check() -> dict:
    """
    Check if the staging API is healthy and responding.
    """
    with get_client() as client:
        response = client.get("/public/hc")
        return format_response(response)


# ============================================================================
# GENERIC REQUEST TOOL
# ============================================================================

@mcp.tool()
def api_request(method: str, path: str, body: dict = None) -> dict:
    """
    Make a generic API request to staging. Use this for endpoints not covered by other tools.
    
    Args:
        method: HTTP method - 'GET', 'POST', 'PUT', 'DELETE'
        path: API path (e.g., '/user/list')
        body: Request body for POST/PUT requests (optional)
    """
    with get_client() as client:
        method = method.upper()
        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            response = client.post(path, json=body or {})
        elif method == "PUT":
            response = client.put(path, json=body or {})
        elif method == "DELETE":
            response = client.delete(path)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        return format_response(response)


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("stms://config")
def get_config() -> str:
    """Get current MCP server configuration (without sensitive data)."""
    return json.dumps({
        "staging_url": STAGING_URL,
        "cookie_configured": bool(STAGING_COOKIE),
    }, indent=2)


# ============================================================================
# PROMPTS
# ============================================================================

@mcp.prompt()
def debug_user_access(idp_user_code: str) -> str:
    """
    Generate a debugging workflow for user access issues.
    
    Args:
        idp_user_code: The user code to debug
    """
    return f"""Debug access issues for user: {idp_user_code}

Steps to follow:
1. First, get user profile: get_user_profile("{idp_user_code}")
2. Check their current access: get_user_access("{idp_user_code}")
3. Get their flattened permissions: get_flattened_permissions("{idp_user_code}")
4. Check pending access requests: get_pending_access_requests()

If the user is missing expected permissions:
- Check if there's a pending access request
- Verify the user's facility and designation assignments
- Check if permissions are granted via groups vs directly
"""


@mcp.prompt()
def debug_sync_issue(entity_type: str) -> str:
    """
    Generate a debugging workflow for sync issues.
    
    Args:
        entity_type: Type of entity with sync issues (e.g., 'user', 'attendance')
    """
    return f"""Debug sync issue for entity type: {entity_type}

Steps to follow:
1. Check API health: health_check()
2. Get current user context: whoami()
3. If user sync issue:
   - Get user profile to see last_wf_sync timestamp
   - Check entity_event table for pending events
   - Verify WF integration is returning data

4. Review recent events in the event queue using push_event tool to trace flow
5. Check if the entity exists in both source (WF) and target (STMS) systems
"""


if __name__ == "__main__":
    mcp.run()
