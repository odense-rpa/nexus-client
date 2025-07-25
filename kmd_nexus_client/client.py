import httpx
import logging
from authlib.integrations.httpx_client import OAuth2Client
from urllib.parse import urljoin

from .hooks import create_response_logging_hook

class NexusClient:
    """
    Basis klient til KMD Nexus API kommunikation.
    
    VIGTIGT: Brug NexusClientManager i stedet for direkte instantiering.
    """
    api: dict

    def __init__(
        self, 
        instance: str, 
        client_id: str, 
        client_secret: str,
        timeout: float = 30.0
    ):
        """
        Initialize the NexusClient with an instance name and client credentials.

        :param instance: The name of the Nexus instance.
        :param client_id: The OAuth2 client ID.
        :param client_secret: The OAuth2 client secret.
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
        self.logger = logging.getLogger("kmd.nexus")
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        # Create response logging hook
        response_hook = create_response_logging_hook(logger=self.logger)
        hooks = {'response': [response_hook]}

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
        response.raise_for_status()
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
        response.raise_for_status()
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
        response.raise_for_status()
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
        response.raise_for_status()
        return response


    def parse_links(self, response: httpx.Response) -> dict:
        """Extract and normalize links from HATEOAS JSON."""
        links = response.json().get("_links", {})
        normalized_links = {
            rel: self._normalize_url(link["href"]) for rel, link in links.items()
        }
        return normalized_links

    def hent_fra_reference(self, reference: dict) -> dict:
        """
        Hent fuldt objekt fra en reference.

        :param reference: Referencen der skal følges til objektet.
        :return: Det fulde objekt.
        """
        if "referencedObject" in reference["_links"]:
            return self.get(reference["_links"]["referencedObject"]["href"]).json()

        if "self" in reference["_links"]:
            return self.get(reference["_links"]["self"]["href"]).json()

        raise ValueError("Kan ikke hente fra reference - hverken referencedObject eller self link fundet.")

