"""
Agent Testing Framework

This module provides a comprehensive testing framework for browser-use agents.
It supports configurable test runs with detailed logging of success/failure 
status and summarizes reasons for failures.
"""

import asyncio
import datetime
import json
import logging
import os
import time
from typing import List, Dict, Any, Optional, Tuple, Callable

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig


class TestLogger:
    """Handles structured logging for agent test results."""
    
    def __init__(self, log_dir: str = "logs", log_level: int = logging.INFO):
        """
        Initialize the test logger.
        
        Args:
            log_dir: Directory to store log files
            log_level: Logging level (INFO, DEBUG, etc.)
        """
        self.log_dir = log_dir
        self.log_level = log_level
        self.results = {
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "failures": [],
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0
        }
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate timestamped filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"{log_dir}/agent_test_{timestamp}.log"
        self.results_file = f"{log_dir}/agent_test_results_{timestamp}.json"
        
        # Configure logging
        self._setup_logging()
        
        self.logger.info(f"Test logger initialized. Log file: {self.log_file}")
    
    def _setup_logging(self):
        """Configure the logging system."""
        self.logger = logging.getLogger("agent_test")
        self.logger.setLevel(self.log_level)
        
        # Clean any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(self.log_level)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        
        # Create formatter and add it to handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def start_test_suite(self):
        """Mark the beginning of a test suite."""
        self.results["start_time"] = datetime.datetime.now().isoformat()
        self.logger.info("====== Starting Agent Test Suite ======")
    
    def log_test_start(self, test_id: int, position: Dict[str, Any]):
        """
        Log the start of a test.
        
        Args:
            test_id: Unique identifier for the test
            position: Test position configuration
        """
        self.logger.info(f"Starting test #{test_id} with position: {position}")
        self.results["total_tests"] += 1
    
    def log_test_success(self, test_id: int, result: Any):
        """
        Log a successful test.
        
        Args:
            test_id: Unique identifier for the test
            result: Result of the test
        """
        self.logger.info(f"Test #{test_id} SUCCEEDED with result: {result}")
        self.results["successful_tests"] += 1
    
    def log_test_failure(self, test_id: int, error: Exception, context: Dict[str, Any] = None):
        """
        Log a failed test with error details.
        
        Args:
            test_id: Unique identifier for the test
            error: Exception that caused the failure
            context: Additional context about the test
        """
        error_msg = str(error)
        error_type = type(error).__name__
        
        self.logger.error(f"Test #{test_id} FAILED: {error_type} - {error_msg}")
        
        if context:
            self.logger.error(f"Test context: {context}")
        
        # Add to failure list
        failure_entry = {
            "test_id": test_id,
            "error_type": error_type,
            "error_message": error_msg,
            "context": context or {}
        }
        self.results["failures"].append(failure_entry)
        self.results["failed_tests"] += 1
    
    def end_test_suite(self):
        """Mark the end of a test suite and generate summary."""
        self.results["end_time"] = datetime.datetime.now().isoformat()
        
        # Calculate duration
        start = datetime.datetime.fromisoformat(self.results["start_time"])
        end = datetime.datetime.fromisoformat(self.results["end_time"])
        self.results["duration_seconds"] = (end - start).total_seconds()
        
        # Log summary
        success_rate = 0
        if self.results["total_tests"] > 0:
            success_rate = (self.results["successful_tests"] / self.results["total_tests"]) * 100
        
        self.logger.info("====== Agent Test Suite Complete ======")
        self.logger.info(f"Total tests: {self.results['total_tests']}")
        self.logger.info(f"Successful tests: {self.results['successful_tests']}")
        self.logger.info(f"Failed tests: {self.results['failed_tests']}")
        self.logger.info(f"Success rate: {success_rate:.2f}%")
        self.logger.info(f"Total duration: {self.results['duration_seconds']:.2f} seconds")
        
        # Group failures by error type for easier analysis
        if self.results["failures"]:
            error_types = {}
            for failure in self.results["failures"]:
                error_type = failure["error_type"]
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(failure)
            
            self.logger.info("Failure summary by error type:")
            for error_type, failures in error_types.items():
                self.logger.info(f"  {error_type}: {len(failures)} occurrences")
        
        # Save results to JSON file
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.logger.info(f"Detailed results saved to: {self.results_file}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a dictionary summary of test results.
        
        Returns:
            Dict containing test summary statistics
        """
        return self.results


class AgentTestFramework:
    """Framework for testing browser-use agents with multiple positions."""
    
    def __init__(self, 
                 logger: Optional[TestLogger] = None,
                 browser_config: Optional[BrowserConfig] = None,
                 browser_context_config: Optional[BrowserContextConfig] = None):
        """
        Initialize the agent test framework.
        
        Args:
            logger: TestLogger instance (creates a new one if None)
            browser_config: Custom browser configuration (uses default if None)
            browser_context_config: Custom browser context config (uses default if None)
        """
        self.logger = logger or TestLogger()
        self.browser_config = browser_config or BrowserConfig(
            headless=True  # Use headless by default for testing
        )
        self.browser_context_config = browser_context_config or BrowserContextConfig(
            highlight_elements=False  # Disable highlighting for tests
        )
    
    async def run_tests(self, 
                       positions: List[Dict[str, Any]], 
                       agent_factory: Callable[[Browser, BrowserContext, Dict[str, Any]], Agent],
                       max_steps_per_test: int = 20,
                       parallel_tests: int = 1):
        """
        Run tests on multiple positions.
        
        Args:
            positions: List of position configurations to test
            agent_factory: Function that creates an agent from browser, context and position
            max_steps_per_test: Maximum number of steps per test
            parallel_tests: Number of tests to run in parallel (use with caution)
            
        Returns:
            Test results summary
        """
        self.logger.start_test_suite()
        
        # Run tests sequentially for now
        # TODO: Add parallel test support when needed
        for i, position in enumerate(positions):
            test_id = i + 1
            self.logger.log_test_start(test_id, position)
            
            try:
                # Create fresh browser for each test
                browser = Browser(config=self.browser_config)
                context = BrowserContext(
                    browser=browser,
                    config=self.browser_context_config
                )
                
                # Create agent using factory function
                agent = agent_factory(browser, context, position)
                
                # Run the agent
                result = await agent.run(max_steps=max_steps_per_test)
                
                # Log success
                self.logger.log_test_success(test_id, result)
                
            except Exception as e:
                # Log failure with context
                self.logger.log_test_failure(test_id, e, context={"position": position})
            
            finally:
                # Ensure browser is closed
                try:
                    await browser.close()
                except Exception as e:
                    self.logger.logger.warning(f"Error closing browser: {e}")
        
        self.logger.end_test_suite()
        return self.logger.get_summary()


async def generate_test_positions(num_positions: int = 100, recent_percentage: float = 10.0) -> List[Dict[str, Any]]:
    """
    Generate test positions for the agent.
    
    Args:
        num_positions: Number of test positions to generate
        recent_percentage: Percentage of newest jobs to include (1-100)
        
    Returns:
        List of position configurations
    """
    positions = []
    
    try:
        # Import the sampling module
        from sample_recent_jobs import sample_recent_jobs
        
        # Generate a fresh sample of the most recent jobs
        # Use percentage for filtering but exact count for limiting
        sample_recent_jobs(percentage=recent_percentage, count=num_positions)
        
        # Load the sample URLs from the JSON file
        with open('sample_urls.json', 'r') as f:
            urls = json.load(f)
        
        # Create positions from the URLs
        for i in range(min(num_positions, len(urls))):
            position = {
                "id": i,
                "url": urls[i],
                # Add additional parameters based on your testing needs
                "parameters": {
                    "param1": f"value_{i}",
                    "param2": i % 5
                }
            }
            positions.append(position)
    except Exception as e:
        # Fallback to example.com if there's an error loading the URLs
        logging.warning(f"Error loading or sampling URLs: {e}. Using fallback URLs.")
        for i in range(num_positions):
            position = {
                "id": i,
                "url": "https://example.com",
                "parameters": {
                    "param1": f"value_{i}",
                    "param2": i % 5
                }
            }
            positions.append(position)
    
    return positions


async def run_agent_tests(
    num_positions: int = 100,
    agent_factory: Optional[Callable] = None,
    browser_config: Optional[BrowserConfig] = None,
    browser_context_config: Optional[BrowserContextConfig] = None,
    log_dir: str = "logs",
    max_steps_per_test: int = 20,
    parallel_tests: int = 1,
    recent_percentage: float = 10.0
) -> Dict[str, Any]:
    """
    Run a complete test suite for an agent.
    
    Args:
        num_positions: Number of test positions to generate
        agent_factory: Function to create agent instances
        browser_config: Custom browser configuration
        browser_context_config: Custom browser context configuration
        log_dir: Directory to store logs
        max_steps_per_test: Maximum steps per test
        parallel_tests: Number of tests to run in parallel
        
    Returns:
        Test results summary
    """
    # Create logger
    logger = TestLogger(log_dir=log_dir)
    
    # Create test framework
    framework = AgentTestFramework(
        logger=logger,
        browser_config=browser_config,
        browser_context_config=browser_context_config
    )
    
    # Generate test positions
    positions = await generate_test_positions(num_positions, recent_percentage)
    
    # Default agent factory if none provided
    if agent_factory is None:
        def default_agent_factory(browser, context, position):
            from browser_use import Agent
            # Create a default agent - modify as needed for your specific agent
            return Agent(
                browser_context=context,
                task=f"Navigate to {position.get('url', 'https://example.com')} and perform basic interactions",
                max_actions_per_step=4
            )
        agent_factory = default_agent_factory
    
    # Run tests
    results = await framework.run_tests(
        positions=positions,
        agent_factory=agent_factory,
        max_steps_per_test=max_steps_per_test,
        parallel_tests=parallel_tests
    )
    
    return results


# Example usage with cookie_agent2_v1.py as the execution core
async def main(num_positions=10, parallel_tests=4, headless=False, max_steps_per_test=20, recent_percentage=10.0):
    # Import the custom agent module
    import yaml
    import os
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI
    from browser_use import Agent
    
    # Load environment variables and prompt
    load_dotenv()
    with open("prompt.yaml", "r", encoding="utf-8") as f:
        prompt_data = yaml.safe_load(f)
        agent_task_template = prompt_data["agent_task"]
    
    # Custom agent factory that uses cookie_agent2_v1 approach
    def cookie_agent_factory(browser, context, position):
        # Customize the task with the URL from the test position
        job_url = position.get('url')
        
        # Create a custom task using the template from prompt.yaml
        # But replace the URL with the one from the test position
        task = agent_task_template.replace("https://q.yingjiesheng.com/jobdetail/157805378.html", job_url)
        
        # Prepend navigation instructions to the task
        task = f"First, navigate to {job_url} to access the job application.\n\n" + task
        
        # Create LLM (same as cookie_agent2_v1.py)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set the OPENAI_API_KEY environment variable")
        
        llm = ChatOpenAI(model="gpt-4.1")
        
        # Create agent with the same configuration as cookie_agent2_v1.py
        return Agent(
            browser_context=context,
            task=task,
            llm=llm,
            max_actions_per_step=4
        )
    
    # Create browser configuration with headless parameter
    browser_config = BrowserConfig(
        headless=headless  # Set based on command line argument
    )
    
    # Create browser context config matching cookie_agent2_v1.py
    browser_context_config = BrowserContextConfig(
        highlight_elements=True,
        viewport_expansion=1000,
        cookies_file="temp_cookies.json"  # Use the same cookies file as in cookie_agent2_v1.py
    )
    
    # Run tests with sampled job URLs using command line parameters
    results = await run_agent_tests(
        num_positions=num_positions,
        agent_factory=cookie_agent_factory,
        browser_config=browser_config,
        browser_context_config=browser_context_config,
        max_steps_per_test=max_steps_per_test,
        parallel_tests=parallel_tests,
        recent_percentage=recent_percentage
    )
    
    print(f"Tests completed with {results['successful_tests']}/{results['total_tests']} successes")


if __name__ == "__main__":
    asyncio.run(main())
