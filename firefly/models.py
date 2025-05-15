from dataclasses import dataclass
from typing import Optional, List

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