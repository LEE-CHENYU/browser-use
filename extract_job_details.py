import json
import re

# Script to extract detail_url and parsed update_time (MM-DD-25) from aggregated_job_details.json

def extract_details(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = []
    for job in data:
        detail_url = job.get('detail_url')
        update_time_raw = job.get('update_time', '')
        # Extract MM-DD using regex
        match = re.search(r'(\d{2}-\d{2})', update_time_raw)
        if match:
            update_time_parsed = f"{match.group(1)}-25"
        else:
            update_time_parsed = None
        results.append({
            "detail_url": detail_url,
            "update_time": update_time_parsed
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    extract_details(
        "aggregated_job_details.json",
        "extracted_job_details.json"
    )
