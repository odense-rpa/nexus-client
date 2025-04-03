import httpx
import logging
import json
from authlib.integrations.httpx_client import OAuth2Client
from urllib.parse import urljoin


def _format_json(data: dict) -> str:
    """Format JSON data for logging.
    :param data: The JSON data to format.
    :return: A formatted string representation of the JSON data.
    """
    return json.dumps(data, indent=2)

class NexusClient:
    api: dict

    def __init__(self, instance: str, client_id: str, client_secret: str):
        """
        Initialize the BaseClient with an instance name, client credentials, and dynamically generated URLs.

        :param instance: The name of the Nexus instance.
        :param client_id: The OAuth2 client ID.
        :param client_secret: The OAuth2 client secret.
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

        # Set up the OAuth2 client
        self.client = OAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            token_endpoint=self.token_url,
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
        url = self._normalize_url(endpoint)
        response = self.client.get(url, **kwargs)
        self._handle_errors(response)
        return response

    def post(self, endpoint: str, json: dict, **kwargs) -> httpx.Response:
        url = self._normalize_url(endpoint)

        self.logger.info(f"POST: {url} data: {_format_json(json)}")

        response = self.client.post(url, json=json, **kwargs)
        self._handle_errors(response)
        return response

    def put(self, endpoint: str, json: dict, **kwargs) -> httpx.Response:
        url = self._normalize_url(endpoint)

        self.logger.info(f"PUT: {url} data: {_format_json(json)}")

        response = self.client.put(url, json=json, **kwargs)
        self._handle_errors(response)
        return response

    def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        url = self._normalize_url(endpoint)
        
        self.logger.info(f"DELETE: {url}")
        
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

