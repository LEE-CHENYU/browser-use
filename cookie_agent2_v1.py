import asyncio
import os
import yaml
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.agent.views import ActionResult

# Load environment variables
load_dotenv()

# Define custom file upload action
async def upload_resume_file(page, file_path):
    """
    Handle file upload using Playwright's set_input_files method.
    
    Args:
        page: The Playwright page
        file_path: Path to the file to upload
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Attempting to upload resume file from: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return False
    
    try:
        # Find any file input elements on the page
        file_inputs = await page.query_selector_all('input[type="file"]')
        print(f"Found {len(file_inputs)} file input elements")
        
        if len(file_inputs) > 0:
            for i, file_input in enumerate(file_inputs):
                try:
                    print(f"Attempting upload with file input {i+1}/{len(file_inputs)}")
                    # Use set_input_files which is the proper way to handle file uploads in Playwright
                    await file_input.set_input_files(file_path)
                    print(f"File upload initiated with file input {i+1}")
                    await asyncio.sleep(2)  # Wait for upload processing
                    return True
                except Exception as e:
                    print(f"Error uploading with file input {i+1}: {e}")
        
        # Check for iframes that might contain file inputs
        frames = page.frames
        for i, frame in enumerate(frames):
            try:
                print(f"Checking frame {i+1}/{len(frames)} for file inputs")
                frame_file_inputs = await frame.query_selector_all('input[type="file"]')
                
                if len(frame_file_inputs) > 0:
                    for j, frame_file_input in enumerate(frame_file_inputs):
                        try:
                            print(f"Attempting upload with frame {i+1} file input {j+1}")
                            await frame_file_input.set_input_files(file_path)
                            print(f"File upload initiated with frame file input")
                            await asyncio.sleep(2)  # Wait for upload processing
                            return True
                        except Exception as e:
                            print(f"Error uploading with frame file input: {e}")
            except Exception as e:
                print(f"Error working with frame {i+1}: {e}")
        
        print("Could not find a suitable file upload element")
        return False
    except Exception as e:
        print(f"Error in upload_resume_file: {e}")
        return False

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

async def custom_agent_with_button_click():
    # Create browser configuration
    browser_config = BrowserConfig(
        headless=False  # Set to True in production
    )
    
    # Create browser instance
    browser = Browser(config=browser_config)
    
    # Create browser context with highlighting enabled
    cookies_dir = "/Users/chenyusu/vscode/jobseeker/happyhunting_app/browser-use/cookies"
    cookies_files = [f for f in os.listdir(cookies_dir) if f.endswith('.json')]
    cookies_file = os.path.join(cookies_dir, cookies_files[0]) if cookies_files else "temp_cookies.json"
    
    context = BrowserContext(
        browser=browser, 
        config=BrowserContextConfig(
            highlight_elements=True,
            viewport_expansion=1000,  # Increased to try to include more elements
            cookies_file=cookies_file
        )
    )
    
    # Define the resume file path - ensure this path is correct and the file exists
    resume_folder = "/Users/chenyusu/vscode/jobseeker/happyhunting_app/browser-use/resume"
    docx_files = [f for f in os.listdir(resume_folder) if f.endswith('.docx')]
    resume_file_path = os.path.join(resume_folder, docx_files[0]) if docx_files else None
    
    if not resume_file_path:
        print("ERROR: No .docx resume file found in the specified folder")
        resume_file_path = input("Please enter the path to your resume file: ")
    
    # Verify the file exists
    if not os.path.exists(resume_file_path):
        print(f"ERROR: Resume file does not exist at: {resume_file_path}")
        resume_file_path = input("Please enter the correct path to your resume file: ")
        if not os.path.exists(resume_file_path):
            print(f"ERROR: Resume file still does not exist at: {resume_file_path}")
            await browser.close()
            return
    
    # Define the URL with proper escaping
    job_url = "https://q.yingjiesheng.com/jobdetail/162210991.html"
    
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
        with open("prompt.yaml", "r", encoding="utf-8") as f:
            prompt_data = yaml.safe_load(f)
        
        # Replace placeholder in the task with actual file path
        agent_task = prompt_data["agent_task"].replace("{resume_file_path}", resume_file_path)
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set the OPENAI_API_KEY environment variable")
        
        llm = ChatOpenAI(model="gpt-4.1")
        
        # Create agent with file upload capability
        agent = Agent(
            browser_context=context,
            task=agent_task,
            llm=llm,
            max_actions_per_step=4,
            available_file_paths=[resume_file_path],  # Make resume file available for upload
            controller=controller  # Use custom controller with file upload action
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