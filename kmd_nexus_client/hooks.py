"""
HTTPX Event Hooks for KMD Nexus Client.

This module provides hook factory functions that can be used with HTTPX's
event hook system to add cross-cutting concerns like logging and error handling
to the Nexus client.
"""

import json
import logging
from typing import Callable, Optional, Any

import httpx


def create_response_logging_hook(
    logger: logging.Logger
) -> Callable[[httpx.Response], None]:
    """
    Create response logging hook for KMD Nexus API that captures HTTP transactions.

    Args:
        logger: Logger instance to use (defaults to module logger)

    Returns:
        Response hook function
    """
    # KMD Nexus specific endpoints to skip logging (reduce noise)
    non_logging_endpoints = ["/patients/search", "/protocol/openid-connect/token"]

    def log_response(response: httpx.Response) -> None:
        """Log complete HTTP transaction from response."""
        request = response.request

        # Skip logging for certain KMD Nexus endpoints to reduce noise
        if any(
            str(request.url).endswith(endpoint) for endpoint in non_logging_endpoints
        ):
            return

        method = request.method
        url = str(request.url)
        status = response.status_code

        # Extract request JSON if available
        request_json = None
        try:
            if hasattr(request, "content") and request.content:
                request_json = _parse_json_content(request.content)
        except Exception:
            # Request content not available or not readable
            request_json = None

        # Always extract response JSON (for debugging API responses)
        response_json = None
        try:
            # Force read the response if it hasn't been read yet
            if not hasattr(response, '_content'):
                response.read()
            response_json = _parse_json_content(response.text)
        except Exception:
            # Response content not available or not readable
            response_json = None

        # Extract headers
        request_headers = dict(request.headers) if hasattr(request, 'headers') else {}
        response_headers = dict(response.headers) if hasattr(response, 'headers') else {}
        
        # Calculate duration in milliseconds
        duration_ms = int(response.elapsed.total_seconds() * 1000) if hasattr(response, 'elapsed') and response.elapsed else 0

        # Build complete log entry with nested HTTP structure
        extra = {
            "http": {
                "method": method,
                "url": url,
                "request_headers": request_headers,
                "request_body": request_json,
                "response_status": status,
                "response_headers": response_headers,
                "response_body": response_json,
                "duration_ms": duration_ms,
            },
        }

        # Log with appropriate level
        if response.is_error:
            logger.error(f"HTTP {status}: {method} {url}", extra=extra)
        else:
            if request.method in ["GET", "HEAD", "OPTIONS"]:
                logger.debug(f"HTTP {status}: {method} {url}", extra=extra)
            else:
                logger.info(f"HTTP {status}: {method} {url}", extra=extra)

        return  # End of log_response function

    return log_response


def _parse_json_content(content: Any) -> Optional[Any]:
    """
    Parse JSON content from request/response body.

    Returns parsed JSON if valid, None otherwise.
    """
    if not content:
        return None

    # Convert bytes to string if needed
    if isinstance(content, bytes):
        try:
            content = content.decode("utf-8")
        except UnicodeDecodeError:
            return None

    # Parse JSON
    try:
        return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return None
