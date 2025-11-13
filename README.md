# Layla Client

Python client library for the Layla OCR microservices platform.

## Features

- **Synchronous API**: Block until job completes with `submit_job()`
- **Asynchronous API**: Non-blocking with callbacks using `asubmit_job()`
- **Progress Tracking**: Real-time progress updates (page-by-page)
- **Type-Safe**: Pydantic models for all API responses
- **Error Handling**: Custom exceptions for different error scenarios
- **Auto-Cleanup**: Optional automatic job deletion after retrieval
- **Multiple Models**: Support for 3 OCR models with different capabilities

## Installation

```bash
pip install -e .
```

Or with uv:

```bash
uv pip install -e .
```

## Quick Start

### Environment Variables

Create a `.env` file:

```env
LAYLA_OCR_SERVICE_URL=http://localhost
LAYLA_OCR_SERVICE_PORT=8000
LAYLA_API_KEY=test-key-11111111-2222-3333-4444-555555555555
```

### Basic Usage (Synchronous)

```python
from layla_client import LaylaService, Configuration, LaylaModel, LocalFileLoader

config = Configuration.from_env()
service = LaylaService(config)

result = service.submit_job(
    loader=LocalFileLoader("document.pdf"),
    model=LaylaModel.DOC_QWEN_3B_MULTI_V2_0_0_PROD,
    progress_callback=lambda p: print(f"Progress: {p}"),
    auto_delete=True
)

print(result)
```

### Async Usage (Non-Blocking)

```python
from layla_client import LaylaService, Configuration, LaylaModel, LocalFileLoader

config = Configuration.from_env()
service = LaylaService(config)

def on_complete(result: str, error: Exception):
    if error:
        print(f"Error: {error}")
    else:
        print(f"Success! Got {len(result)} characters")

job_id = service.asubmit_job(
    loader=LocalFileLoader("document.pdf"),
    completion_callback=on_complete,
    progress_callback=lambda p: print(f"Progress: {p}"),
    model=LaylaModel.DOC_QWEN_3B_MULTI_V2_0_0_PROD
)

print(f"Job submitted: {job_id}")
```

## API Reference

### LaylaService

The main service class for interacting with the Layla OCR platform.

#### `__init__(configuration: Configuration)`

Initialize the service with configuration.

```python
config = Configuration(
    ocr_service_url="http://localhost",
    ocr_service_port=8000,
    api_key="your-api-key"
)
service = LaylaService(config)
```

#### `submit_job(loader, model=..., timeout=3600, poll_interval=2.0, progress_callback=None, auto_delete=False) -> str`

Submit OCR job and wait for completion (blocking).

**Parameters:**
- `loader` (Loader): File loader instance
- `model` (LaylaModel): OCR model to use (default: DOC_QWEN_3B_MULTI_V2_0_0_PROD)
- `timeout` (int): Max time to wait in seconds (default: 3600)
- `poll_interval` (float): How often to poll status in seconds (default: 2.0)
- `progress_callback` (Callable[[str], None]): Optional progress callback
- `auto_delete` (bool): Delete job after retrieval (default: False)

**Returns:** Markdown string with OCR results

**Raises:**
- `JobTimeoutError`: Job exceeded timeout
- `JobFailedError`: Job failed on server
- `AuthenticationError`: Invalid API key
- `NetworkError`: Connection issues

**Example:**
```python
result = service.submit_job(
    loader=LocalFileLoader("doc.pdf"),
    model=LaylaModel.DOC_QWEN_3B_MULTI_V2_0_0_PROD,
    timeout=1800,
    progress_callback=lambda p: print(p)
)
```

#### `asubmit_job(loader, completion_callback, model=..., progress_callback=None, timeout=3600, poll_interval=2.0, auto_delete=False) -> str`

Submit OCR job asynchronously with callback (non-blocking).

**Parameters:**
- `loader` (Loader): File loader instance
- `completion_callback` (Callable[[str, Exception], None]): Called when done with (result, error)
- `model` (LaylaModel): OCR model to use (default: DOC_QWEN_3B_MULTI_V2_0_0_PROD)
- `progress_callback` (Callable[[str], None]): Optional progress callback
- `timeout` (int): Max time to wait in seconds (default: 3600)
- `poll_interval` (float): How often to poll status in seconds (default: 2.0)
- `auto_delete` (bool): Delete job after retrieval (default: False)

**Returns:** Job ID for tracking

**Example:**
```python
def on_complete(result, error):
    if error:
        print(f"Failed: {error}")
    else:
        print(f"Success: {result}")

job_id = service.asubmit_job(
    loader=LocalFileLoader("doc.pdf"),
    completion_callback=on_complete,
    progress_callback=lambda p: print(f"Progress: {p}")
)
```

#### `get_job_status(job_id: str) -> JobStatusResponse`

Get current status of a job.

**Returns:** JobStatusResponse with status, progress, markdown, etc.

**Example:**
```python
status = service.get_job_status("01HQX123...")
print(f"Status: {status.status}")
if status.progress:
    print(f"Progress: {status.progress}")
```

#### `delete_job(job_id: str) -> bool`

Delete a job and its results.

**Returns:** True if deleted, False if not found

**Example:**
```python
if service.delete_job("01HQX123..."):
    print("Job deleted")
```

#### `health_check() -> HealthResponse`

Check service health.

**Returns:** HealthResponse with service and Redis status

**Example:**
```python
health = service.health_check()
print(f"Service: {health.status}")
print(f"Redis: {health.redis}")
```

### Configuration

Configuration dataclass for the service.

```python
@dataclass
class Configuration:
    ocr_service_url: str
    ocr_service_port: Optional[int] = None
    api_key: str
    
    @staticmethod
    def from_env() -> Configuration:
        """Load from environment variables"""
```

### LaylaModel

Enum of available OCR models:

- `DOC_TRF_0_9B_MULTI_V1_0_0_PROD` - Fast (0.9B params, 109 languages)
- `DOC_TRF_3B_MULTI_V1_0_0_PROD` - Table-aware (3B params, HTML output)
- `DOC_QWEN_3B_MULTI_V2_0_0_PROD` - Advanced multilingual (3B params)

### Exceptions

All exceptions inherit from `LaylaError`:

- `LaylaError`: Base exception
- `JobTimeoutError`: Job exceeded timeout
- `JobFailedError`: Job failed on server
- `NetworkError`: Network/connection error
- `AuthenticationError`: Invalid API key

### Response Models

#### JobStatusResponse

```python
class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # 'processing', 'completed', 'failed'
    model: Optional[str]
    progress: Optional[str]  # e.g., "Processing 12/36 pages"
    markdown: Optional[str]  # Result when completed
    error: Optional[str]     # Error when failed
```

#### HealthResponse

```python
class HealthResponse(BaseModel):
    status: str
    redis: str
    queue_size: Optional[int]
```

## Examples

See `example_usage.py` for comprehensive examples:

```bash
# Synchronous (blocking)
python example_usage.py sync

# Asynchronous (non-blocking)
python example_usage.py async

# Health check
python example_usage.py health

# Manual status checking
python example_usage.py status

# Using environment variables
python example_usage.py env
```

## Error Handling

```python
from layla_client import (
    JobTimeoutError,
    JobFailedError,
    NetworkError,
    AuthenticationError,
)

try:
    result = service.submit_job(
        loader=LocalFileLoader("doc.pdf"),
        timeout=600
    )
except JobTimeoutError:
    print("Job took too long")
except JobFailedError as e:
    print(f"Job failed: {e}")
except AuthenticationError:
    print("Check your API key")
except NetworkError:
    print("Cannot connect to service")
```

## Advanced Usage

### Custom Polling Interval

```python
result = service.submit_job(
    loader=LocalFileLoader("doc.pdf"),
    poll_interval=0.5,  # Poll every 500ms
    timeout=7200  # 2 hour timeout
)
```

### Progress Tracking

```python
def on_progress(progress: str):
    if "Processing" in progress:
        parts = progress.split()
        current, total = parts[1].split('/')
        percent = (int(current) / int(total)) * 100
        print(f"Progress: {percent:.1f}%")

result = service.submit_job(
    loader=LocalFileLoader("doc.pdf"),
    progress_callback=on_progress
)
```

### Async with Thread Safety

```python
import threading

results = {}
lock = threading.Lock()

def on_complete(result, error):
    with lock:
        if error:
            results['error'] = error
        else:
            results['data'] = result

job_id = service.asubmit_job(
    loader=LocalFileLoader("doc.pdf"),
    completion_callback=on_complete
)

# Do other work...

# Wait for completion
import time
while 'data' not in results and 'error' not in results:
    time.sleep(0.1)
```

## Development

### Install Dependencies

```bash
uv pip install -e .
```

### Run Examples

```bash
python example_usage.py sync
```

### Environment Variables

Required:
- `LAYLA_OCR_SERVICE_URL` - Service URL (e.g., http://localhost)
- `LAYLA_OCR_SERVICE_PORT` - Service port (e.g., 8000)
- `LAYLA_API_KEY` - API key for authentication

## License

MIT

