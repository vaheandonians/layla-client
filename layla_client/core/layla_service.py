import requests
import time
import threading
from typing import Optional, Callable

from layla_client.loaders import Loader
from layla_client.datamodels import (
    Configuration,
    LaylaModel,
    OcrJobResponse,
    JobStatusResponse,
    HealthResponse,
    JobDeleteResponse,
    LaylaError,
    JobTimeoutError,
    JobFailedError,
    NetworkError,
    AuthenticationError,
)


class LaylaService:

    def __init__(self, configuration: Configuration):
        self._configuration = configuration
        if self._configuration.ocr_service_port:
            self._base_url = f'{self._configuration.ocr_service_url}:{self._configuration.ocr_service_port}'
        else:
            self._base_url = self._configuration.ocr_service_url
        self._headers = {'X-API-Key': self._configuration.api_key}

    def submit_job(
        self,
        loader: Loader,
        model: LaylaModel = LaylaModel.DOC_QWEN_3B_MULTI_V2_0_0_PROD,
        timeout: int = 3600,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[str], None]] = None,
        auto_delete: bool = False
    ) -> OcrJobResponse:
        job_response = self._submit_job_request(loader, model)
        
        result = self._wait_for_completion(
            job_id=job_response.job_id,
            timeout=timeout,
            poll_interval=poll_interval,
            progress_callback=progress_callback
        )
        
        if auto_delete:
            try:
                self.delete_job(job_response.job_id)
            except Exception:
                pass
        
        return OcrJobResponse(
            job_id=job_response.job_id,
            status="completed",
            model=job_response.model,
            message="Job completed successfully",
            result=result
        )

    def asubmit_job(
        self,
        loader: Loader,
        completion_callback: Callable[[OcrJobResponse, Optional[Exception]], None],
        model: LaylaModel = LaylaModel.DOC_QWEN_3B_MULTI_V2_0_0_PROD,
        progress_callback: Optional[Callable[[str], None]] = None,
        timeout: int = 3600,
        poll_interval: float = 2.0,
        auto_delete: bool = False
    ) -> OcrJobResponse:
        job_response = self._submit_job_request(loader, model)
        
        def background_worker():
            try:
                result = self._wait_for_completion(
                    job_id=job_response.job_id,
                    timeout=timeout,
                    poll_interval=poll_interval,
                    progress_callback=progress_callback
                )
                
                if auto_delete:
                    try:
                        self.delete_job(job_response.job_id)
                    except Exception:
                        pass
                
                final_response = OcrJobResponse(
                    job_id=job_response.job_id,
                    status="completed",
                    model=job_response.model,
                    message="Job completed successfully",
                    result=result
                )
                completion_callback(final_response, None)
            except Exception as e:
                completion_callback(None, e)
        
        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()
        
        return job_response

    def get_job_status(self, job_id: str) -> JobStatusResponse:
        try:
            response = requests.get(
                f'{self._base_url}/status/{job_id}',
                headers=self._headers
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Missing API key")
            elif response.status_code == 403:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 404:
                raise LaylaError(f"Job not found: {job_id}")
            elif response.status_code == 503:
                raise NetworkError("Service unavailable (Redis disconnected)")
            
            response.raise_for_status()
            return JobStatusResponse(**response.json())
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get job status: {e}")

    def delete_job(self, job_id: str) -> JobDeleteResponse:
        try:
            response = requests.delete(
                f'{self._base_url}/job/{job_id}',
                headers=self._headers
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Missing API key")
            elif response.status_code == 403:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 404:
                raise LaylaError(f"Job not found: {job_id}")
            
            response.raise_for_status()
            return JobDeleteResponse(**response.json())
        except requests.RequestException as e:
            raise NetworkError(f"Failed to delete job: {e}")

    def health_check(self) -> HealthResponse:
        try:
            response = requests.get(f'{self._base_url}/health')
            response.raise_for_status()
            return HealthResponse(**response.json())
        except requests.RequestException as e:
            raise NetworkError(f"Failed to check health: {e}")

    def _submit_job_request(self, loader: Loader, model: LaylaModel) -> OcrJobResponse:
        try:
            filename, file_bytes = loader.load()
            
            import mimetypes
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            response = requests.post(
                f'{self._base_url}/ocr',
                files={'file': (filename, file_bytes, content_type)},
                params={'model': model.value},
                headers=self._headers
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Missing API key")
            elif response.status_code == 403:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 400:
                raise LaylaError(f"Invalid request: {response.text}")
            elif response.status_code == 503:
                raise NetworkError("Model service unavailable")
            
            response.raise_for_status()
            
            job_response = OcrJobResponse(**response.json())
            return job_response
        except requests.RequestException as e:
            raise NetworkError(f"Failed to submit job: {e}")

    def _wait_for_completion(
        self,
        job_id: str,
        timeout: int,
        poll_interval: float,
        progress_callback: Optional[Callable[[str], None]]
    ) -> str:
        start_time = time.time()
        last_progress = None
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise JobTimeoutError(f"Job {job_id} exceeded timeout of {timeout}s")
            
            status_response = self.get_job_status(job_id)
            
            if status_response.status == 'completed':
                if status_response.markdown is None:
                    raise LaylaError("Job completed but no result returned")
                return status_response.markdown
            
            elif status_response.status == 'failed':
                error_msg = status_response.error or "Unknown error"
                raise JobFailedError(f"Job {job_id} failed: {error_msg}")
            
            elif status_response.status == 'processing':
                if progress_callback and status_response.progress:
                    if status_response.progress != last_progress:
                        progress_callback(status_response.progress)
                        last_progress = status_response.progress
                
                time.sleep(poll_interval)
            
            else:
                raise LaylaError(f"Unknown job status: {status_response.status}")
    