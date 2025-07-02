import httpx
import logging
from authlib.integrations.httpx_client import OAuth2Client
from urllib.parse import urljoin
from typing import Dict, List, Callable, Optional

from .hooks import create_default_hooks, combine_hooks

class NexusClient:
    api: dict

    def __init__(
        self, 
        instance: str, 
        client_id: str, 
        client_secret: str,
        enable_logging: bool = True,
        non_logging_endpoints: Optional[List[str]] = None,
        enable_error_context: bool = True,
        enable_timing: bool = False,
        enable_metrics: bool = False,
        custom_hooks: Optional[Dict[str, List[Callable]]] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the NexusClient with an instance name, client credentials, and optional hooks.

        :param instance: The name of the Nexus instance.
        :param client_id: The OAuth2 client ID.
        :param client_secret: The OAuth2 client secret.
        :param enable_logging: Enable request/response logging (default: True).
        :param non_logging_endpoints: List of endpoint suffixes to skip logging.
        :param enable_error_context: Enable enhanced error context (default: True).
        :param enable_timing: Enable request timing tracking (default: False).
        :param enable_metrics: Enable basic metrics collection (default: False).
        :param custom_hooks: Custom HTTPX event hooks to add.
        :param timeout: Request timeout in seconds (default: 30.0).
        """
        if not instance:
            raise ValueError("Instance name must be provided.")

        # Construct the token and base URLs dynamically - note only works on production instances
        self.token_url = f"https://iam.nexus.kmd.dk/authx/realms/{instance}/protocol/openid-connect/token"
        self.base_url = (
            f"https://{instance}.nexus.kmd.dk/api/core/mobile/{instance}/v2/"
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        # Create event hooks
        hooks = create_default_hooks(
            enable_logging=enable_logging,
            enable_error_context=enable_error_context,
            enable_timing=enable_timing,
            enable_metrics=enable_metrics,
            non_logging_endpoints=non_logging_endpoints or ["/patients/search"],
            logger=self.logger
        )

        # Add custom hooks if provided
        if custom_hooks:
            hooks = combine_hooks(hooks, custom_hooks)

        # Set up the OAuth2 client with event hooks
        self.client = OAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            token_endpoint=self.token_url,
            timeout=timeout,
            event_hooks=hooks
        )

        # Automatically fetch the token during initialization
        self.client.fetch_token()

        self.api = self.parse_links(self.get(self.base_url))

    def _normalize_url(self, endpoint: str) -> str:
        """Ensure the URL is absolute, handling relative URLs."""
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return urljoin(self.base_url, endpoint)

    def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """
        Perform GET request to the specified endpoint.
        
        :param endpoint: API endpoint (relative or absolute URL)
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        url = self._normalize_url(endpoint)
        response = self.client.get(url, **kwargs)
        self._handle_errors(response)
        return response

    def post(self, endpoint: str, json: dict, **kwargs) -> httpx.Response:
        """
        Perform POST request to the specified endpoint.
        
        :param endpoint: API endpoint (relative or absolute URL) 
        :param json: JSON data to send in request body
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        url = self._normalize_url(endpoint)
        response = self.client.post(url, json=json, **kwargs)
        self._handle_errors(response)
        return response

    def put(self, endpoint: str, json: dict, **kwargs) -> httpx.Response:
        """
        Perform PUT request to the specified endpoint.
        
        :param endpoint: API endpoint (relative or absolute URL)
        :param json: JSON data to send in request body
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        url = self._normalize_url(endpoint)
        response = self.client.put(url, json=json, **kwargs)
        self._handle_errors(response)
        return response

    def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        """
        Perform DELETE request to the specified endpoint.
        
        :param endpoint: API endpoint (relative or absolute URL)
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        url = self._normalize_url(endpoint)
        response = self.client.delete(url, **kwargs)
        self._handle_errors(response)
        return response

    def _handle_errors(self, response: httpx.Response):
       
        if response.is_error:
            self.logger.error(f"Response: {response.status_code} - {response.text}")
            
        response.raise_for_status()

    def parse_links(self, response: httpx.Response) -> dict:
        """Extract and normalize links from HATEOAS JSON."""
        links = response.json().get("_links", {})
        normalized_links = {
            rel: self._normalize_url(link["href"]) for rel, link in links.items()
        }
        return normalized_links

