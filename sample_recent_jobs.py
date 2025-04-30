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
import random

def parse_date(date_str):
    """Parse date string in MM-DD-YY format to datetime object."""
    try:
        return datetime.strptime(date_str, "%m-%d-%y")
    except ValueError:
        # Return a very old date if parsing fails
        return datetime(1900, 1, 1)

def sample_recent_jobs(percentage=10, count=None, output_file="sample_urls.json", input_file="extracted_job_details.json", headless=True, random_sampling=False):
    """
    Sample job listings based on either update_time or random selection.
    
    Args:
        percentage: Percentage of jobs to include (1-100)
        count: Exact number of jobs to include (overrides percentage if specified)
        output_file: Output file path for the sampled URLs
        input_file: Input file path for the extracted job details
        headless: Whether to run in headless mode (for compatibility)
        random_sampling: Whether to use random sampling instead of date-based sampling
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(input_file):
        input_file = os.path.join(script_dir, input_file)
    
    # Load the job details
    with open(input_file, 'r') as f:
        jobs = json.load(f)
    
    # Determine how many jobs to include
    if count is not None:
        num_jobs = min(count, len(jobs))
    else:
        num_jobs = max(1, int(len(jobs) * (percentage / 100)))
    
    if random_sampling:
        # Random sampling
        sampled_jobs = random.sample(jobs, min(num_jobs, len(jobs)))
        sampling_method = "random"
    else:
        # Sort by update_time (newest first)
        sorted_jobs = sorted(jobs, key=lambda x: parse_date(x.get("update_time", "")), reverse=True)
        sampled_jobs = sorted_jobs[:num_jobs]
        sampling_method = "recent"
    
    # Extract just the URLs
    urls = [job.get("detail_url") for job in sampled_jobs]
    
    # Save to file
    output_path = os.path.join(script_dir, output_file)
    with open(output_path, 'w') as f:
        json.dump(urls, f)
    
    print(f"Sampled {len(urls)} URLs out of {len(jobs)} total jobs ({(len(urls)/len(jobs))*100:.1f}%)")
    print(f"Sampling method: {sampling_method}")
    if not random_sampling and len(sampled_jobs) > 1:
        print(f"Date range: {sampled_jobs[-1].get('update_time', 'N/A')} to {sampled_jobs[0].get('update_time', 'N/A')}")
    print(f"Saved to {output_path}")
    
    return urls

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sample job listings by date or randomly")
    parser.add_argument("-p", "--percentage", type=float, default=10.0,
                      help="Percentage of jobs to include (default: 10)")
    parser.add_argument("-n", "--count", type=int, default=None,
                      help="Exact number of jobs to include (overrides percentage if specified)")
    parser.add_argument("-o", "--output", type=str, default="sample_urls.json",
                      help="Output file for sampled URLs (default: sample_urls.json)")
    parser.add_argument("-i", "--input", type=str, default="extracted_job_details.json",
                      help="Input file for extracted job details (default: extracted_job_details.json)")
    parser.add_argument("--headless", action="store_true", default=False,
                      help="Run in headless mode (default: False)")
    parser.add_argument("--random", action="store_true", default=False,
                      help="Use random sampling instead of date-based sampling (default: False)")
    
    args = parser.parse_args()
    sample_recent_jobs(args.percentage, args.count, args.output, input_file=args.input, headless=args.headless, random_sampling=args.random)
