from dataclasses import dataclass, field
from typing import Optional, List
import requests

@dataclass
class FireflyImageSize:
    width: int
    height: int

@dataclass
class FireflyImage:
    url: str

@dataclass
class FireflyImageOutput:
    seed: int
    image: FireflyImage

@dataclass
class FireflyImageResponse:
    size: FireflyImageSize
    outputs: List[FireflyImageOutput]
    contentClass: Optional[str] = None
    _response: requests.Response = field(repr=False, default=None)

    def json(self):
        """Return the original JSON response from the API."""
        return self._response.json() if self._response is not None else None 