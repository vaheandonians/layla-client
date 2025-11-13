from layla_client.datamodels.configuration import Configuration
from layla_client.datamodels.ocr_model import OCRModel


class LaylaService:

    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    def submit_job(self, file: bytes, model: OCRModel = OCRModel.DOC_QWEN_3B_MULTI_V2_0_0_PROD) -> str:
        pass