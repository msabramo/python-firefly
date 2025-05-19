# stdlib imports
from typing import Optional, Dict, Any

# third party imports
import requests

# local imports
from .exceptions import FireflyAPIError, FireflyAuthError
from .models import FireflyImage, FireflyImageOutput, FireflyImageResponse, FireflyImageSize
from .ims_auth import AdobeIMSAuth


class FireflyClient:
    """
    Main client for interacting with the Adobe Firefly API.

    Example:
        client = FireflyClient(client_id="...", client_secret="...")
        image_url = client.generate_image(prompt="a cat coding on a laptop")
    """

    BASE_URL = "https://firefly-api.adobe.io/v3/images/generate"

    def __init__(self, client_id: str, client_secret: str, timeout: int = 30):
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._ims_auth = AdobeIMSAuth(client_id, client_secret, timeout)

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
        token = self._ims_auth.get_access_token()
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
            return resp
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
            resp_json = resp.json()
            outputs = [
                FireflyImageOutput(
                    seed=output["seed"],
                    image=FireflyImage(url=output["image"]["url"])
                ) for output in resp_json["outputs"]
            ]
            size = resp_json["size"]
            return FireflyImageResponse(
                size=FireflyImageSize(width=size["width"], height=size["height"]),
                outputs=outputs,
                contentClass=resp_json.get("contentClass"),
                _response=resp,
            )
        except (KeyError, IndexError, TypeError) as e:
            raise FireflyAPIError(f"Unexpected response format: {resp}")
