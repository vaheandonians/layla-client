import requests
import time

document_path = 'document.pdf'
result_path = 'result.md'

# Submit job (returns immediately)
with open(document_path, 'rb') as f:
    response = requests.post(
        'http://cognaize-ocr.ngrok.app/ocr',
        files={'file': f},
        params={'model': 'doc_qwen_3b_multi_v2.0.0_prod'}  # or full name
    )
    print(response.json())
    job_id = response.json()['job_id']
    print(f"Job submitted: {job_id}")

# Poll for results with progress
while True:
    response = requests.get(f'http://cognaize-ocr.ngrok.app/status/{job_id}')
    data = response.json()

    if data['status'] == 'completed':
        print("\nCompleted!")
        with open(result_path, 'w') as f:
            f.write(data['markdown'])
        break
    elif data['status'] == 'failed':
        print(f"Error: {data['error']}")
        break

    # Show progress if available
    progress = data.get('progress', 'Processing...')
    print(f"Status: {progress}", end='\r')
    time.sleep(2)
