"""
HTTPX Event Hooks for KMD Nexus Client.

This module provides hook factory functions that can be used with HTTPX's
event hook system to add cross-cutting concerns like logging, error handling,
caching, and metrics to the Nexus client.
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Callable, Optional, Any
from collections import defaultdict

import httpx


def _parse_json(data: Any) -> Any:
    """Parse JSON data for structured logging."""
    if isinstance(data, (str, bytes)):
        try:
            # Try to parse JSON string/bytes to native Python objects
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            return json.loads(data)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return str(data)
    elif isinstance(data, (dict, list)):
        return data
    else:
        return str(data)


def _format_json(data: Any) -> str:
    """Format JSON data for logging (legacy support)."""
    parsed = _parse_json(data)
    if isinstance(parsed, (dict, list)):
        return json.dumps(parsed, indent=2)
    else:
        return str(parsed)


def create_logging_hooks(
    logger: Optional[logging.Logger] = None,
    non_logging_endpoints: Optional[List[str]] = None,
    log_request_body: bool = True,
    log_response_body: bool = False
) -> Dict[str, List[Callable]]:
    """
    Create logging hooks for request/response logging.
    
    Args:
        logger: Logger instance to use (defaults to module logger)
        non_logging_endpoints: List of endpoint suffixes to skip logging
        log_request_body: Whether to log request body for POST/PUT
        log_response_body: Whether to log response body (can be verbose)
        
    Returns:
        Dictionary with 'request' and 'response' hook lists
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    non_logging = non_logging_endpoints or ["/patients/search"]
    
    def log_request(request: httpx.Request) -> None:
        """Log outgoing requests."""
        # Skip logging for certain endpoints
        if any(str(request.url).endswith(endpoint) for endpoint in non_logging):
            return
        
        method = request.method
        url = str(request.url)
        
        if method in ['POST', 'PUT'] and log_request_body and hasattr(request, 'content'):
            try:
                content = request.content
                if content:
                    # Parse JSON for structured logging
                    parsed_data = _parse_json(content)
                    logger.info(
                        f"{method}: {url}",
                        extra={
                            'http_method': method,
                            'http_url': url,
                            'request_data': parsed_data,
                            'event_type': 'http_request'
                        }
                    )
                else:
                    logger.info(
                        f"{method}: {url}",
                        extra={
                            'http_method': method,
                            'http_url': url,
                            'event_type': 'http_request'
                        }
                    )
            except Exception:
                logger.info(
                    f"{method}: {url} (could not log body)",
                    extra={
                        'http_method': method,
                        'http_url': url,
                        'event_type': 'http_request',
                        'error': 'could_not_parse_body'
                    }
                )
        else:
            logger.info(
                f"{method}: {url}",
                extra={
                    'http_method': method,
                    'http_url': url,
                    'event_type': 'http_request'
                }
            )
    
    def log_response(response: httpx.Response) -> None:
        """Log incoming responses."""
        request = response.request
        
        # Skip logging for certain endpoints
        if any(str(request.url).endswith(endpoint) for endpoint in non_logging):
            return
        
        method = request.method
        url = str(request.url)
        status = response.status_code
        
        # Base extra data for all responses
        base_extra = {
            'http_method': method,
            'http_url': url,
            'http_status': status,
            'event_type': 'http_response'
        }
        
        if response.is_error:
            try:
                # Ensure response content is read before accessing text
                if not hasattr(response, '_content'):
                    response.read()
                
                if response.text:
                    parsed_response = _parse_json(response.text)
                    logger.error(
                        f"Response: {method} {url} - {status}",
                        extra={
                            **base_extra,
                            'response_data': parsed_response,
                            'is_error': True
                        }
                    )
                else:
                    logger.error(
                        f"Response: {method} {url} - {status} (no body)",
                        extra={**base_extra, 'is_error': True}
                    )
            except Exception:
                logger.error(
                    f"Response: {method} {url} - {status} (could not read body)",
                    extra={
                        **base_extra,
                        'is_error': True,
                        'error': 'could_not_read_body'
                    }
                )
        elif log_response_body:
            try:
                # Ensure response content is read before accessing text
                if not hasattr(response, '_content'):
                    response.read()
                
                if response.text:
                    parsed_response = _parse_json(response.text)
                    logger.debug(
                        f"Response: {method} {url} - {status}",
                        extra={
                            **base_extra,
                            'response_data': parsed_response
                        }
                    )
                else:
                    logger.debug(
                        f"Response: {method} {url} - {status} (no body)",
                        extra=base_extra
                    )
            except Exception:
                logger.debug(
                    f"Response: {method} {url} - {status} (could not log body)",
                    extra={
                        **base_extra,
                        'error': 'could_not_read_body'
                    }
                )
        else:
            logger.debug(
                f"Response: {method} {url} - {status}",
                extra=base_extra
            )
    
    return {
        'request': [log_request],
        'response': [log_response]
    }


def create_error_context_hooks() -> Dict[str, List[Callable]]:
    """
    Create hooks that add rich context to error responses.
    
    Returns:
        Dictionary with 'response' hook list
    """
    def add_error_context(response: httpx.Response) -> None:
        """Add debugging context to error responses."""
        if response.is_error:
            # Store context in a way that doesn't require dynamic attributes
            context = {
                'method': response.request.method,
                'url': str(response.request.url),
                'status_code': response.status_code,
                'timestamp': datetime.now().isoformat(),
                'headers': dict(response.headers),
                'request_headers': dict(response.request.headers)
            }
            # Context is available for debugging but not attached to response object
            logger = logging.getLogger(__name__)
            logger.debug(f"Error context: {context}")
    
    return {
        'response': [add_error_context]
    }


def create_timing_hooks() -> Dict[str, List[Callable]]:
    """
    Create hooks that track request timing.
    
    Returns:
        Dictionary with 'request' and 'response' hook lists
    """
    # Use a dict to store timing data keyed by request id
    timing_storage = {}
    logger = logging.getLogger(__name__)
    
    def start_timer(request: httpx.Request) -> None:
        """Start timing the request."""
        request_id = id(request)
        timing_storage[request_id] = time.time()
    
    def end_timer(response: httpx.Response) -> None:
        """Calculate and log request duration."""
        request_id = id(response.request)
        if request_id in timing_storage:
            duration = time.time() - timing_storage[request_id]
            logger.info(f"Request timing: {response.request.method} {response.request.url} - {duration:.3f}s")
            # Clean up storage
            del timing_storage[request_id]
    
    return {
        'request': [start_timer],
        'response': [end_timer]
    }




def create_metrics_hooks() -> Dict[str, List[Callable]]:
    """
    Create hooks that collect basic metrics about API usage.
    
    Returns:
        Dictionary with 'request' and 'response' hook lists
    """
    # Simple metrics storage
    metrics = {
        'requests_total': defaultdict(int),
        'responses_by_status': defaultdict(int),
        'errors': []
    }
    
    def track_request(request: httpx.Request) -> None:
        """Track request metrics."""
        metrics['requests_total'][request.method] += 1
    
    def track_response(response: httpx.Response) -> None:
        """Track response metrics."""
        metrics['responses_by_status'][response.status_code] += 1
        
        # Track errors
        if response.is_error:
            metrics['errors'].append({
                'method': response.request.method,
                'url': str(response.request.url),
                'status': response.status_code,
                'timestamp': datetime.now().isoformat()
            })
    
    return {
        'request': [track_request],
        'response': [track_response]
    }


def combine_hooks(*hook_dicts: Dict[str, List[Callable]]) -> Dict[str, List[Callable]]:
    """
    Combine multiple hook dictionaries into one.
    
    Args:
        *hook_dicts: Multiple hook dictionaries to combine
        
    Returns:
        Combined hook dictionary with all hooks
    """
    combined = defaultdict(list)
    
    for hook_dict in hook_dicts:
        for event_type, hooks in hook_dict.items():
            combined[event_type].extend(hooks)
    
    return dict(combined)


def create_default_hooks(
    enable_logging: bool = True,
    enable_error_context: bool = True,
    enable_timing: bool = False,
    enable_metrics: bool = False,
    **kwargs
) -> Dict[str, List[Callable]]:
    """
    Create a default set of hooks for common use cases.
    
    Args:
        enable_logging: Enable request/response logging
        enable_error_context: Enable enhanced error context
        enable_timing: Enable request timing
        enable_metrics: Enable basic metrics collection
        **kwargs: Additional arguments passed to specific hook creators
        
    Returns:
        Combined hook dictionary
    """
    hooks_to_combine = []
    
    if enable_logging:
        hooks_to_combine.append(create_logging_hooks(**kwargs))
    
    if enable_error_context:
        hooks_to_combine.append(create_error_context_hooks())
    
    if enable_timing:
        hooks_to_combine.append(create_timing_hooks())
    
    if enable_metrics:
        hooks_to_combine.append(create_metrics_hooks())
    
    return combine_hooks(*hooks_to_combine) if hooks_to_combine else {}