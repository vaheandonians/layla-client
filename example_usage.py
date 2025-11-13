"""
Layla Client Examples - Comprehensive Teaching Guide

This file demonstrates all the ways to use the Layla OCR client library.
The Layla service is an async OCR platform that:
  1. Accepts job submissions (returns immediately with job_id)
  2. Processes documents in the background
  3. Provides real-time progress updates
  4. Returns results when complete

Key Concepts:
  - SYNCHRONOUS: submit_job() blocks until completion (easy, simple)
  - ASYNCHRONOUS: asubmit_job() returns immediately, callbacks notify completion (advanced)
  - POLLING: The client automatically polls the server for status updates
  - PROGRESS: Get page-by-page progress via callbacks
  - MODELS: Choose from 3 OCR models with different capabilities
"""

import os
import sys
import time
from pathlib import Path

from layla_client import (
    LaylaService,
    Configuration,
    LaylaModel,
    LocalFileLoader,
    OcrJobResponse,
    JobStatusResponse,
    JobTimeoutError,
    JobFailedError,
    NetworkError,
    AuthenticationError,
    LaylaError,
)


def get_test_file():
    """Helper function to find a test PDF file in common locations."""
    test_files = ["document.pdf", "test.pdf"]
    for f in test_files:
        if os.path.exists(f):
            return f
    print("Warning: No test PDF found. Please provide a PDF file as argument.")
    return None


def example_synchronous(file_path: str):
    """
    EXAMPLE 1: Synchronous Job Submission
    
    This is the EASIEST way to use Layla - just call submit_job() and wait.
    The function blocks (waits) until the OCR job is complete.
    
    Use this when:
      - You want simple, straightforward code
      - You can wait for results before continuing
      - You're processing one file at a time
    
    The flow:
      1. Load configuration from environment variables
      2. Create LaylaService instance
      3. Call submit_job() - this BLOCKS until done
      4. Get back OcrJobResponse with the result
    """
    
    config = Configuration.from_env()
    
    service = LaylaService(config)
    
    print("Example 1: Synchronous job submission (blocks until done)")
    print("=" * 60)
    print(f"File: {file_path}")
    print(f"Service: {service._base_url}")
    print()
    
    try:
        response = service.submit_job(
            loader=LocalFileLoader(file_path),
            model=LaylaModel.DOC_QWEN_3B_MULTI_V2_0_0_PROD,
            progress_callback=lambda p: print(f"\r{p}", end="", flush=True),
            auto_delete=False
        )
        
        print("\n\nJob completed!")
        print(f"Job ID: {response.job_id}")
        print(f"Model: {response.model}")
        print(f"Status: {response.status}")
        print(f"Result length: {len(response.result)} characters")
        print(f"\nOCR Result (first 500 chars):")
        print(response.result[:500] + "...")
        
        output_file = f"output_{response.job_id}.md"
        with open(output_file, 'w') as f:
            f.write(response.result)
        print(f"\nFull result saved to: {output_file}")
        
        os.remove(output_file)
        print(f"(Cleaned up temporary file: {output_file})")
        
    except JobTimeoutError as e:
        print(f"Job timed out: {e}")
    except JobFailedError as e:
        print(f"Job failed: {e}")
    except AuthenticationError as e:
        print(f"Authentication error: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")


def example_asynchronous(file_path: str):
    """
    EXAMPLE 2: Asynchronous Job Submission
    
    This is the ADVANCED way to use Layla - submit and continue working.
    The function returns immediately with a job_id, processing happens in background.
    
    Use this when:
      - You need to process multiple files in parallel
      - You want to continue working while OCR runs
      - You're building a UI/web app that can't block
    
    Key concepts:
      - COMPLETION CALLBACK: Called when job finishes (success or failure)
      - PROGRESS CALLBACK: Called periodically with status updates
      - BACKGROUND THREAD: Polling happens in a daemon thread
      - NON-BLOCKING: Main thread continues immediately
    
    The flow:
      1. Submit job with asubmit_job() - returns immediately
      2. Get job_id instantly (job is already processing on server)
      3. Main thread continues working
      4. Background thread polls for status
      5. Completion callback called when done
    """
    
    config = Configuration.from_env()
    service = LaylaService(config)
    
    print("\nExample 2: Asynchronous job submission (non-blocking)")
    print("=" * 60)
    print(f"File: {file_path}")
    print(f"Service: {service._base_url}")
    print()
    
    job_completed = {"done": False}
    
    def on_complete(response: OcrJobResponse, error: Exception):
        """
        COMPLETION CALLBACK
        
        Called exactly once when the job finishes.
        Receives either:
          - response: OcrJobResponse with .result field containing markdown
          - error: Exception if something went wrong
        
        This function runs in the background thread, so be careful with:
          - Shared state (use locks if needed)
          - UI updates (may need to dispatch to main thread)
          - File I/O (generally safe)
        """
        if error:
            print(f"\n\n❌ Job failed with error: {error}")
        else:
            print(f"\n\n✅ Job completed successfully!")
            print(f"Job ID: {response.job_id}")
            print(f"Model: {response.model}")
            print(f"Result length: {len(response.result)} characters")
            print(f"\nFirst 300 chars: {response.result[:300]}...")
            
            output_file = f"output_async_{response.job_id}.md"
            with open(output_file, 'w') as f:
                f.write(response.result)
            print(f"\nFull result saved to: {output_file}")
            
            os.remove(output_file)
            print(f"(Cleaned up temporary file: {output_file})")
        
        job_completed["done"] = True
    
    def on_progress(progress: str):
        """
        PROGRESS CALLBACK
        
        Called each time the progress changes (e.g., "Processing 5/10 pages").
        Use this to:
          - Update progress bars
          - Show real-time status
          - Log processing updates
        
        Note: Only called when progress actually changes, not on every poll.
        """
        print(f"\r{progress}", end="", flush=True)
    
    try:
        job_response = service.asubmit_job(
            loader=LocalFileLoader(file_path),
            completion_callback=on_complete,
            progress_callback=on_progress,
            model=LaylaModel.DOC_QWEN_3B_MULTI_V2_0_0_PROD,
            auto_delete=False
        )
        
        print(f"Job submitted:")
        print(f"  Job ID: {job_response.job_id}")
        print(f"  Model: {job_response.model}")
        print(f"  Status: {job_response.status}")
        print("\nProcessing in background...")
        print("Main thread can continue doing other work:\n")
        
        counter = 0
        while not job_completed["done"]:
            counter += 1
            print(f"\rMain thread tick: {counter}", end="", flush=True)
            time.sleep(0.5)
        
        print("\n\nBackground job finished!")
        
    except AuthenticationError as e:
        print(f"Authentication error: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")


def example_health_check():
    """
    EXAMPLE 4: Health Check
    
    Check if the Layla service is running and healthy.
    This is useful for:
      - Verifying connectivity before submitting jobs
      - Monitoring service availability
      - Checking Redis connection (job queue status)
    
    The health check endpoint does NOT require a file and is fast.
    """
    
    config = Configuration.from_env()
    service = LaylaService(config)
    
    print("\nExample 4: Health check")
    print("=" * 60)
    print(f"Service: {service._base_url}")
    print()
    
    try:
        health = service.health_check()
        print(f"✅ Service status: {health.status}")
        print(f"   Redis status: {health.redis}")
        if health.queue_size is not None:
            print(f"   Queue size: {health.queue_size}")
    except NetworkError as e:
        print(f"❌ Health check failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_job_status(file_path: str):
    """
    EXAMPLE 3: Manual Job Status Checking (Low-Level API)
    
    This demonstrates the LOW-LEVEL API for advanced use cases.
    You manually submit the job and poll for status yourself.
    
    Use this when:
      - You need custom polling logic
      - You want to integrate with your own async framework
      - You need fine-grained control over the workflow
    
    Key methods demonstrated:
      - _submit_job_request(): Submit without waiting
      - get_job_status(): Check status manually
      - delete_job(): Clean up when done
    
    The flow:
      1. Submit job (get job_id immediately)
      2. Loop: Poll status every N seconds
      3. Check if completed/failed
      4. Retrieve result and delete job
    """
    
    config = Configuration.from_env()
    service = LaylaService(config)
    
    print("\nExample 3: Manual job status checking with low-level API")
    print("=" * 60)
    print(f"File: {file_path}")
    print(f"Service: {service._base_url}")
    print()
    
    try:
        job_response = service._submit_job_request(
            loader=LocalFileLoader(file_path),
            model=LaylaModel.DOC_QWEN_3B_MULTI_V2_0_0_PROD
        )
        print(f"Job submitted:")
        print(f"  Job ID: {job_response.job_id}")
        print(f"  Model: {job_response.model}")
        print(f"  Status: {job_response.status}")
        print("\nPolling for status every 2 seconds...\n")
        
        start_time = time.time()
        while True:
            status = service.get_job_status(job_response.job_id)
            elapsed = time.time() - start_time
            
            print(f"\r[{elapsed:.1f}s] Status: {status.status:<12}", end="")
            
            if status.progress:
                print(f" | {status.progress}", end="", flush=True)
            
            if status.status == "completed":
                print(f"\n\n✅ Job completed!")
                print(f"Result length: {len(status.markdown)} characters")
                print(f"First 300 chars: {status.markdown[:300]}...")
                
                delete_response = service.delete_job(job_response.job_id)
                print(f"\n🗑️  {delete_response.message}")
                break
            elif status.status == "failed":
                print(f"\n\n❌ Job failed!")
                print(f"Error: {status.error}")
                break
            
            time.sleep(2)
            
    except LaylaError as e:
        print(f"\n❌ Layla error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def print_usage():
    """Display usage instructions and explain the examples."""
    print("Layla Client - OCR Examples")
    print("=" * 80)
    print("\nUsage: python example_usage.py <example> [file.pdf]")
    print("\nAvailable Examples:")
    print("  sync   - Synchronous (EASY): Blocks until done, returns result")
    print("  async  - Asynchronous (ADVANCED): Non-blocking with callbacks")
    print("  health - Health check (no file required)")
    print("  status - Manual polling (LOW-LEVEL API)")
    print("  all    - Run all examples sequentially")
    print("\n" + "=" * 80)
    print("\nRequired Environment Variables:")
    print("  LAYLA_OCR_SERVICE_URL  - OCR service URL")
    print("  LAYLA_OCR_SERVICE_PORT - OCR service port")
    print("  LAYLA_API_KEY          - API authentication key from service provider")
    print("\nSet these in a .env file or export them:")
    print("  export LAYLA_OCR_SERVICE_URL")
    print("  export LAYLA_OCR_SERVICE_PORT")
    print("  export LAYLA_API_KEY=your-api-key-here")
    print("\n" + "=" * 80)
    print("\nExample Commands:")
    print("  python example_usage.py health                    # Check service status")
    print("  python example_usage.py sync document.pdf         # Process one file (blocking)")
    print("  python example_usage.py async test.pdf            # Process in background")
    print("  python example_usage.py all document.pdf          # Run all examples")
    print("\n" + "=" * 80)
    print("\nAvailable OCR Models:")
    print("  DOC_QWEN_3B_MULTI_V2_0_0_PROD  - Best quality, multilingual (default)")
    print("  DOC_TRF_3B_MULTI_V1_0_0_PROD   - Table-aware, HTML output")
    print("  DOC_TRF_0_9B_MULTI_V1_0_0_PROD - Fastest, 109 languages")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    """
    MAIN ENTRY POINT
    
    This script can be run with different examples to demonstrate various
    features of the Layla client library.
    
    Environment variables are loaded from .env file automatically.
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    example = sys.argv[1]
    file_path = sys.argv[2] if len(sys.argv) > 2 else get_test_file()
    
    if example == "health":
        example_health_check()
    elif example in ["sync", "async", "status", "all"]:
        if not file_path or not os.path.exists(file_path):
            print(f"❌ Error: File not found: {file_path}")
            print("\nPlease provide a valid PDF file:")
            print(f"  python example_usage.py {example} /path/to/document.pdf")
            sys.exit(1)
        
        if example == "sync":
            example_synchronous(file_path)
        elif example == "async":
            example_asynchronous(file_path)
        elif example == "status":
            example_job_status(file_path)
        elif example == "all":
            example_health_check()
            print("\n" + "=" * 80 + "\n")
            example_synchronous(file_path)
            print("\n" + "=" * 80 + "\n")
            example_asynchronous(file_path)
            print("\n" + "=" * 80 + "\n")
            example_job_status(file_path)
    else:
        print(f"❌ Unknown example: {example}")
        print()
        print_usage()
        sys.exit(1)

