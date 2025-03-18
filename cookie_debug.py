import json
import os
import asyncio
import sys
from browser_use import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext
from playwright.async_api import Error as PlaywrightError

async def main():
    # Load cookies from file
    cookies_path = "/Users/chenyusu/vscode/jobseeker/cookies.json"
    
    if not os.path.exists(cookies_path):
        print(f"Error: Cookie file not found at {cookies_path}")
        return
    
    print(f"Reading cookies from: {cookies_path}")
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
    for i, cookie in enumerate(cookies):
        try:
            # Get domain and path
            domain = cookie.get("domain", "")
            path = cookie.get("path", "/")
            
            # Remove leading dot from domain if present
            if domain.startswith("."):
                clean_domain = domain[1:]
            else:
                clean_domain = domain
            
            # Determine protocol
            secure = cookie.get("secure", False)
            protocol = "https" if secure else "http"
            
            # Create URL
            url = f"{protocol}://{clean_domain}{path}"
            
            # Create a new cookie with only the required fields
            # IMPORTANT: Include either domain OR url, not both
            fixed_cookie = {
                "name": cookie.get("name", ""),
                "value": cookie.get("value", ""),
                # "domain": domain,  # Remove domain field
                "path": path,
                "url": url,  # Use only URL field
                "sameSite": "None"  # Must be one of: "Strict", "Lax", or "None"
            }
            
            # Add optional fields if they exist
            if "expires" in cookie or "expirationDate" in cookie:
                fixed_cookie["expires"] = cookie.get("expires", cookie.get("expirationDate", 0))
            
            if "secure" in cookie:
                fixed_cookie["secure"] = cookie["secure"]
            
            if "httpOnly" in cookie:
                fixed_cookie["httpOnly"] = cookie["httpOnly"]
            
            # Check if all required fields have values
            if not fixed_cookie["name"]:
                print(f"Warning: Skipping cookie {i+1} with missing name: {fixed_cookie}")
                continue
            
            fixed_cookies.append(fixed_cookie)
            print(f"Fixed cookie {i+1}/{len(cookies)}: {fixed_cookie['name']} for URL {fixed_cookie['url']}")
        except Exception as e:
            print(f"Error processing cookie {i+1}: {e}")
    
    print(f"\nSuccessfully fixed {len(fixed_cookies)}/{len(cookies)} cookies")
    
    # Print the first fixed cookie
    if fixed_cookies:
        print("\nFirst cookie (after fixing):")
        print(json.dumps(fixed_cookies[0], indent=2))
    
    # Create browser config
    browser_config = BrowserConfig()
    
    # Create a browser
    print("\nCreating browser...")
    browser = Browser(config=browser_config)
    
    # Create a browser context
    print("Creating browser context...")
    browser_context = BrowserContext(browser=browser)
    
    try:
        # Get the session and add the fixed cookies
        print("Getting browser session...")
        session = await browser_context.get_session()
        
        # Add cookies one by one to better handle errors
        print("\nAdding cookies to browser context...")
        successful_cookies = 0
        
        for i, cookie in enumerate(fixed_cookies):
            try:
                # Try adding each cookie individually
                await session.context.add_cookies([cookie])
                successful_cookies += 1
                print(f"✅ Added cookie {i+1}/{len(fixed_cookies)}: {cookie['name']} for {cookie['url']}")
            except PlaywrightError as e:
                print(f"❌ Failed to add cookie {i+1}/{len(fixed_cookies)}: {cookie['name']} - Error: {e}")
                # Print the problematic cookie
                print(f"Problematic cookie: {json.dumps(cookie, indent=2)}")
        
        print(f"\nSuccessfully added {successful_cookies}/{len(fixed_cookies)} cookies to browser context")
        
        # Verify cookies were added
        added_cookies = await session.context.cookies()
        print(f"Browser reports {len(added_cookies)} cookies are now active")
        
        # Print the first added cookie
        if added_cookies:
            print("\nFirst cookie in browser context:")
            print(json.dumps(added_cookies[0], indent=2))
        
        # Navigate to the website to test if cookies are working
        print("\nNavigating to yingjiesheng.com to test cookies...")
        page = await browser_context.get_current_page()
        
        try:
            await page.goto("https://www.yingjiesheng.com", timeout=30000)
            print("Page loaded successfully")
            
            # Wait a bit to see if login popup appears
            print("Waiting to check for login popup...")
            await asyncio.sleep(5)
            
            # Check if we're logged in by looking for specific elements
            print("\nChecking login status...")
            login_popup = await page.query_selector('button[aria-label="Close"]')
            if login_popup:
                print("❌ Login popup detected - cookies may not be working correctly")
                
                # Take a screenshot for reference
                await page.screenshot(path="login_popup.png")
                print("Screenshot saved to login_popup.png")
            else:
                print("✅ No login popup detected - cookies may be working correctly")
                
                # Take a screenshot for reference
                await page.screenshot(path="logged_in.png")
                print("Screenshot saved to logged_in.png")
        except PlaywrightError as e:
            print(f"❌ Error navigating to page: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close the browser
        print("\nClosing browser...")
        await browser.close()
        print("Browser closed")

if __name__ == "__main__":
    asyncio.run(main()) 