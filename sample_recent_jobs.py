#!/usr/bin/env python
"""
Sample Recent Jobs

This script extracts the most recent job listings from extracted_job_details.json
based on a configurable percentage parameter.
"""

import json
import argparse
from datetime import datetime
import os

def parse_date(date_str):
    """Parse date string in MM-DD-YY format to datetime object."""
    try:
        return datetime.strptime(date_str, "%m-%d-%y")
    except ValueError:
        # Return a very old date if parsing fails
        return datetime(1900, 1, 1)

def sample_recent_jobs(percentage=10, count=None, output_file="sample_urls.json"):
    """
    Sample the most recent job listings based on update_time.
    
    Args:
        percentage: Percentage of newest jobs to include (1-100)
        count: Exact number of jobs to include (overrides percentage if specified)
        output_file: Output file path for the sampled URLs
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "extracted_job_details.json")
    
    # Load the job details
    with open(input_file, 'r') as f:
        jobs = json.load(f)
    
    # Sort by update_time (newest first)
    sorted_jobs = sorted(jobs, key=lambda x: parse_date(x.get("update_time", "")), reverse=True)
    
    # Determine how many jobs to include
    if count is not None:
        num_jobs = min(count, len(sorted_jobs))
    else:
        num_jobs = max(1, int(len(sorted_jobs) * (percentage / 100)))
    
    # Get the top N jobs
    recent_jobs = sorted_jobs[:num_jobs]
    
    # Extract just the URLs
    urls = [job.get("detail_url") for job in recent_jobs]
    
    # Save to file
    output_path = os.path.join(script_dir, output_file)
    with open(output_path, 'w') as f:
        json.dump(urls, f)
    
    print(f"Sampled {len(urls)} URLs out of {len(jobs)} total jobs ({(len(urls)/len(jobs))*100:.1f}%)")
    print(f"Date range: {recent_jobs[-1].get('update_time', 'N/A')} to {recent_jobs[0].get('update_time', 'N/A')}")
    print(f"Saved to {output_path}")
    
    return urls

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sample recent job listings by date")
    parser.add_argument("-p", "--percentage", type=float, default=10.0,
                      help="Percentage of newest jobs to include (default: 10)")
    parser.add_argument("-n", "--count", type=int, default=None,
                      help="Exact number of jobs to include (overrides percentage if specified)")
    parser.add_argument("-o", "--output", type=str, default="sample_urls.json",
                      help="Output file for sampled URLs (default: sample_urls.json)")
    
    args = parser.parse_args()
    sample_recent_jobs(args.percentage, args.count, args.output)
