from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContext
import asyncio
from dotenv import load_dotenv
import os
from playwright.sync_api import sync_playwright
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class BrowserAgent:
    def __init__(self, headless: bool = False, cookies_data: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the browser agent with optional cookie support
        
        Args:
            headless: Whether to run browser in headless mode
            cookies_data: List of cookies in the format Playwright expects
        """
        self.headless = headless
        self.cookies_data = cookies_data
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.logger = logging.getLogger(__name__)

    def load_cookies_from_data(self, cookies_data):
        """Convert cookies to the format Playwright expects"""
        playwright_cookies = []
        for cookie in cookies_data:
            # Playwright doesn't use these fields
            cookie_copy = cookie.copy()
            if "hostOnly" in cookie_copy:
                del cookie_copy["hostOnly"]
            if "session" in cookie_copy:
                del cookie_copy["session"]
            if "storeId" in cookie_copy:
                del cookie_copy["storeId"]
            
            # Convert sameSite to the format Playwright expects
            if "sameSite" in cookie_copy:
                if cookie_copy["sameSite"] == "unspecified":
                    del cookie_copy["sameSite"]
                elif cookie_copy["sameSite"] == "lax":
                    cookie_copy["sameSite"] = "Lax"
            
            playwright_cookies.append(cookie_copy)
        
        return playwright_cookies

    def load_cookies_from_file(self, cookies_file_path):
        """Load cookies from a JSON file"""
        with open(cookies_file_path, 'r') as f:
            cookies_data = json.load(f)
        return self.load_cookies_from_data(cookies_data)

    def start(self):
        """Start the browser and load cookies if provided"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        
        # Create a new browser context
        self.context = self.browser.new_context()
        
        # Add cookies if available
        if self.cookies_data:
            self.logger.info(f"Loading {len(self.cookies_data)} cookies")
            cookies = self.load_cookies_from_data(self.cookies_data)
            self.context.add_cookies(cookies)
        
        # Create page
        self.page = self.context.new_page()
        self.logger.info("Browser started successfully")
        
    def navigate(self, url: str, wait_for_load: bool = True):
        """Navigate to a URL and optionally wait for the page to load"""
        self.logger.info(f"Navigating to {url}")
        self.page.goto(url)
        
        if wait_for_load:
            self.page.wait_for_load_state("networkidle")
    
    def check_login_status(self, selector: str = "text=我的应届生") -> bool:
        """Check if we're logged in by looking for elements that would only appear when logged in"""
        return self.page.is_visible(selector)
    
    def run_agent_logic(self):
        """Implement your agent logic here"""
        # Example agent actions:
        self.logger.info("Agent is running...")
        
        # Extract information from the page
        title = self.page.title()
        self.logger.info(f"Page title: {title}")
        
        # Perform some actions (example)
        # self.page.click("a.some-link")
        # self.page.fill("input.search-box", "search term")
        # self.page.press("input.search-box", "Enter")
        
        # Add your agent's specific logic here
        
        return title

    def execute(self, url: str, login_check_selector: str = "text=我的应届生"):
        """Main method to execute agent logic"""
        try:
            # Start the browser with cookies
            self.start()
            
            # Navigate to the target site
            self.navigate(url)
            
            # Check login status
            logged_in = self.check_login_status(login_check_selector)
            self.logger.info(f"Logged in: {logged_in}")
            
            if not logged_in:
                self.logger.warning("Not logged in, authentication may be required")
            
            # Execute agent-specific logic here
            return self.run_agent_logic()
            
        except Exception as e:
            self.logger.error(f"Error during agent execution: {e}")
            return None
    
    def close(self):
        """Close the browser and playwright"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.logger.info("Browser closed")

async def main():
    # Make sure you have your OpenAI API key in your .env file
    if not os.getenv("OPENAI_API_KEY"):
        print("Please add your OPENAI_API_KEY to the .env file")
        return
    
    # Create browser config
    browser_config = BrowserConfig()
    
    # Create a browser
    browser = Browser(config=browser_config)
    
    # Create a browser context
    browser_context = BrowserContext(browser=browser)
    
    # Create an agent with a specific task to navigate yingjiesheng.com
    # Include login instructions in the task
    agent = Agent(
        task="""
        Navigate to yingjiesheng.com and explore the website. 
        
        First, if a login popup appears, close it by clicking the X button.
        
        Then, look at job listings, forums, and other features. Take screenshots of interesting pages.
        
        If you encounter any login walls, just skip those sections and explore the publicly accessible parts of the site.
        """,
        llm=ChatOpenAI(model="gpt-4o"),
        browser_context=browser_context
    )
    
    # Run the agent
    result = await agent.run()
    
    # Print the result
    print("Agent completed with result:", result)

if __name__ == "__main__":
    # Path to your cookies JSON file
    cookie_file = "cookies.json"
    
    # Initialize the agent with cookies
    agent = BrowserAgent(headless=False, cookies_data=None)
    
    # Execute agent logic with cookies loaded
    result = agent.execute(url="https://www.yingjiesheng.com/")
    if result:
        print("Agent completed with result:", result)
    else:
        print("Agent execution failed")