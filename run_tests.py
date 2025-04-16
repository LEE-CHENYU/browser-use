#!/usr/bin/env python
"""
Test Runner Script

This script runs the agent testing framework with the sampled job URLs.
It uses cookie_agent2_v1.py as the execution core.
"""

import asyncio
import os
import argparse
from agent_test_framework import main

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run agent tests on job URLs')
    parser.add_argument('-n', '--num_positions', type=int, default=10,
                        help='Number of job URLs to test')
    parser.add_argument('-p', '--parallel', type=int, default=4,
                        help='Number of parallel tests to run')
    parser.add_argument('--headless', action='store_true',
                        help='Run tests in headless mode')
    parser.add_argument('--steps', type=int, default=20,
                        help='Maximum steps per test')
    args = parser.parse_args()
    
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Print test configuration
    print(f"Running tests with the following configuration:")
    print(f"  - Number of positions: {args.num_positions}")
    print(f"  - Parallel tests: {args.parallel}")
    print(f"  - Headless mode: {args.headless}")
    print(f"  - Max steps per test: {args.steps}")
    
    # Run the main function from agent_test_framework with command line arguments
    asyncio.run(main(num_positions=args.num_positions, 
                     parallel_tests=args.parallel,
                     headless=args.headless,
                     max_steps=args.steps))
