import time
import requests
from .exceptions import FireflyAuthError

class AdobeIMSAuth:
    TOKEN_URL = "https://ims-na1.adobelogin.com/ims/token/v3"

    def __init__(self, client_id: str, client_secret: str, timeout: int = 30):
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._access_token = None
        self._token_expiry = 0

    def get_access_token(self) -> str:
        now = time.time()
        if self._access_token and now < self._token_expiry - 60:
            return self._access_token
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