# Layla Client Tutorial

A comprehensive guide to using the Layla OCR client library.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding the Architecture](#understanding-the-architecture)
3. [Synchronous vs Asynchronous](#synchronous-vs-asynchronous)
4. [Configuration](#configuration)
5. [Error Handling](#error-handling)
6. [Advanced Usage](#advanced-usage)

---

## Quick Start

### Step 1: Install Dependencies

```bash
pip install -e .
```

### Step 2: Set Environment Variables

Create a `.env` file:

```env
LAYLA_OCR_SERVICE_URL=http://localhost
LAYLA_OCR_SERVICE_PORT=8000
LAYLA_API_KEY=your-api-key-here
```

### Step 3: Run Your First OCR Job

```python
from layla_client import LaylaService, Configuration, LocalFileLoader

config = Configuration.from_env()
service = LaylaService(config)

response = service.submit_job(loader=LocalFileLoader("document.pdf"))
print(response.result)
```

That's it! The simplest possible usage.

---

## Understanding the Architecture

### How Layla Works

Layla is an **asynchronous OCR service**. Here's what happens when you submit a job:

```
┌─────────────┐                ┌─────────────┐
│   Client    │                │   Server    │
│   (You)     │                │   (Layla)   │
└──────┬──────┘                └──────┬──────┘
       │                              │
       │  1. POST /ocr (file)         │
       │──────────────────────────────>│
       │                              │
       │  2. Returns job_id           │  3. Processing
       │<──────────────────────────────│     in background
       │  (immediate!)                │        │
       │                              │        │
       │  4. GET /status/{job_id}     │        │
       │──────────────────────────────>│        │
       │  5. status: "processing"     │        │
       │<──────────────────────────────│        │
       │                              │        │
       │  6. GET /status/{job_id}     │        ✓
       │──────────────────────────────>│
       │  7. status: "completed"      │
       │     + result (markdown text)  │
       │<──────────────────────────────│
       │                              │
```

### Key Points

1. **Job submission is instant** - You get a `job_id` immediately
2. **Processing happens on the server** - Your client doesn't do OCR
3. **You poll for status** - Check `/status/{job_id}` periodically
4. **Results are cached** - Retrieved from Redis when ready

---

## Synchronous vs Asynchronous

### Synchronous: `submit_job()`

**What it does:** Blocks (waits) until the job is complete.

**Use when:**
- You have simple scripts
- You process one file at a time
- You can afford to wait

**Example:**
```python
from layla_client import LaylaService, Configuration, LocalFileLoader

config = Configuration.from_env()
service = LaylaService(config)

response = service.submit_job(
    loader=LocalFileLoader("document.pdf"),
    progress_callback=lambda p: print(f"Progress: {p}")
)

print(f"Result: {response.result}")
```

**Behind the scenes:**
1. Submits job to server → gets `job_id`
2. Starts polling loop (every 2 seconds by default)
3. Calls `progress_callback` when progress updates
4. Returns when `status == "completed"`

### Asynchronous: `asubmit_job()`

**What it does:** Returns immediately, calls your callback when done.

**Use when:**
- You need to process multiple files in parallel
- You're building a web app or UI
- You want to continue working while OCR runs

**Example:**
```python
from layla_client import LaylaService, Configuration, LocalFileLoader

config = Configuration.from_env()
service = LaylaService(config)

def on_complete(response, error):
    if error:
        print(f"Failed: {error}")
    else:
        print(f"Success: {response.result}")

job_response = service.asubmit_job(
    loader=LocalFileLoader("document.pdf"),
    completion_callback=on_complete
)

print(f"Job {job_response.job_id} is processing...")
```

**Behind the scenes:**
1. Submits job to server → gets `job_id`
2. Starts background thread for polling
3. Returns immediately with job info
4. Background thread calls your callback when done

---

## Configuration

### Method 1: Environment Variables (Recommended)

Create `.env` file:
```env
LAYLA_OCR_SERVICE_URL=http://localhost
LAYLA_OCR_SERVICE_PORT=8000
LAYLA_API_KEY=your-api-key
```

Then:
```python
config = Configuration.from_env()
```

### Method 2: Direct Instantiation

```python
config = Configuration(
    api_key="your-api-key",
    ocr_service_url="http://localhost",
    ocr_service_port=8000
)
```

### Method 3: Custom Environment Variable Names

```python
config = Configuration.from_env(
    api_key_key='MY_CUSTOM_API_KEY',
    ocr_service_url_key='MY_CUSTOM_URL',
    ocr_service_port_key='MY_CUSTOM_PORT'
)
```

---

## Error Handling

### Exception Hierarchy

```
LaylaError (base)
├── JobTimeoutError      - Job exceeded timeout
├── JobFailedError       - Job failed on server
├── NetworkError         - Connection/HTTP errors
└── AuthenticationError  - Invalid/missing API key
```

### Best Practices

```python
from layla_client import (
    LaylaService,
    JobTimeoutError,
    JobFailedError,
    NetworkError,
    AuthenticationError,
    LaylaError
)

try:
    response = service.submit_job(loader=LocalFileLoader("doc.pdf"))
    print(response.result)
    
except JobTimeoutError as e:
    print(f"Processing took too long: {e}")
    
except JobFailedError as e:
    print(f"Server-side error: {e}")
    
except AuthenticationError as e:
    print(f"Check your API key: {e}")
    
except NetworkError as e:
    print(f"Connection problem: {e}")
    
except LaylaError as e:
    print(f"Unknown Layla error: {e}")
```

---

## Advanced Usage

### Choosing OCR Models

Three models available with different trade-offs:

```python
from layla_client import LaylaModel

response = service.submit_job(
    loader=LocalFileLoader("doc.pdf"),
    model=LaylaModel.DOC_QWEN_3B_MULTI_V2_0_0_PROD
)

response = service.submit_job(
    loader=LocalFileLoader("doc.pdf"),
    model=LaylaModel.DOC_TRF_3B_MULTI_V1_0_0_PROD
)

response = service.submit_job(
    loader=LocalFileLoader("doc.pdf"),
    model=LaylaModel.DOC_TRF_0_9B_MULTI_V1_0_0_PROD
)
```

### Custom Timeouts and Polling

```python
response = service.submit_job(
    loader=LocalFileLoader("large_document.pdf"),
    timeout=7200,
    poll_interval=5.0
)
```

### Progress Tracking

```python
def track_progress(progress_str):
    if "Processing" in progress_str:
        parts = progress_str.split()
        current, total = parts[1].split('/')
        percent = (int(current) / int(total)) * 100
        print(f"Progress: {percent:.1f}%")

response = service.submit_job(
    loader=LocalFileLoader("doc.pdf"),
    progress_callback=track_progress
)
```

### Auto-Delete After Retrieval

```python
response = service.submit_job(
    loader=LocalFileLoader("doc.pdf"),
    auto_delete=True
)
```

### Parallel Processing (Multiple Files)

```python
from threading import Lock

results = {}
results_lock = Lock()

def make_callback(filename):
    def callback(response, error):
        with results_lock:
            if error:
                results[filename] = {"error": str(error)}
            else:
                results[filename] = {"result": response.result}
    return callback

files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]

for f in files:
    service.asubmit_job(
        loader=LocalFileLoader(f),
        completion_callback=make_callback(f)
    )

while len(results) < len(files):
    time.sleep(0.1)

print("All jobs complete!")
for filename, data in results.items():
    if "error" in data:
        print(f"{filename}: ERROR - {data['error']}")
    else:
        print(f"{filename}: {len(data['result'])} chars")
```

### Manual Job Control (Low-Level API)

```python
job_response = service._submit_job_request(
    loader=LocalFileLoader("doc.pdf"),
    model=LaylaModel.DOC_QWEN_3B_MULTI_V2_0_0_PROD
)

job_id = job_response.job_id

while True:
    status = service.get_job_status(job_id)
    
    if status.status == "completed":
        print(status.result)
        service.delete_job(job_id)
        break
    elif status.status == "failed":
        print(f"Error: {status.error}")
        break
    
    time.sleep(2)
```

### Health Monitoring

```python
try:
    health = service.health_check()
    if health.status == "healthy" and health.redis == "connected":
        print("Service ready!")
    else:
        print("Service degraded")
except NetworkError:
    print("Service unavailable")
```

---

## Response Models

### OcrJobResponse

Returned by `submit_job()` and `asubmit_job()`:

```python
class OcrJobResponse:
    job_id: str          # Unique job identifier (ULID format)
    status: str          # "processing" or "completed"
    model: str           # Model name used
    message: str         # Human-readable message
    result: Optional[str]  # Markdown result (only when completed)
```

### JobStatusResponse

Returned by `get_job_status()`:

```python
class JobStatusResponse:
    job_id: str           # Job identifier
    status: str           # "processing", "completed", or "failed"
    model: Optional[str]  # Model name
    progress: Optional[str]  # e.g., "Processing 5/10 pages"
    result: Optional[str]    # Result (when completed)
    error: Optional[str]     # Error message (when failed)
```

### HealthResponse

Returned by `health_check()`:

```python
class HealthResponse:
    status: str              # "healthy" or other
    redis: str               # "connected" or "disconnected"
    queue_size: Optional[int]  # Number of queued jobs
```

### JobDeleteResponse

Returned by `delete_job()`:

```python
class JobDeleteResponse:
    job_id: str     # Deleted job ID
    message: str    # Confirmation message
```

---

## Common Patterns

### Pattern 1: Simple OCR

```python
from layla_client import LaylaService, Configuration, LocalFileLoader

config = Configuration.from_env()
service = LaylaService(config)
response = service.submit_job(loader=LocalFileLoader("doc.pdf"))
print(response.result)
```

### Pattern 2: Batch Processing

```python
files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
results = []

for f in files:
    response = service.submit_job(
        loader=LocalFileLoader(f),
        progress_callback=lambda p: print(f"{f}: {p}")
    )
    results.append(response.result)
```

### Pattern 3: Fire-and-Forget

```python
def save_result(response, error):
    if not error:
        with open(f"{response.job_id}.md", 'w') as f:
            f.write(response.result)

service.asubmit_job(
    loader=LocalFileLoader("doc.pdf"),
    completion_callback=save_result
)
```

### Pattern 4: Retry Logic

```python
from layla_client import NetworkError
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        response = service.submit_job(loader=LocalFileLoader("doc.pdf"))
        print(response.result)
        break
    except NetworkError as e:
        if attempt < max_retries - 1:
            print(f"Retry {attempt + 1}/{max_retries}...")
            time.sleep(5)
        else:
            raise
```

---

## Troubleshooting

### Problem: "Missing API key" or "Invalid API key"

**Solution:** Check your `.env` file has `LAYLA_API_KEY` set correctly.

```bash
cat .env | grep LAYLA_API_KEY
```

### Problem: "Service unavailable"

**Solution:** Check if the Layla service is running:

```python
health = service.health_check()
print(f"Status: {health.status}, Redis: {health.redis}")
```

### Problem: Job times out

**Solution:** Increase timeout for large documents:

```python
response = service.submit_job(
    loader=LocalFileLoader("large.pdf"),
    timeout=7200
)
```

### Problem: "Job not found"

**Solution:** Jobs expire after 1 hour. Process results promptly or increase TTL on server.

---

## API Reference Summary

### LaylaService Methods

| Method | Returns | Blocking? | Use Case |
|--------|---------|-----------|----------|
| `submit_job()` | `OcrJobResponse` | ✅ Yes | Simple, one-file processing |
| `asubmit_job()` | `OcrJobResponse` | ❌ No | Parallel processing, UI apps |
| `get_job_status()` | `JobStatusResponse` | ❌ No | Manual status checking |
| `delete_job()` | `JobDeleteResponse` | ❌ No | Clean up completed jobs |
| `health_check()` | `HealthResponse` | ❌ No | Service monitoring |

### Parameters

#### `submit_job()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `loader` | `Loader` | required | File loader instance |
| `model` | `LaylaModel` | `DOC_QWEN_3B` | OCR model to use |
| `timeout` | `int` | `3600` | Max wait time (seconds) |
| `poll_interval` | `float` | `2.0` | Poll frequency (seconds) |
| `progress_callback` | `Callable` | `None` | Progress update function |
| `auto_delete` | `bool` | `False` | Delete job after retrieval |

#### `asubmit_job()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `loader` | `Loader` | required | File loader instance |
| `completion_callback` | `Callable` | required | Called when done |
| `model` | `LaylaModel` | `DOC_QWEN_3B` | OCR model to use |
| `progress_callback` | `Callable` | `None` | Progress update function |
| `timeout` | `int` | `3600` | Max wait time (seconds) |
| `poll_interval` | `float` | `2.0` | Poll frequency (seconds) |
| `auto_delete` | `bool` | `False` | Delete job after retrieval |

---

## Examples Index

Run these from the command line to see each pattern in action:

```bash
python example_usage.py health           # Health check
python example_usage.py sync doc.pdf     # Synchronous
python example_usage.py async doc.pdf    # Asynchronous
python example_usage.py status doc.pdf   # Manual polling
python example_usage.py all doc.pdf      # All examples
```

---

## Next Steps

1. ✅ Run `python example_usage.py health` to verify connectivity
2. ✅ Try `python example_usage.py sync document.pdf` for your first OCR
3. ✅ Experiment with different models to find the best for your use case
4. ✅ Read the docstrings in `layla_client/core/layla_service.py` for details
5. ✅ Check `README.md` for full API documentation

Happy OCR'ing! 🚀

