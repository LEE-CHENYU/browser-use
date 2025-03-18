import asyncio
import json
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def convert_cookies_to_playwright_format(cookies_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert cookies to the format Playwright expects"""
    playwright_cookies = []
    for cookie in cookies_data:
        # Create a copy of the cookie to avoid modifying the original
        cookie_copy = cookie.copy()
        
        # Remove fields not used by Playwright
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
            elif cookie_copy["sameSite"] == "strict":
                cookie_copy["sameSite"] = "Strict"
        
        playwright_cookies.append(cookie_copy)
    
    return playwright_cookies

def save_cookies_to_file(cookies_data: List[Dict[str, Any]], file_path: str) -> None:
    """Save cookies to a JSON file"""
    # Ensure directory exists
    Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
    
    # Convert cookies to Playwright format
    playwright_cookies = convert_cookies_to_playwright_format(cookies_data)
    
    # Save to file
    with open(file_path, 'w') as f:
        json.dump(playwright_cookies, f, indent=2)
    
    logger.info(f"Saved {len(playwright_cookies)} cookies to {file_path}")

async def run_agent_with_cookies(
    cookies_data: List[Dict[str, Any]], 
    task: str, 
    llm_model: str = "gpt-4o", 
    target_url: Optional[str] = None,
    cookies_file: str = "temp_cookies.json",
    headless: bool = False,
    max_steps: int = 25
):
    """
    Run a browser-use agent with pre-loaded cookies
    
    Args:
        cookies_data: List of cookies in browser extension format
        task: Task for the agent to complete
        llm_model: LLM model to use
        target_url: Optional URL to navigate to before running the agent
        cookies_file: Path to save the cookies file
        headless: Whether to run the browser in headless mode
        max_steps: Maximum number of steps for the agent to run
    """
    # Save cookies to a temporary file
    save_cookies_to_file(cookies_data, cookies_file)
    
    # Create browser configuration
    browser_config = BrowserConfig(
        headless=headless
    )
    
    # Create browser instance
    browser = Browser(config=browser_config)
    
    # Create browser context with cookies and custom highlighting config
    context = BrowserContext(
        browser=browser, 
        config=BrowserContextConfig(
            cookies_file=cookies_file,
            highlight_elements=True,
            viewport_expansion=-1
        )
    )
    
    # Initialize the LLM
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable")
    
    llm = ChatOpenAI(model=llm_model)
    
    # Create the agent with the task
    agent = Agent(
        browser_context=context,
        task=task,
        llm=llm,
        max_actions_per_step=4
    )
    
    # Find the current page and evaluate JavaScript on it
    page = await context.get_current_page()
    await page.evaluate("""() => {
      // Look specifically for the div with class "delivery-btn"
      const applyButtons = document.querySelectorAll('div.delivery-btn');
      
      // Also look for any element containing the text
      const allElements = document.querySelectorAll('*');
      const textElements = Array.from(allElements).filter(el => 
        el.textContent && el.textContent.trim() === '立即申请');
      
      // Highlight all found elements
      const elementsToHighlight = [...applyButtons, ...textElements];
      
      elementsToHighlight.forEach(element => {
        console.log('Found element:', element);
        element.style.border = '5px solid red';
        element.style.boxShadow = '0 0 15px #ff0000';
        element.style.position = 'relative';
        element.style.zIndex = '1000';
      });
    }""")
    
    # Run the agent
    result = await agent.run(max_steps=max_steps)
    
    logger.info(f"Agent completed with result: {result}")
    return result

async def main():
    # Example cookies data (from simple_cookie_browser.py)
    cookies_data = [
        {"domain": ".yingjiesheng.com", "expirationDate": 1772760264.497254, "hostOnly": False, "httpOnly": False, "name": "CookieUuid", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "8f10304c302ab8629acc6a8b1b9222e0"},
        {"domain": "www.yingjiesheng.com", "expirationDate": 1772796290.296017, "hostOnly": True, "httpOnly": False, "name": "uid", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "wKhK62ebYYJB1hZQoWCrAg=="},
        {"domain": ".yingjiesheng.com", "expirationDate": 1744769279, "hostOnly": False, "httpOnly": False, "name": "Yjs_logindata", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "{%22is51jobUserMobile%22:%221%22%2C%22isShowBind51job%22:false%2C%22isNewYJS%22:%220%22}"},
        {"domain": ".yingjiesheng.com", "expirationDate": 1744769281.137759, "hostOnly": False, "httpOnly": False, "name": "Yjs_Partner", "path": "/", "sameSite": "lax", "secure": False, "session": False, "storeId": "0", "value": ""},
        {"domain": ".yingjiesheng.com", "expirationDate": 1771630895, "hostOnly": False, "httpOnly": False, "name": "Hm_lvt_b15730ce74e116ff0df97e207706fa4a", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "1740094886"},
        {"domain": ".yingjiesheng.com", "expirationDate": 1771630896, "hostOnly": False, "httpOnly": False, "name": "Hm_lvt_a5e61e07eeae649be5a862f42c636bc7", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "1740094889"},
        {"domain": ".www.yingjiesheng.com", "expirationDate": 1773713311, "hostOnly": False, "httpOnly": False, "name": "Hm_lvt_6465b7e5e0e872fc416968a53d4fb422", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "1740067867,1741532947"},
        {"domain": ".www.yingjiesheng.com", "hostOnly": False, "httpOnly": False, "name": "HMACCOUNT", "path": "/", "sameSite": "unspecified", "secure": False, "session": True, "storeId": "0", "value": "ABE831302B97B64A"},
        {"domain": ".yingjiesheng.com", "expirationDate": 1776737310.578583, "hostOnly": False, "httpOnly": False, "name": "sensorsdata2015jssdkcross", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "%7B%22distinct_id%22%3A%22198242887%22%2C%22first_id%22%3A%228f10304c302ab8629acc6a8b1b9222e0%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24latest_landing_page%22%3A%22https%3A%2F%2Fwww.yingjiesheng.com%2F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfbG9naW5faWQiOiIxOTgyNDI4ODciLCIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk0YjRjZjJmMzcyNDFiLTBiMjI4ZTAyZjMyNWI3LTFlNTI1NjM2LTE0MDUzMjAtMTk0YjRjZjJmMzgyODUyIiwiJGlkZW50aXR5X2Fub255bW91c19pZCI6IjhmMTAzMDRjMzAyYWI4NjI5YWNjNmE4YjFiOTIyMmUwIn0%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%22198242887%22%7D%2C%22%24device_id%22%3A%22194b4cf2f37241b-0b228e02f325b7-1e525636-1405320-194b4cf2f382852%22%7D"},
        {"domain": ".yingjiesheng.com", "hostOnly": False, "httpOnly": False, "name": "YSSN", "path": "/", "sameSite": "unspecified", "secure": False, "session": True, "storeId": "0", "value": "hae58qomuj35mtpqn0abk7mt361cl5ag"},
        {"domain": ".yingjiesheng.com", "expirationDate": 1744769281.138473, "hostOnly": False, "httpOnly": False, "name": "Yjs_UAccountId", "path": "/", "sameSite": "lax", "secure": False, "session": False, "storeId": "0", "value": "198242887"},
        {"domain": ".yingjiesheng.com", "expirationDate": 1744769281.138332, "hostOnly": False, "httpOnly": True, "name": "Yjs_UToken", "path": "/", "sameSite": "lax", "secure": False, "session": False, "storeId": "0", "value": "1d062ae533ee24e7fabd4a11b37e7037"},
        {"domain": ".yingjiesheng.com", "expirationDate": 1744769311.914437, "hostOnly": False, "httpOnly": False, "name": "Yjs_Udate", "path": "/", "sameSite": "lax", "secure": False, "session": False, "storeId": "0", "value": "2021%2F10%2F10"},
        {"domain": ".www.yingjiesheng.com", "hostOnly": False, "httpOnly": False, "name": "Hm_lpvt_6465b7e5e0e872fc416968a53d4fb422", "path": "/", "sameSite": "unspecified", "secure": False, "session": True, "storeId": "0", "value": "1742177311"},
        {"domain": ".yingjiesheng.com", "expirationDate": 1757729309, "hostOnly": False, "httpOnly": False, "name": "ssxmod_itna", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "Yq0xnD2DyGDQG=oGHqGd6SiUQwp47IKGCKDsmzW9DBqxAKoDZDiqAPGhDC+RAhf2GH=zZ+ciikQAAxLrXzB8OT4Gi04exFViYxiTD4q07Db4GkDAqiOD7T4xoD4b5GwD0eG+DD4DW+qDUV7T=D7rXgUkNXWq=07TNDmb=uDGQcDitQxivqqCiZl4eqxA3uD7UVWTQDbqDuFa=3cqDL0nnaxB=uDYPFAqHCxBjNNTj3SqixakHoexLs/EDoQ4xLY7est2G=3Sh4lBEIw0GrehGHbfdBS4mxDDfYA7qxD="},
        {"domain": ".yingjiesheng.com", "expirationDate": 1757729309, "hostOnly": False, "httpOnly": False, "name": "ssxmod_itna2", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "Yq0xnD2DyGDQG=oGHqGd6SiUQwp47IKGCKDsmzWD8kP2imAxGNeeG8KxF2iV=IKGFKlGGtwKRO00QiwSPlhUk=Fb7n6Ozl1T5YicSh7Gyj1MZ70jKS4+Gv89jTNu6HzO5z5eTZXVF54GAqODKprw2q4xIDN3DH1eCFhZODkGWY7UZ9dToevzEoOHfgGWFywZ7Btb2H11cfIN8eYg1FOc=AUsbAHZx3GjZ5TmOH4NQw36xRwD/RtxEiuGO4n7hMqF5fF1OH06ZYac=0Te/iHdC0B6rIGfgFyS9yqqKc9qoTk9npL+WjqAMoKGDXRxzExlMCdOeQ3zqiQ5Dxf7K3B83BbbMKYdYQLd3Aq/Ax4ftFRYxgKKgh+qpjo8g0dw7e3YHdgYdi5NY4x4eImvjh30G+Y0mer3z7DiB1gevK0A+d8yefITxOgx4f==cdbf+eneixpmgAXb5H+Gqp1joouDmvC8=x8WgzXhwe8xwT8Ik5vi16Ci44QN3YGnay7UdiHG7PD7jk7+4dR80IrCFTlT5MGPOq1QgW34lDGcDG7=iDD="}
    ]
    
    # Define the task for the agent
    task = """
    
    Complete the job application with the following information:
    
    Education:
    - Columbia University, Master of Science in Applied Analytics (Sep 2021 - Feb 2023)
    - Shanghai Jiao Tong University, Bachelor of Arts in Japanese, Finance (Sep 2017 - Jun 2021, GPA: 3.7/4.0)
      Include: Waseda University Business School Exchange Program (Spring 2019)
    
    Professional Experience:
    - VCV Digital, Investment Associate (May 2023 - Present, New York)
    - Guosheng Securities Co., Ltd., Equity Analyst Intern (Oct 2021 - Dec 2021, Shanghai)
    - Nanjing Securities Co. Ltd., Investment Banking Analyst Intern (Nov 2020 - Feb 2021, Nanjing)
    - KPMG, Audit Intern (Jan 2020 - Mar 2020, Shanghai)
    
    Include all the detailed project descriptions and achievements for each position as provided.
    
    Skills:
    - Technical: Python for Data Analytics, SQL Data Management, Advanced Excel, Data Visualization, Financial Analysis, Hardware platform selection, Driver development, Terminal product technology protection and distribution
    - Soft Skills: Critical Thinking, Analytical Mindset, Contrarian Thinking, Effective Communication, Strong communication skills, Ability to work under pressure
    - Languages: Japanese (JLPT N1, Fluent), English (IELTS 7.5/7.0 Writing, GRE 330), Mandarin Chinese (Native)
    
    Take screenshots of the completed application and report back when finished.
    """
    
    # Run the agent with the cookies
    await run_agent_with_cookies(
        cookies_data=cookies_data,
        task=task,
        target_url="https://www.yingjiesheng.com/",
        headless=False
    )
    
    # Wait for user input before closing
    input('Press Enter to close the browser...')

if __name__ == "__main__":
    asyncio.run(main()) 