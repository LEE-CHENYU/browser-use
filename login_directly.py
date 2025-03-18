import asyncio
from browser_use import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext

async def main():
    # Create browser config
    browser_config = BrowserConfig()
    
    # Create a browser
    browser = Browser(config=browser_config)
    
    # Create a browser context
    browser_context = BrowserContext(browser=browser)
    
    try:
        # Get the session
        session = await browser_context.get_session()
        
        # Get the current page
        page = await browser_context.get_current_page()
        
        # Navigate to the login page
        print("Navigating to yingjiesheng.com...")
        await page.goto("https://www.yingjiesheng.com")
        
        # Wait for the page to load
        await asyncio.sleep(3)
        
        # Check if login popup appears and close it
        login_popup_close = await page.query_selector('button[aria-label="Close"]')
        if login_popup_close:
            print("Closing login popup...")
            await login_popup_close.click()
            await asyncio.sleep(1)
        
        # Find and click the login button
        login_button = await page.query_selector('a:has-text("登录")')
        if login_button:
            print("Clicking login button...")
            await login_button.click()
            await asyncio.sleep(2)
        
        # Enter username and password
        # Replace with your actual credentials
        username = "your_username"
        password = "your_password"
        
        # Find username and password fields
        username_field = await page.query_selector('input[placeholder="请输入用户名"]')
        password_field = await page.query_selector('input[placeholder="请输入密码"]')
        
        if username_field and password_field:
            print("Entering credentials...")
            await username_field.fill(username)
            await password_field.fill(password)
            
            # Click the login submit button
            submit_button = await page.query_selector('button:has-text("登录")')
            if submit_button:
                print("Submitting login...")
                await submit_button.click()
                await asyncio.sleep(5)
                
                # Check if login was successful
                print("Checking login status...")
                # You can add code here to check if login was successful
                
                # Take a screenshot
                await page.screenshot(path="login_result.png")
                print("Screenshot saved to login_result.png")
            else:
                print("Login submit button not found")
        else:
            print("Username or password field not found")
        
        # Wait for user input before closing
        input("Press Enter to close the browser...")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the browser
        await browser.close()
        print("Browser closed")

if __name__ == "__main__":
    asyncio.run(main()) 