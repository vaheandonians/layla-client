from dataclasses import Field, dataclass
from typing import Optional


@dataclass
class Configuration:
    ocr_service_url: str
    ocr_service_port: Optional[int] = None
    api_key: Optional[str] = None
