# stdlib imports
from dataclasses import dataclass
import time
from typing import Optional, Dict, Any, List

# third party imports
import requests

# local imports
from .exceptions import FireflyAPIError, FireflyAuthError


@dataclass
class FireflyImage:
    url: str


@dataclass
class FireflyImageOutput:
    seed: int
    image: FireflyImage


@dataclass
class FireflyImageResponse:
    size: Dict[str, Any]
    outputs: List[FireflyImageOutput]
    contentClass: Optional[str] = None


class FireflyClient:
    """
    Main client for interacting with the Adobe Firefly API.

    Example:
        client = FireflyClient(client_id="...", client_secret="...")
        image_url = client.generate_image(prompt="a cat coding on a laptop")
    """

    BASE_URL = "https://firefly-api.adobe.io/v3/images/generate"
    TOKEN_URL = "https://ims-na1.adobelogin.com/ims/token/v3"

    def __init__(self, client_id: str, client_secret: str, timeout: int = 30):
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._access_token = None
        self._token_expiry = 0

    def _get_access_token(self) -> str:
        now = time.time()
        if self._access_token and now < self._token_expiry - 60:
            return self._access_token
        # Retrieve new token
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "openid,AdobeID,session,additional_info,read_organizations,firefly_api,ff_apis",
        }
        try:
            resp = requests.post(self.TOKEN_URL, data=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            self._token_expiry = now + int(data.get("expires_in", 3600))
            return self._access_token
        except Exception as e:
            raise FireflyAuthError(f"Failed to retrieve access token: {e}")

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json: Any = None,
        data: Any = None,
        **kwargs,
    ) -> Any:
        token = self._get_access_token()
        req_headers = headers.copy() if headers else {}
        req_headers["Authorization"] = f"Bearer {token}"
        req_headers["x-api-key"] = self.client_id
        if "Content-Type" not in req_headers:
            req_headers["Content-Type"] = "application/json"
        req_headers["Accept"] = "application/json"
        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=req_headers,
                json=json,
                data=data,
                timeout=self.timeout,
                **kwargs,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise FireflyAuthError(f"Unauthorized: {e.response.text}")
            raise FireflyAPIError(f"API error: {e.response.text}")
        except Exception as e:
            raise FireflyAPIError(f"Request failed: {e}")

    def generate_image(self, prompt: str, **kwargs) -> FireflyImageResponse:
        """
        Generate an image from a text prompt using Adobe Firefly.

        Args:
            prompt (str): The text prompt for image generation.
            **kwargs: Additional parameters for the API (e.g., style, aspect ratio).

        Returns:
            FireflyImageResponse: The response object containing all fields from the API response.

        Raises:
            FireflyAPIError, FireflyAuthError
        """
        data = {"prompt": prompt}
        data.update(kwargs)
        resp = self._request(method="POST", url=self.BASE_URL, json=data)
        try:
            outputs = [
                FireflyImageOutput(
                    seed=output["seed"],
                    image=FireflyImage(url=output["image"]["url"])
                )
                for output in resp["outputs"]
            ]
            return FireflyImageResponse(
                size=resp["size"],
                outputs=outputs,
                contentClass=resp.get("contentClass"),
            )
        except (KeyError, IndexError, TypeError) as e:
            raise FireflyAPIError(f"Unexpected response format: {resp}")
