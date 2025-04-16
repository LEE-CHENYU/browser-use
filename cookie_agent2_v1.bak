import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

# Load environment variables
load_dotenv()

async def custom_agent_with_button_click():
    # Create browser configuration
    browser_config = BrowserConfig(
        headless=False  # Set to True in production
    )
    
    # Create browser instance
    browser = Browser(config=browser_config)
    
    # Create browser context with highlighting enabled
    context = BrowserContext(
        browser=browser, 
        config=BrowserContextConfig(
            highlight_elements=True,
            viewport_expansion=1000,  # Increased to try to include more elements
            cookies_file="temp_cookies.json"  # If you're using cookies
        )
    )
    
    # Define the resume file path
    resume_file_path = "/Users/chenyusu/Documents/GitHub/browser-use/李宸宇中文简历.docx"
    
    # Define the URL with proper escaping
    job_url = "https://q.yingjiesheng.com/jobdetail/157805378.html"
    
    try:
        # Get a session and navigate to the URL
        session = await context.get_session()
        page = await context.get_current_page()
        
        print(f"Navigating to job listing...")
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
            await page.evaluate("""() => {
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
        else:
            print("Apply button found, clicking...")
            await apply_button.click()
        
        # Wait a moment for any redirects or form loads
        await asyncio.sleep(2)
        
        # Now run the agent with further exploration instructions
        import yaml
        with open("prompt.yaml", "r", encoding="utf-8") as f:
            prompt_data = yaml.safe_load(f)
        agent_task = prompt_data["agent_task"]

        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set the OPENAI_API_KEY environment variable")
        
        llm = ChatOpenAI(model="gpt-4.1")
        
        agent = Agent(
            browser_context=context,
            task=agent_task,
            llm=llm,
            max_actions_per_step=4
        )
        
        print("Starting agent exploration...")
        result = await agent.run(max_steps=20)
        print(f"Agent completed with result: {result}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Keep browser open until user decides to close
        input("Press Enter to close the browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(custom_agent_with_button_click())