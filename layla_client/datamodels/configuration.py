from dataclasses import dataclass
import os
from typing import Optional


@dataclass(kw_only=True)
class Configuration:
    api_key: str
    ocr_service_url: str
    ocr_service_port: Optional[int] = None

    @staticmethod
    def from_env(
            api_key_key: str = 'LAYLA_API_KEY',
            ocr_service_url_key: str = 'LAYLA_OCR_SERVICE_URL',
            ocr_service_port_key: str = 'LAYLA_OCR_SERVICE_PORT',
    ) -> 'Configuration':
        return Configuration(
            api_key=os.getenv(api_key_key),
            ocr_service_url=os.getenv(ocr_service_url_key),
            ocr_service_port=os.getenv(ocr_service_port_key),
        )
