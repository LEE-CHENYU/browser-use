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
import csv
import base64
from typing import List, Dict, Any, Optional, Tuple, Callable

from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.agent.views import ActionResult

# Import the custom agent module
import cookie_agent2_v1


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
            "test_details": [],
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0
        }
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate timestamped filenames
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"{log_dir}/agent_test_{self.timestamp}.log"
        self.results_file = f"{log_dir}/agent_test_results_{self.timestamp}.json"
        self.details_csv = f"{log_dir}/agent_test_details_{self.timestamp}.csv"
        self.intermediate_file = f"{log_dir}/agent_test_intermediate_{self.timestamp}.json"
        
        # Configure logging
        self._setup_logging()
        
        # Initialize CSV file with headers for incremental logging
        self._init_csv_file()
        
        self.logger.info(f"Test logger initialized. Log file: {self.log_file}")
        self.logger.info(f"Intermediate results will be saved to: {self.intermediate_file}")
    
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
    
    def _init_csv_file(self):
        """Initialize the CSV file with headers."""
        # Define CSV headers
        self.csv_headers = [
            "test_id", "timestamp", "url", "position", "success", "failure_reason", 
            "is_one_click", "login_failure"
        ]
        
        with open(self.details_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
            writer.writeheader()
    
    def _append_to_csv(self, test_details: Dict[str, Any]):
        """Append a single test result to the CSV file."""
        with open(self.details_csv, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
            # Extract only the fields we want for the CSV
            row = {field: test_details.get(field, "") for field in self.csv_headers}
            writer.writerow(row)
    
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
    
    def log_test_success(self, test_id: int, result: Any, position: Dict[str, Any], metrics: Dict[str, Any] = None):
        """
        Log a successful test with detailed metrics.
        
        Args:
            test_id: Unique identifier for the test
            result: Result of the test
            position: The position configuration
            metrics: Additional metrics about the test (one-click, etc.)
        """
        self.logger.info(f"Test #{test_id} SUCCEEDED with result: {result}")
        self.results["successful_tests"] += 1
        
        # Prepare test details
        url = position.get('url', 'unknown')
        position_name = position.get('position_name', position.get('parameters', {}).get('param1', 'unknown'))
        
        # Default metrics if none provided
        if metrics is None:
            metrics = {}
        
        test_details = {
            "test_id": test_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "url": url,
            "position": position_name,
            "success": True,
            "failure_reason": None,
            "is_one_click": metrics.get("is_one_click", False),
            "login_failure": metrics.get("login_failure", False),
            "additional_metrics": metrics
        }
        
        # Add to test details list
        self.results["test_details"].append(test_details)
        
        # Append to CSV file immediately
        self._append_to_csv(test_details)
        
        # Periodically save JSON results for recovery
        if test_id % 5 == 0:
            self._save_interim_json_results()
    
    def log_test_failure(self, test_id: int, error: Exception, context: Dict[str, Any] = None, metrics: Dict[str, Any] = None):
        """
        Log a failed test with error details and metrics.
        
        Args:
            test_id: Unique identifier for the test
            error: Exception that caused the failure
            context: Additional context about the test
            metrics: Additional metrics about the test (one-click, etc.)
        """
        error_msg = str(error)
        error_type = type(error).__name__
        
        self.logger.error(f"Test #{test_id} FAILED: {error_type} - {error_msg}")
        
        if context:
            self.logger.error(f"Test context: {context}")
        
        # Generate a more user-friendly failure reason using the error message
        failure_reason = self._generate_failure_reason(error_msg, error_type)
        
        # Extract position info from context
        position = context.get("position", {}) if context else {}
        url = position.get('url', 'unknown')
        position_name = position.get('position_name', position.get('parameters', {}).get('param1', 'unknown'))
        
        # Default metrics if none provided
        if metrics is None:
            metrics = {}
        
        # Add to failure list
        failure_entry = {
            "test_id": test_id,
            "error_type": error_type,
            "error_message": error_msg,
            "failure_reason": failure_reason,
            "context": context or {},
            "timestamp": datetime.datetime.now().isoformat(),
            "url": url,
            "position": position_name,
            "is_one_click": metrics.get("is_one_click", False),
            "login_failure": metrics.get("login_failure", False)
        }
        self.results["failures"].append(failure_entry)
        
        # Add to test details list for consistent reporting
        test_details = {
            "test_id": test_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "url": url,
            "position": position_name,
            "success": False,
            "failure_reason": failure_reason,
            "is_one_click": metrics.get("is_one_click", False),
            "login_failure": metrics.get("login_failure", False),
            "additional_metrics": metrics
        }
        self.results["test_details"].append(test_details)
        
        # Append to CSV file immediately
        self._append_to_csv(test_details)
        
        self.results["failed_tests"] += 1
        
        # Periodically save JSON results for recovery
        if test_id % 5 == 0:
            self._save_interim_json_results()
    
    def _save_interim_json_results(self):
        """Save intermediate JSON results for recovery purposes."""
        try:
            # Use the specific naming format requested
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            interim_file = f"{self.log_dir}/agent_test_intermediate_{current_time}.json"
            
            # Also save to the original intermediate file path for consistency
            with open(self.intermediate_file, 'w') as f:
                json.dump(self.results, f, indent=2)
                
            # Save with current timestamp for historical tracking
            with open(interim_file, 'w') as f:
                json.dump(self.results, f, indent=2)
                
            self.logger.info(f"Saved intermediate results to: {interim_file}")
        except Exception as e:
            self.logger.warning(f"Failed to save interim results: {e}")
    
    def _generate_failure_reason(self, error_msg: str, error_type: str) -> str:
        """
        Generate a user-friendly failure reason from the error message.
        
        Args:
            error_msg: The error message
            error_type: The type of error
            
        Returns:
            A user-friendly reason for the failure
        """
        # Common patterns and their user-friendly descriptions
        if "timeout" in error_msg.lower():
            return "Operation timed out - the page or element may have taken too long to load"
        elif "element not found" in error_msg.lower() or "no element" in error_msg.lower():
            return "Required element not found on the page - the page structure may have changed"
        elif "navigation" in error_msg.lower() and "failed" in error_msg.lower():
            return "Failed to navigate to the page - the URL may be invalid or the site may be down"
        elif "permission" in error_msg.lower() or "access denied" in error_msg.lower():
            return "Permission denied - the agent may not have access to perform this operation"
        elif "login" in error_msg.lower() and ("failed" in error_msg.lower() or "error" in error_msg.lower()):
            return "Login failed - credentials may be invalid or login flow has changed"
        elif "captcha" in error_msg.lower():
            return "CAPTCHA detected - automated access was blocked by security measures"
        elif "connection" in error_msg.lower() and "closed" in error_msg.lower():
            return "Connection closed unexpectedly - the site may have terminated the session"
        
        # Default to a generic message based on the error type
        return f"Operation failed due to a {error_type.lower().replace('error', '').strip()} issue"
    
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
        
        # Save detailed results to JSON file
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # CSV is already being written incrementally, so we don't need this method anymore
        # self._export_test_details_to_csv()
        
        self.logger.info(f"Detailed results saved to: {self.results_file}")
        self.logger.info(f"Test details saved to: {self.details_csv}")
    
    def _export_test_details_to_csv(self):
        """
        Export test details to a CSV file for easier analysis.
        This method is kept for backwards compatibility but is no longer needed as 
        results are written incrementally after each test.
        """
        pass
    
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
        
        # Directory to store screenshots under a run-specific timestamp subfolder
        base_ss_dir = os.path.join(self.logger.log_dir, "screenshots")
        run_ts = self.logger.timestamp
        self.screenshot_dir = os.path.join(base_ss_dir, run_ts)
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    # ---------------------------------------------------------------------
    # Screenshot helpers
    # ---------------------------------------------------------------------

    def _save_screenshot(self, screenshot_b64: str, test_id: int, stage: str) -> Optional[str]:
        """Decode a base64 screenshot and save it to the screenshot directory.

        Args:
            screenshot_b64: The base64 encoded screenshot.
            test_id: The current test id.
            stage: Descriptive stage name (e.g., 'login', 'final', 'error', 'step_001').

        Returns:
            Path to the saved screenshot or ``None`` if saving failed.
        """
        if not screenshot_b64:
            return None

        try:
            file_path = os.path.join(self.screenshot_dir, f"test_{test_id}_{stage}.png")
            with open(file_path, 'wb') as fp:
                fp.write(base64.b64decode(screenshot_b64))
            # Log the saved path for reference
            self.logger.logger.info(f"Saved screenshot to: {file_path}")
            return file_path
        except Exception as e:
            self.logger.logger.warning(f"Failed to save screenshot for test #{test_id} ({stage}): {e}")
            return None
    
    async def run_tests(self, 
                       positions: List[Dict[str, Any]], 
                       agent_factory: Callable[[Browser, BrowserContext, Dict[str, Any]], Agent],
                       page_preprocessor: Optional[Callable[[BrowserContext, Dict[str, Any]], Any]] = None,
                       max_steps_per_test: int = 20,
                       parallel_tests: int = 1,
                       record_every_step: bool = False):
        """
        Run tests on multiple positions.
        
        Args:
            positions: List of position configurations to test
            agent_factory: Function that creates an agent from browser, context and position
            page_preprocessor: Optional function to preprocess the page before creating the agent
            max_steps_per_test: Maximum number of steps per test
            parallel_tests: Number of tests to run in parallel (use with caution)
            record_every_step: If ``True``, save screenshots of every step in the agent's history.
            
        Returns:
            Test results summary
        """
        self.logger.start_test_suite()
        
        # Run tests sequentially for now
        # TODO: Add parallel test support when needed
        for i, position in enumerate(positions):
            test_id = i + 1
            self.logger.log_test_start(test_id, position)
            
            # Initialize metrics
            metrics = {
                "is_one_click": False,
                "login_failure": False,
                "steps_taken": 0,
                "elements_clicked": 0,
                "forms_filled": 0,
                "pages_navigated": 0
            }
            
            try:
                # Create fresh browser for each test
                browser = Browser(config=self.browser_config)
                context = BrowserContext(
                    browser=browser,
                    config=self.browser_context_config
                )
                
                # Run preprocessor if provided
                if page_preprocessor:
                    try:
                        preprocess_result = await page_preprocessor(context, position)
                        if isinstance(preprocess_result, dict) and "is_one_click" in preprocess_result:
                            metrics["is_one_click"] = preprocess_result["is_one_click"]
                    except Exception as e:
                        if "login" in str(e).lower() and "fail" in str(e).lower():
                            metrics["login_failure"] = True
                        raise e
                
                # Take an initial/login screenshot after potential navigation in preprocessor
                try:
                    login_ss = await context.take_screenshot(full_page=True)
                    self._save_screenshot(login_ss, test_id, "login")
                except Exception as e:
                    self.logger.logger.warning(f"Test #{test_id}: could not capture login screenshot: {e}")
                
                # Create agent using factory function
                agent = agent_factory(browser, context, position)
                
                # Run the agent
                result = await agent.run(max_steps=max_steps_per_test)
                
                # Update metrics with information from the agent run
                if hasattr(agent, 'steps_taken'):
                    metrics["steps_taken"] = agent.steps_taken
                
                # Extract additional metrics from the agent's observations if available
                try:
                    # Count form interactions
                    for step in agent.steps:
                        if 'action' in step and 'observations' in step:
                            if any(x in step['action'].lower() for x in ['click', 'press']):
                                metrics["elements_clicked"] += 1
                            if any(x in step['action'].lower() for x in ['type', 'fill']):
                                metrics["forms_filled"] += 1
                            if 'navigate' in step['action'].lower():
                                metrics["pages_navigated"] += 1
                            
                            # Check for login failures
                            if 'login' in step['action'].lower() and any(x in str(step['observations']).lower() for x in ['failed', 'error', 'incorrect']):
                                metrics["login_failure"] = True
                            
                            # Check for one-click applications
                            if any(x in step['action'].lower() for x in ['apply', 'submit', 'click']) and any(x in str(step['observations']).lower() for x in ['success', 'applied', 'application submitted']):
                                metrics["is_one_click"] = True
                except (AttributeError, KeyError):
                    # If the agent doesn't have steps or they don't have the expected structure, just continue
                    pass
                
                # Check if the agent completed successfully
                success_status = agent.history.is_successful()
                
                # Add detailed logging about the success status
                self.logger.logger.info(f"Test #{test_id} success status: {success_status}")
                try:
                    if agent.history.history and agent.history.history[-1].result:
                        last_result = agent.history.history[-1].result[-1]
                        if last_result.is_done:
                            self.logger.logger.info(f"Test #{test_id} is marked as done: {last_result.is_done}")
                        if last_result.success is not None:
                            self.logger.logger.info(f"Test #{test_id} has success flag: {last_result.success}")
                        if last_result.extracted_content:
                            self.logger.logger.info(f"Test #{test_id} last result content: {last_result.extracted_content[:100]}...")
                        elif last_result.error:
                            self.logger.logger.info(f"Test #{test_id} last result error: {last_result.error}")
                except (AttributeError, IndexError) as e:
                    self.logger.logger.warning(f"Test #{test_id} couldn't extract detailed result info: {e}")
                
                if success_status is True:
                    # Capture final state screenshot before logging success
                    try:
                        final_ss = None
                        if agent.history.history and agent.history.history[-1].state.screenshot:
                            final_ss = agent.history.history[-1].state.screenshot
                        else:
                            final_ss = await context.take_screenshot(full_page=True)
                        self._save_screenshot(final_ss, test_id, "final")
                    except Exception as e:
                        self.logger.logger.warning(f"Test #{test_id}: could not capture final screenshot: {e}")

                    # Optionally save every step's screenshot
                    if record_every_step:
                        for idx, ss in enumerate(agent.history.screenshots(), start=1):
                            if ss:
                                self._save_screenshot(ss, test_id, f"step_{idx:03d}")

                    self.logger.log_test_success(test_id, result, position, metrics)
                else:
                    # Create error message based on success status
                    if success_status is False:
                        # Agent explicitly marked the task as failed
                        error_msg = "Agent marked the task as unsuccessful"
                        try:
                            # Try to extract the last result message for more context
                            if agent.history.history and agent.history.history[-1].result:
                                last_result = agent.history.history[-1].result[-1]
                                if last_result.extracted_content:
                                    error_msg = f"Agent reported failure: {last_result.extracted_content}"
                                elif last_result.error:
                                    error_msg = f"Agent error: {last_result.error}"
                        except (AttributeError, IndexError):
                            pass
                        
                        error = Exception(error_msg)
                    else:  # success_status is None
                        # Agent didn't mark the task as done
                        error = Exception("Agent did not complete the task within the maximum steps")
                    
                    # Capture error screenshot before logging failure
                    try:
                        error_ss = await context.take_screenshot(full_page=True)
                        self._save_screenshot(error_ss, test_id, "error")
                    except Exception as e:
                        self.logger.logger.warning(f"Test #{test_id}: could not capture error screenshot: {e}")

                    # Optionally save every step's screenshot even on failure
                    if record_every_step:
                        for idx, ss in enumerate(agent.history.screenshots(), start=1):
                            if ss:
                                self._save_screenshot(ss, test_id, f"step_{idx:03d}")

                    # Log failure with context and metrics
                    self.logger.log_test_failure(test_id, error, context={"position": position}, metrics=metrics)
                
            except Exception as e:
                # Attempt to take screenshot on unexpected exception
                try:
                    exc_ss = await context.take_screenshot(full_page=True)
                    self._save_screenshot(exc_ss, test_id, "error")
                except Exception as e2:
                    self.logger.logger.warning(f"Test #{test_id}: could not capture screenshot during exception: {e2}")

                # Log failure with context and metrics
                self.logger.log_test_failure(test_id, e, context={"position": position}, metrics=metrics)
            
            finally:
                # Ensure browser is closed
                try:
                    await browser.close()
                except Exception as e:
                    self.logger.logger.warning(f"Error closing browser: {e}")
        
        self.logger.end_test_suite()
        return self.logger.get_summary()


async def generate_test_positions(num_positions: int = 100, recent_percentage: float = 10.0, input_file: str = "extracted_job_details.json", headless: bool = True, random_sampling: bool = False) -> List[Dict[str, Any]]:
    """
    Generate test positions for the agent.
    
    Args:
        num_positions: Number of test positions to generate
        recent_percentage: Percentage of jobs to include (1-100)
        input_file: Input file for extracted job details
        headless: Whether to run in headless mode
        random_sampling: Whether to use random sampling instead of date-based sampling
        
    Returns:
        List of position configurations
    """
    positions = []
    
    try:
        # Import the sampling module
        from sample_recent_jobs import sample_recent_jobs
        
        # Generate a sample of job URLs
        sample_recent_jobs(
            percentage=recent_percentage, 
            count=num_positions, 
            input_file=input_file, 
            headless=headless,
            random_sampling=random_sampling
        )
        
        # Load the sample URLs from the JSON file
        with open('browser-use/sample_urls.json', 'r') as f:
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
    page_preprocessor: Optional[Callable] = None,
    browser_config: Optional[BrowserConfig] = None,
    browser_context_config: Optional[BrowserContextConfig] = None,
    log_dir: str = "logs",
    max_steps_per_test: int = 20,
    parallel_tests: int = 1,
    recent_percentage: float = 10.0,
    input_file: str = "extracted_job_details.json",
    headless: bool = True,
    random_sampling: bool = False,
    record_every_step: bool = False
) -> Dict[str, Any]:
    """
    Run a complete test suite for an agent.
    
    Args:
        num_positions: Number of test positions to generate
        agent_factory: Function to create agent instances
        page_preprocessor: Optional function to preprocess the page before creating the agent
        browser_config: Custom browser configuration
        browser_context_config: Custom browser context configuration
        log_dir: Directory to store logs
        max_steps_per_test: Maximum steps per test
        parallel_tests: Number of tests to run in parallel
        recent_percentage: Percentage of jobs to include
        input_file: Input file for extracted job details
        headless: Whether to run in headless mode
        random_sampling: Whether to use random sampling instead of date-based sampling
        record_every_step: If ``True``, save screenshots of every step in the agent's history
        
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
    positions = await generate_test_positions(
        num_positions, 
        recent_percentage, 
        input_file=input_file, 
        headless=headless,
        random_sampling=random_sampling
    )
    
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
        page_preprocessor=page_preprocessor,
        max_steps_per_test=max_steps_per_test,
        parallel_tests=parallel_tests,
        record_every_step=record_every_step
    )
    
    return results


# Example usage with cookie_agent2_v1.py as the execution core
async def main(num_positions=10, parallel_tests=4, headless=False, max_steps_per_test=20, recent_percentage=10.0, input_file="extracted_job_details.json", random_sampling=False, record_every_step=False):
    # Import necessary modules
    import yaml
    import os
    
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI
    from browser_use import Agent, Controller
    from browser_use.agent.views import ActionResult
    
    # Load environment variables
    load_dotenv()
    
    # Define the resume file path
    resume_folder = "/Users/chenyusu/vscode/jobseeker/happyhunting_app/browser-use/resume"
    if os.path.exists(resume_folder):
        docx_files = [f for f in os.listdir(resume_folder) if f.endswith('.docx')]
        resume_file_path = os.path.join(resume_folder, docx_files[0]) if docx_files else None
    else:
        resume_file_path = None
    
    # Fallback to the path specified in cookie_agent2_v1.py if no files found
    if not resume_file_path:
        resume_file_path = "/Users/chenyusu/Documents/GitHub/browser-use/李宸宇简历.docx"
    
    # Verify the file exists
    if not os.path.exists(resume_file_path):
        print(f"ERROR: Resume file does not exist at: {resume_file_path}")
        resume_file_path = input("Please enter the correct path to your resume file: ")
        if not os.path.exists(resume_file_path):
            print(f"ERROR: Resume file still does not exist at: {resume_file_path}")
            return
    
    # Create a controller with custom file upload action
    controller = Controller()
    
    @controller.action('Upload file to interactive element with file path')
    async def upload_file(index: int, path: str, browser: BrowserContext, available_file_paths: list[str]):
        if path not in available_file_paths:
            return ActionResult(error=f'File path {path} is not available')

        if not os.path.exists(path):
            return ActionResult(error=f'File {path} does not exist')

        try:
            dom_el = await browser.get_dom_element_by_index(index)
            file_upload_dom_el = dom_el.get_file_upload_element()

            if file_upload_dom_el is None:
                msg = f'No file upload element found at index {index}'
                print(msg)
                return ActionResult(error=msg)

            file_upload_el = await browser.get_locate_element(file_upload_dom_el)

            if file_upload_el is None:
                msg = f'No file upload element found at index {index}'
                print(msg)
                return ActionResult(error=msg)

            await file_upload_el.set_input_files(path)
            msg = f'Successfully uploaded file to index {index}'
            print(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)
        except Exception as e:
            msg = f'Failed to upload file to index {index}: {str(e)}'
            print(msg)
            return ActionResult(error=msg)
    
    # Page preprocessor that implements the job application button click from cookie_agent2_v1.py
    async def cookie_agent_page_preprocessor(context, position):
        job_url = position.get('url')
        
        # Initialize metrics
        metrics = {
            "is_one_click": False,
            "login_failure": False
        }
        
        # Get session and navigate to the URL
        session = await context.get_session()
        page = await context.get_current_page()
        
        print(f"Navigating to job listing: {job_url}")
        await page.goto(job_url)
        
        # Wait for page to load
        await page.wait_for_load_state("networkidle")
        
        # Find and click the apply button directly
        print("Looking for the apply button...")
        
        # Try multiple possible selectors for the button
        apply_button = await page.query_selector('div.delivery-btn')
        if not apply_button:
            apply_button = await page.query_selector('button:has-text("立即申请")')
        if not apply_button:
            apply_button = await page.query_selector('a:has-text("立即申请")')
        if not apply_button:
            # Try a more generic approach
            one_click_available = await page.evaluate("""() => {
                const elements = Array.from(document.querySelectorAll('*'));
                for (const element of elements) {
                    if (element.textContent.trim() === '立即申请') {
                        element.style.border = '3px solid red';
                        element.click();
                        return true;
                    }
                }
                return false;
            }""")
            if one_click_available:
                metrics["is_one_click"] = True
        else:
            print("Apply button found, clicking...")
            await apply_button.click()
            metrics["is_one_click"] = True
        
        # Wait a moment for any redirects or form loads
        await asyncio.sleep(2)
        
        # Check if we're on a login page after clicking apply
        current_url = page.url
        if "login" in current_url.lower() or await page.query_selector('form[action*="login"]') or await page.query_selector('input[type="password"]'):
            print("Login page detected after clicking apply")
            metrics["login_detected"] = True
        
        return metrics
    
    # Simple factory that creates the agent with the exact same configuration as cookie_agent2_v1.py
    def cookie_agent_factory(browser, context, position):
        # Load the task from prompt.yaml with absolute path
        prompt_yaml_path = os.path.join("/Users/chenyusu/vscode/jobseeker/happyhunting_app/browser-use", "prompt.yaml")
        with open(prompt_yaml_path, "r", encoding="utf-8") as f:
            prompt_data = yaml.safe_load(f)
        agent_task = prompt_data["agent_task"]
        
        # Replace placeholder in the task with actual file path
        agent_task = agent_task.replace("{resume_file_path}", resume_file_path)
        
        # Create LLM exactly as in cookie_agent2_v1.py
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set the OPENAI_API_KEY environment variable")
        
        llm = ChatOpenAI(model="gpt-4.1")
        
        # Print the task for debugging
        print(f"Agent task: {agent_task[:100]}...")
        
        # Create agent with exactly the same configuration as cookie_agent2_v1.py
        # but with file upload capabilities
        return Agent(
            browser_context=context,
            task=agent_task,
            llm=llm,
            max_actions_per_step=4,
            available_file_paths=[resume_file_path],  # Make resume file available for upload
            controller=controller  # Use custom controller with file upload action
        )
    
    # Use the exact same browser configuration as in cookie_agent2_v1.py
    browser_config = BrowserConfig(
        headless=headless  # Configurable through command line
    )
    
    # Use the exact same browser context config as in cookie_agent2_v1.py
    # Match cookie_agent2_v1.py's cookie handling exactly
    cookies_dir = "/Users/chenyusu/vscode/jobseeker/happyhunting_app/browser-use/cookies"
    cookies_files = [f for f in os.listdir(cookies_dir) if f.endswith('.json')]
    cookies_file = os.path.join(cookies_dir, cookies_files[0]) if cookies_files else "temp_cookies.json"
    
    # Print resolved cookie file path for debugging
    print(f"Using cookies file: {os.path.abspath(cookies_file)}")
    
    browser_context_config = BrowserContextConfig(
        highlight_elements=True,
        viewport_expansion=1000,
        cookies_file=cookies_file
    )
    
    # Run tests with the cookie_agent2_v1 configuration
    results = await run_agent_tests(
        num_positions=num_positions,
        agent_factory=cookie_agent_factory,
        page_preprocessor=cookie_agent_page_preprocessor,
        browser_config=browser_config,
        browser_context_config=browser_context_config,
        max_steps_per_test=max_steps_per_test,
        parallel_tests=parallel_tests,
        recent_percentage=recent_percentage,
        input_file=input_file,
        headless=headless,
        random_sampling=random_sampling,
        record_every_step=record_every_step
    )
    
    print(f"Tests completed with {results['successful_tests']}/{results['total_tests']} successes")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Agent Test Framework CLI")
    parser.add_argument("--num_positions", type=int, default=10, help="Number of test positions to generate")
    parser.add_argument("--parallel_tests", type=int, default=4, help="Number of tests to run in parallel")
    parser.add_argument("--headless", action="store_true", default=False, help="Run browser in headless mode (default: False)")
    parser.add_argument("--max_steps_per_test", type=int, default=20, help="Maximum steps per test")
    parser.add_argument("--recent_percentage", type=float, default=10.0, help="Percentage of jobs to include")
    parser.add_argument("--input", type=str, default="aggregated_job_details.json", help="Input file for extracted job details")
    parser.add_argument("--random", action="store_true", default=False, help="Use random sampling instead of date-based sampling")
    parser.add_argument("--record_every_step", action="store_true", default=False, help="Save screenshots for every step in the agent's history")
    args = parser.parse_args()

    asyncio.run(main(
        num_positions=args.num_positions,
        parallel_tests=args.parallel_tests,
        headless=args.headless,
        max_steps_per_test=args.max_steps_per_test,
        recent_percentage=args.recent_percentage,
        input_file=args.input,
        random_sampling=args.random,
        record_every_step=args.record_every_step
    ))
