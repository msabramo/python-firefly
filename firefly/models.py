from dataclasses import dataclass
from typing import Optional, Dict, Any, List

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