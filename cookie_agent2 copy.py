import asyncio
import os
import json
import time
import argparse
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

# Load environment variables
load_dotenv()

def load_user_info(json_path='user_info.json'):
    """Load user information from a JSON file"""
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            user_info = json.load(file)
        print(f"Successfully loaded user information from {json_path}")
        return user_info
    except FileNotFoundError:
        print(f"User info file {json_path} not found. Creating a template file.")
        # Create a template file if it doesn't exist
        template = {
            "personal_info": {
                "name": "Your Name",
                "email": "your.email@example.com",
                "linkedin": "Your LinkedIn Name",
                "location": "Your City",
                "gender": "0",  # 0 for male, 1 for female
                "political_status": "3",  # 3 for 群众
                "ethnicity": "1",  # 1 for 汉族
                "household_registration": ["Province", "City"],
                "phone": "Your Phone Number",
                "birth_date": "YYYY-MM-DD",
                "github": "https://github.com/yourusername",
                "linkedin_url": "linkedin.com/in/your-profile"
            },
            "education": [
                {
                    "institution": "University Name",
                    "degree": "Your Degree",
                    "location": "City",
                    "period": "Start Date - End Date",
                    "gpa": "Your GPA",
                    "courses": "Course1; Course2; Course3",
                    "projects": "Project description"
                }
            ],
            "experience": [
                {
                    "company": "Company Name",
                    "position": "Your Position",
                    "location": "City",
                    "period": "Start Date - End Date",
                    "responsibilities": [
                        "Responsibility 1",
                        "Responsibility 2"
                    ]
                }
            ],
            "activities": [
                {
                    "organization": "Organization Name",
                    "role": "Your Role",
                    "location": "City",
                    "period": "Time Period",
                    "description": "Description of activities"
                }
            ],
            "skills": {
                "languages": [
                    {"language": "Language 1", "proficiency": "Proficiency Level"},
                    {"language": "Language 2", "proficiency": "Proficiency Level"}
                ],
                "technical": [
                    "Skill 1",
                    "Skill 2"
                ],
                "other": ["Other skill"]
            },
            "interests": "Your interests"
        }
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(template, file, ensure_ascii=False, indent=2)
        print(f"Created template file at {json_path}. Please fill it with your information and run the script again.")
        return None

def load_rpa_config(json_path='rpa_config.json'):
    """Load RPA configuration from a JSON file"""
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            rpa_config = json.load(file)
        print(f"Successfully loaded RPA configuration from {json_path}")
        return rpa_config
    except FileNotFoundError:
        print(f"RPA config file {json_path} not found. Creating a template file.")
        # Create a template file if it doesn't exist
        template = {
            "resume_file_path": "/path/to/your/resume.docx",
            "resume_url": "https://example.com/your-resume.docx",
            "job_url": "https://example.com/job-listing",
            "form_selectors": {
                "name": "#cc_Cname_1_1",
                "gender": "#cc_Gender_1_1",
                "birth_date": "#cc_Birthday_3_1",
                "political_status": "#cc_Party_1_1",
                "ethnicity": "#cc_CCA6_1_1",
                "province_select": "#ddl_City_1_1",
                "city_select": "#cc_City_1_1",
                "household_province": "#ddl_CCE2_5_1",
                "household_city": "#cc_CCE2_5_1",
                "email": "#cc_Email_1_1",
                "phone": "#cc_MobilePhone_1_1",
                "resume_iframe": "iframe[src*=\"UpLoad.aspx?fid=2\"]",
                "next_button": "#imgbtnNext",
                "save_button": "#imgbtnSave",
                "apply_button": [
                    "div.delivery-btn",
                    "button:has-text(\"立即申请\")",
                    "a:has-text(\"立即申请\")"
                ],
                "confirm_button": [
                    "button:has-text(\"确定\")",
                    "input[value=\"确定\"]",
                    ".btn-confirm",
                    ".confirm-btn"
                ]
            },
            "navigation": {
                "expected_form_url_patterns": [
                    "/ehireplus/",
                    "resume.asp",
                    "application_form",
                    "apply"
                ],
                "max_wait_for_navigation": 10,
                "post_confirm_wait": 3
            },
            "province_mapping": {
                "江苏": "7",
                "上海": "2", 
                "北京": "1",
                "广东": "3",
                "浙江": "8",
                "四川": "9"
            },
            "city_mapping": {
                "南京": "070200",
                "上海": "020000",
                "北京": "010000",
                "广州": "030200",
                "深圳": "040000",
                "杭州": "080200"
            },
            "wait_times": {
                "page_load": 2,
                "dropdown_update": 0.5,
                "upload": 3,
                "before_submit": 1
            }
        }
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(template, file, ensure_ascii=False, indent=2)
        print(f"Created template file at {json_path}. Please fill it with your configuration and run the script again.")
        return None

async def upload_resume(page, resume_file_path, selectors):
    """Enhanced function to upload a resume file"""
    print(f"Attempting to upload resume from: {resume_file_path}")
    
    if not os.path.exists(resume_file_path):
        print(f"Error: Resume file not found at {resume_file_path}")
        return False
    
    try:
        # Take screenshot before upload attempt
        await page.screenshot(path="before_upload.png")
        print("Screenshot saved as before_upload.png")
        
        # Look for iframe elements that might contain the file upload
        resume_iframes = await page.query_selector_all('iframe')
        print(f"Found {len(resume_iframes)} iframes on the page")
        
        upload_successful = False
        
        # Try the specific iframe first - this is the most likely scenario
        resume_iframe_selector = selectors.get("resume_iframe", 'iframe[src*="UpLoad.aspx?fid=2"]')
        resume_iframe = await page.query_selector(resume_iframe_selector)
        if resume_iframe:
            print(f"Found the upload iframe with selector: {resume_iframe_selector}")
            iframe_frame = await resume_iframe.content_frame()
            upload_button = await iframe_frame.query_selector('input[type="file"]')
            
            if upload_button:
                print("Found file upload input in primary iframe")
                await upload_button.set_input_files(resume_file_path)
                await asyncio.sleep(3)  # Wait for upload
                print("File upload initiated in primary iframe")
                upload_successful = True
        
        # If the specific iframe didn't work, try all iframes
        if not upload_successful:
            print("Trying all iframes...")
            for i, iframe in enumerate(resume_iframes):
                try:
                    print(f"Checking iframe {i+1}/{len(resume_iframes)}")
                    iframe_frame = await iframe.content_frame()
                    if iframe_frame:
                        # Take a screenshot of the iframe content
                        await iframe_frame.screenshot(path=f"iframe_{i+1}.png")
                        print(f"Screenshot of iframe {i+1} saved")
                        
                        # Look for file input
                        upload_button = await iframe_frame.query_selector('input[type="file"]')
                        if upload_button:
                            print(f"Found file upload input in iframe {i+1}")
                            await upload_button.set_input_files(resume_file_path)
                            await asyncio.sleep(3)  # Wait for upload
                            print(f"File upload initiated in iframe {i+1}")
                            upload_successful = True
                            break
                except Exception as e:
                    print(f"Error checking iframe {i+1}: {e}")
        
        # If iframe approach didn't work, try direct page approach
        if not upload_successful:
            print("Trying direct page approach...")
            # Look for file input directly on the page
            file_inputs = await page.query_selector_all('input[type="file"]')
            print(f"Found {len(file_inputs)} file inputs directly on the page")
            
            for i, file_input in enumerate(file_inputs):
                try:
                    print(f"Attempting upload with file input {i+1}/{len(file_inputs)}")
                    await file_input.set_input_files(resume_file_path)
                    await asyncio.sleep(3)  # Wait for upload
                    print(f"File upload initiated with file input {i+1}")
                    upload_successful = True
                    break
                except Exception as e:
                    print(f"Error uploading with file input {i+1}: {e}")
        
        # Take screenshot after upload attempt
        await page.screenshot(path="after_upload.png")
        print("Screenshot saved as after_upload.png")
        
        if upload_successful:
            print("Resume upload process completed successfully")
            return True
        else:
            print("Could not find a suitable file upload element")
            return False
            
    except Exception as e:
        print(f"Error uploading resume: {e}")
        return False

async def fill_form_with_rpa(page, user_info, rpa_config):
    """RPA function to fill out the form directly using separate config"""
    print("Executing RPA form filling function...")
    
    try:
        # Extract configuration
        selectors = rpa_config.get("form_selectors", {})
        province_mapping = rpa_config.get("province_mapping", {})
        city_mapping = rpa_config.get("city_mapping", {})
        wait_times = rpa_config.get("wait_times", {})
        
        # Extract personal info
        personal_info = user_info.get("personal_info", {})
        
        # Basic information section
        # Fill name (if not already filled)
        name_selector = selectors.get("name", "#cc_Cname_1_1")
        name_field = await page.query_selector(name_selector)
        if name_field:
            current_name = await name_field.input_value()
            if not current_name and "name" in personal_info:
                await name_field.fill(personal_info["name"])
                print(f"Filled name: {personal_info['name']}")
        
        # Select gender (if not already selected)
        gender_selector = selectors.get("gender", "#cc_Gender_1_1")
        gender_select = await page.query_selector(gender_selector)
        if gender_select:
            gender = personal_info.get("gender", "0")  # Default to male if not specified
            await gender_select.select_option(gender)
            print(f"Selected gender: {gender}")
        
        # Set birth date (if not already set)
        birth_date_selector = selectors.get("birth_date", "#cc_Birthday_3_1")
        birth_date = await page.query_selector(birth_date_selector)
        if birth_date:
            current_date = await birth_date.input_value()
            if not current_date and "birth_date" in personal_info:
                await birth_date.fill(personal_info["birth_date"])
                print(f"Filled birth date: {personal_info['birth_date']}")
        
        # Set Political Status
        political_selector = selectors.get("political_status", "#cc_Party_1_1")
        party_select = await page.query_selector(political_selector)
        if party_select:
            political_status = personal_info.get("political_status", "3")  # Default to 群众 if not specified
            await party_select.select_option(political_status)
            print(f"Selected political status: {political_status}")
        
        # Set Ethnicity
        ethnicity_selector = selectors.get("ethnicity", "#cc_CCA6_1_1")
        ethnicity_select = await page.query_selector(ethnicity_selector)
        if ethnicity_select:
            ethnicity = personal_info.get("ethnicity", "1")  # Default to 汉族 if not specified
            await ethnicity_select.select_option(ethnicity)
            print(f"Selected ethnicity: {ethnicity}")
        
        # Set Current Residence
        province_selector = selectors.get("province_select", "#ddl_City_1_1")
        city_selector = selectors.get("city_select", "#cc_City_1_1")
        
        city_province_select = await page.query_selector(province_selector)
        city_select = await page.query_selector(city_selector)
        
        if city_province_select and city_select and "household_registration" in personal_info and len(personal_info["household_registration"]) >= 2:
            province = personal_info["household_registration"][0]
            province_code = province_mapping.get(province, "7")  # Default to 江苏省 if not found
            
            # First select province
            await city_province_select.select_option(province_code)
            await asyncio.sleep(wait_times.get("dropdown_update", 0.5))  # Wait for city dropdown to update
            print(f"Selected province: {province}")
            
            # Then select city
            city = personal_info["household_registration"][1]
            city_code = city_mapping.get(city, "070200")  # Default to 南京
            
            await city_select.select_option(city_code)
            print(f"Selected city: {city}")
        
        # Set Household Registration (户籍) - similar to residence
        household_province_selector = selectors.get("household_province", "#ddl_CCE2_5_1")
        household_city_selector = selectors.get("household_city", "#cc_CCE2_5_1")
        
        household_province_select = await page.query_selector(household_province_selector)
        household_city_select = await page.query_selector(household_city_selector)
        
        if household_province_select and "household_registration" in personal_info and len(personal_info["household_registration"]) >= 2:
            province = personal_info["household_registration"][0]
            province_code = province_mapping.get(province, "7")
            
            await household_province_select.select_option(province_code)
            await asyncio.sleep(wait_times.get("dropdown_update", 0.5))
            print(f"Selected household registration province: {province}")
            
            if household_city_select:
                city = personal_info["household_registration"][1]
                city_code = city_mapping.get(city, "070200")  # Default
                
                try:
                    await household_city_select.select_option(city_code)
                    print(f"Selected household registration city: {city}")
                except Exception as e:
                    print(f"Could not select household city. Error: {e}")
        
        # Email
        email_selector = selectors.get("email", "#cc_Email_1_1")
        email_field = await page.query_selector(email_selector)
        if email_field:
            current_email = await email_field.input_value()
            if not current_email and "email" in personal_info:
                await email_field.fill(personal_info["email"])
                print(f"Filled email: {personal_info['email']}")
        
        # Mobile Phone
        phone_selector = selectors.get("phone", "#cc_MobilePhone_1_1")
        phone_field = await page.query_selector(phone_selector)
        if phone_field:
            current_phone = await phone_field.input_value()
            if not current_phone and "phone" in personal_info:
                await phone_field.fill(personal_info["phone"])
                print(f"Filled phone: {personal_info['phone']}")
        
        # Upload resume using the dedicated resume upload function
        if "resume_file_path" in rpa_config:
            resume_uploaded = await upload_resume(page, rpa_config["resume_file_path"], selectors)
            if resume_uploaded:
                print("Resume upload completed successfully")
            else:
                print("Resume upload failed or couldn't be verified")
        
        # Wait a moment before clicking the next button
        await asyncio.sleep(wait_times.get("before_submit", 1))
        
        # Click the next step button
        next_button_selector = selectors.get("next_button", "#imgbtnNext")
        next_button = await page.query_selector(next_button_selector)
        if next_button:
            await next_button.click()
            print("Form filled successfully, clicked '下一步'")
        else:
            # Try alternative button
            save_button_selector = selectors.get("save_button", "#imgbtnSave")
            save_button = await page.query_selector(save_button_selector)
            if save_button:
                await save_button.click()
                print("Form saved successfully using Save button")
            else:
                print("Could not find the '下一步' or Save button")
        
        # Take a screenshot of the completed form
        await page.screenshot(path="form_completed.png")
        print("Screenshot saved as form_completed.png")
        
        # Return success
        return True
    
    except Exception as e:
        print(f"Error in RPA form filling: {e}")
        return False

async def navigate_to_form_page(page, rpa_config):
    """Handle navigation after clicking 确定 button to reach the form page"""
    print("Navigating to the form page after clicking '确定' button...")
    
    try:
        # Get navigation settings
        navigation = rpa_config.get("navigation", {})
        expected_patterns = navigation.get("expected_form_url_patterns", [
            "/ehireplus/",
            "resume.asp",
            "application_form"
        ])
        max_wait = navigation.get("max_wait_for_navigation", 10)
        post_confirm_wait = navigation.get("post_confirm_wait", 3)
        
        # Get confirm button selectors
        selectors = rpa_config.get("form_selectors", {})
        confirm_button_selectors = selectors.get("confirm_button", [
            "button:has-text(\"确定\")",
            "input[value=\"确定\"]",
            ".btn-confirm",
            ".confirm-btn"
        ])
        
        # First take a screenshot before navigation
        await page.screenshot(path="before_navigation.png")
        print("Screenshot saved as before_navigation.png")
        
        # Try to find and click the confirm button
        confirm_button = None
        for selector in confirm_button_selectors:
            confirm_button = await page.query_selector(selector)
            if confirm_button:
                print(f"Found confirm button with selector: {selector}")
                break
        
        if confirm_button:
            print("Clicking '确定' button...")
            # Use a listener to detect the navigation
            navigation_event = asyncio.Event()
            
            async def on_frame_navigated(frame):
                current_url = frame.url
                print(f"Navigated to: {current_url}")
                
                # Check if we've reached the expected form page
                for pattern in expected_patterns:
                    if pattern in current_url:
                        print(f"Detected form page navigation with pattern: {pattern}")
                        navigation_event.set()
                        break
            
            # Add event listener for navigation
            page.on("framenavigated", on_frame_navigated)
            
            # Click the confirm button
            await confirm_button.click()
            print("Clicked '确定' button")
            
            # Wait for navigation or timeout
            try:
                await asyncio.wait_for(navigation_event.wait(), timeout=max_wait)
                print("Successfully navigated to the form page")
                # Additional wait to ensure page is fully loaded
                await asyncio.sleep(post_confirm_wait)
            except asyncio.TimeoutError:
                print(f"Navigation timeout after {max_wait} seconds")
                # Take a screenshot to see the current state
                await page.screenshot(path="navigation_timeout.png")
                print("Screenshot saved as navigation_timeout.png")
                
                # Check if we're on the form page despite the timeout
                current_url = page.url
                for pattern in expected_patterns:
                    if pattern in current_url:
                        print(f"We seem to be on the form page ({current_url}) despite the timeout")
                        break
                else:
                    print(f"Current URL does not match expected form page patterns: {current_url}")
                    return False
            
            # Remove the event listener
            page.remove_listener("framenavigated", on_frame_navigated)
            
            # Wait for the page to stabilize
            await page.wait_for_load_state("networkidle")
            
            # Take screenshot after navigation
            await page.screenshot(path="after_navigation.png")
            print("Screenshot saved as after_navigation.png")
            
            return True
        else:
            print("No '确定' button found. We might already be on the form page.")
            # Check if we're already on a form page
            current_url = page.url
            for pattern in expected_patterns:
                if pattern in current_url:
                    print(f"We seem to be already on the form page: {current_url}")
                    return True
            
            print(f"Current URL does not match expected form page patterns: {current_url}")
            return False
    
    except Exception as e:
        print(f"Error navigating to form page: {e}")
        return False

async def run_agent(context, user_info, rpa_config, max_steps=20, timeout_seconds=30, retries=3):
    """Run the AI agent with retries and timeout"""
    resume_url = rpa_config.get("resume_url", "")
    
    # Combine user_info and necessary parts of rpa_config
    combined_info = user_info.copy()
    combined_info["resume_url"] = resume_url
    combined_info["resume_file_path"] = rpa_config.get("resume_file_path", "")
    
    # Convert combined info to JSON string for the agent task
    user_info_json = json.dumps(combined_info, ensure_ascii=False)
    
    # Define the agent task
    agent_task = f"""
Achieve the following mini goal, and once it's achieved, complete: Fill out the job application form by entering the user's name, email, and phone number and attaching the resume. Complete the other questions and prepare the form for submission.

This mini goal is part of the big goal the user wants to achieve. To achieve the mini goal, use the big goal as context: Go to the job application form, fill out the form, and apply to the job. Answer any questions that appear in the form. Your goal is complete when the page says you've successfully applied to the job. If you are unable to apply successfully, terminate the application.

IMPORTANT:
	•	Navigating through pages by clicking buttons such as "确定" or "下一页".
	•	Do not navigate back or redirect to other URLs. Your navigation should be restricted to clicking buttons. 
	•	Follow the sequence provided in the form rather than the order of the JSON below.
	•	If you encounter any missing information, skip that section. If skipping is not possible, report it.
	•	If a field is already filled with correct information, do not input anything in that field.

{user_info_json}

Take screenshots of the completed application and report back when finished.
"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable")
    
    llm = ChatOpenAI(model="gpt-4o")
    
    agent = Agent(
        browser_context=context,
        task=agent_task,
        llm=llm,
        max_actions_per_step=4
    )
    
    print("Starting agent exploration...")
    
    success = False
    
    for attempt in range(1, retries + 1):
        try:
            print(f"Agent attempt {attempt} of {retries}")
            # Set a timeout for the agent
            start_time = time.time()
            
            # Create a task for the agent
            agent_task_obj = asyncio.create_task(agent.run(max_steps=max_steps))
            
            # Wait for the task with timeout
            while not agent_task_obj.done():
                await asyncio.sleep(0.5)
                if time.time() - start_time > timeout_seconds:
                    print(f"Agent timed out after {timeout_seconds} seconds")
                    # Cancel the agent task
                    agent_task_obj.cancel()
                    try:
                        await agent_task_obj
                    except asyncio.CancelledError:
                        pass
                    break
            
            if agent_task_obj.done() and not agent_task_obj.cancelled():
                result = agent_task_obj.result()
                print(f"Agent completed with result: {result}")
                success = True
                break
        
        except Exception as e:
            print(f"Error in agent attempt {attempt}: {e}")
        
        # If we reach here, either there was an exception or a timeout
        if attempt < retries:
            print(f"Retrying... ({attempt}/{retries})")
            await asyncio.sleep(1)  # Small delay before retry
    
    return success

async def job_application_automation(user_json_path='user_info.json', rpa_json_path='rpa_config.json', use_agent=False, agent_timeout=30, agent_retries=3, agent_max_steps=20):
    """Main function to automate job application with option to use agent or RPA"""
    # Load user information
    user_info = load_user_info(user_json_path)
    if not user_info:
        print("Please fill in the template user JSON file with your information and run the script again.")
        return
    
    # Load RPA configuration
    rpa_config = load_rpa_config(rpa_json_path)
    if not rpa_config:
        print("Please fill in the template RPA config JSON file and run the script again.")
        return
    
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
    
    # Get job URL from rpa_config
    job_url = rpa_config.get("job_url", "")
    if not job_url:
        print("Error: No job URL provided in the RPA config file.")
        await browser.close()
        return
    
    try:
        # Get a session and navigate to the URL
        session = await context.get_session()
        page = await context.get_current_page()
        
        print(f"Navigating to job listing: {job_url}")
        await page.goto(job_url)
        
        # Wait for page to load
        wait_times = rpa_config.get("wait_times", {})
        await page.wait_for_load_state("networkidle")
        
        # Find and click the apply button directly
        print("Looking for the apply button...")
        
        # Get apply button selectors from config
        apply_button_selectors = rpa_config.get("form_selectors", {}).get("apply_button", [
            'div.delivery-btn',
            'button:has-text("立即申请")',
            'a:has-text("立即申请")'
        ])
        
        # Try each selector
        apply_button = None
        for selector in apply_button_selectors:
            apply_button = await page.query_selector(selector)
            if apply_button:
                print(f"Apply button found with selector: {selector}")
                break
        
        if apply_button:
            print("Apply button found, clicking...")
            await apply_button.click()
        else:
            # Try a more generic approach
            print("Using JavaScript to find and click the apply button...")
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
        
        # Wait a moment for any redirects or form loads
        await asyncio.sleep(wait_times.get("page_load", 2))
        
        # Take a screenshot after clicking apply
        await page.screenshot(path="after_apply_click.png")
        print("Screenshot saved as after_apply_click.png")
        
        # Navigate to the form page after clicking apply
        navigation_successful = await navigate_to_form_page(page, rpa_config)
        
        if navigation_successful:
            print("Successfully navigated to the application form")
        else:
            print("Navigation to form page failed or timed out")
                    # Navigate to the form page after clicking apply
        navigation_successful = await navigate_to_form_page(page, rpa_config)
        
        if navigation_successful:
            print("Successfully navigated to the application form")
        else:
            print("Navigation to form page failed or timed out")
            # Continue anyway as we might still be on a valid form page
        
        # Take a screenshot of the application form
        await page.screenshot(path="application_form.png")
        print("Screenshot of application form saved as application_form.png")
        
        success = False
        
        # Decide whether to use the agent or direct RPA
        if use_agent:
            print("Using AI agent to fill the form...")
            success = await run_agent(
                context=context, 
                user_info=user_info,
                rpa_config=rpa_config,
                max_steps=agent_max_steps,
                timeout_seconds=agent_timeout,
                retries=agent_retries
            )
            
            # If agent failed, fall back to RPA
            if not success:
                print("Agent failed to complete the task. Falling back to RPA approach.")
                success = await fill_form_with_rpa(page, user_info, rpa_config)
        else:
            # Directly use RPA approach
            print("Using RPA approach to fill the form...")
            success = await fill_form_with_rpa(page, user_info, rpa_config)
        
        if success:
            print("Job application process completed successfully!")
        else:
            print("Job application process could not be completed.")
        
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Keep browser open until user decides to close
        user_input = input("Press Enter to close the browser or type 'keep' to keep it open: ")
        if user_input.lower() != 'keep':
            await browser.close()
            print("Browser closed.")
        else:
            print("Browser remains open. Please close it manually when done.")

if __name__ == "__main__":
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Automate job application form filling')
    parser.add_argument('--user-json', default='user_info.json', help='Path to JSON file with user information')
    parser.add_argument('--rpa-json', default='rpa_config.json', help='Path to JSON file with RPA configuration')
    parser.add_argument('--agent', action='store_true', help='Use AI agent instead of direct RPA')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds for AI agent')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries for AI agent')
    parser.add_argument('--steps', type=int, default=20, help='Maximum steps for AI agent')
    
    args = parser.parse_args()
    
    # Run the automation
    asyncio.run(job_application_automation(
        user_json_path=args.user_json,
        rpa_json_path=args.rpa_json,
        use_agent=args.agent,
        agent_timeout=args.timeout,
        agent_retries=args.retries,
        agent_max_steps=args.steps
    ))