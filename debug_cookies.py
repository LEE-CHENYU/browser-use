import json
import os
import asyncio
from browser_use import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext

async def main():
    # Load cookies from file
    cookies_path = "/Users/chenyusu/vscode/jobseeker/cookies.json"
    
    if not os.path.exists(cookies_path):
        print(f"Error: Cookie file not found at {cookies_path}")
        return
    
    with open(cookies_path, 'r') as f:
        try:
            cookies = json.load(f)
            print(f"Successfully loaded {len(cookies)} cookies from {cookies_path}")
        except json.JSONDecodeError as e:
            print(f"Error parsing cookies file: {e}")
            return
    
    # Print the first cookie for inspection
    if cookies:
        print("\nFirst cookie (before fixing):")
        print(json.dumps(cookies[0], indent=2))
    
    # Fix cookies by properly formatting them for Playwright
    fixed_cookies = []
    for cookie in cookies:
        # Create a new cookie with only the required fields
        fixed_cookie = {
            "name": cookie.get("name", ""),
            "value": cookie.get("value", ""),
            "domain": cookie.get("domain", ""),
            "path": cookie.get("path", "/"),
            "sameSite": "None"
        }
        
        # Add optional fields if they exist
        if "expires" in cookie or "expirationDate" in cookie:
            fixed_cookie["expires"] = cookie.get("expires", cookie.get("expirationDate", 0))
        
        if "secure" in cookie:
            fixed_cookie["secure"] = cookie["secure"]
        
        if "httpOnly" in cookie:
            fixed_cookie["httpOnly"] = cookie["httpOnly"]
        
        # Check if all required fields have values
        if not fixed_cookie["name"] or not fixed_cookie["domain"]:
            print(f"Warning: Skipping cookie with missing required fields: {fixed_cookie}")
            continue
        
        fixed_cookies.append(fixed_cookie)
    
    print(f"\nFixed {len(fixed_cookies)} cookies")
    
    # Print the first fixed cookie
    if fixed_cookies:
        print("\nFirst cookie (after fixing):")
        print(json.dumps(fixed_cookies[0], indent=2))
    
    # Create browser config
    browser_config = BrowserConfig()
    
    # Create a browser
    browser = Browser(config=browser_config)
    
    # Create a browser context
    browser_context = BrowserContext(browser=browser)
    
    try:
        # Get the session and add the fixed cookies
        session = await browser_context.get_session()
        print("\nAdding cookies to browser context...")
        await session.context.add_cookies(fixed_cookies)
        
        # Verify cookies were added
        added_cookies = await session.context.cookies()
        print(f"Successfully added {len(added_cookies)} cookies to browser context")
        
        # Print the first added cookie
        if added_cookies:
            print("\nFirst cookie in browser context:")
            print(json.dumps(added_cookies[0], indent=2))
        
        # Navigate to the website to test if cookies are working
        page = await browser_context.get_current_page()
        print("\nNavigating to yingjiesheng.com to test cookies...")
        await page.goto("https://www.yingjiesheng.com")
        
        # Wait a bit to see if login popup appears
        await asyncio.sleep(5)
        
        # Check if we're logged in by looking for specific elements
        print("\nChecking login status...")
        login_popup = await page.query_selector('button[aria-label="Close"]')
        if login_popup:
            print("Login popup detected - cookies may not be working correctly")
        else:
            print("No login popup detected - cookies may be working correctly")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the browser
        await browser.close()
        print("\nBrowser closed")

if __name__ == "__main__":
    asyncio.run(main()) 