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

    def generate_image(
        self,
        prompt: str,
        num_variations: Optional[int] = None,
        style: Optional[dict] = None,
        structure: Optional[dict] = None,
        prompt_biasing_locale_code: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        output_format: Optional[str] = None,
        content_class: Optional[str] = None,  # 'photo' or 'art'
        **kwargs
    ) -> FireflyImageResponse:
        """
        Generate an image from a text prompt using Adobe Firefly.

        Args:
            prompt (str): The text prompt for image generation.
            num_variations (int, optional): Number of images to generate (was `n`).
            style (dict, optional): Style object, e.g. {"presets": [...], "imageReference": {...}, "strength": ...}.
            structure (dict, optional): Structure reference object, e.g. {"strength": ..., "imageReference": {...}}.
            prompt_biasing_locale_code (str, optional): Locale code for prompt biasing (was `locale`).
            negative_prompt (str, optional): Negative prompt to avoid certain content.
            seed (int, optional): Seed for deterministic output.
            aspect_ratio (str, optional): Aspect ratio, e.g. "1:1", "16:9".
            output_format (str, optional): Output format, e.g. "jpeg", "png".
            content_class (str, optional): Content class, either 'photo' or 'art'.
            **kwargs: Additional parameters for the API.

        Returns:
            FireflyImageResponse: The response object containing all fields from the API response.

        Raises:
            FireflyAPIError, FireflyAuthError
        """
        data = {"prompt": prompt}
        if num_variations is not None:
            data["numVariations"] = num_variations
        if style is not None:
            data["style"] = style
        if structure is not None:
            data["structure"] = structure
        if prompt_biasing_locale_code is not None:
            data["promptBiasingLocaleCode"] = prompt_biasing_locale_code
        if negative_prompt is not None:
            data["negativePrompt"] = negative_prompt
        if seed is not None:
            data["seed"] = seed
        if aspect_ratio is not None:
            data["aspectRatio"] = aspect_ratio
        if output_format is not None:
            data["outputFormat"] = output_format
        if content_class is not None:
            if content_class not in ("photo", "art"):
                raise ValueError("content_class must be either 'photo' or 'art'")
            data["contentClass"] = content_class
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
        except (KeyError, IndexError, TypeError):
            raise FireflyAPIError(f"Unexpected response format: {resp}")
