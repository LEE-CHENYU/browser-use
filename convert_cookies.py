#!/usr/bin/env python3
import json
import sys

def convert_cookies(input_file, output_file):
    """
    Convert browser-exported cookies to Playwright format.
    
    Playwright requires specific cookie formatting:
    1. SameSite values must be "None", "Lax", or "Strict" with proper capitalization
    2. Cookies with sameSite="None" must have secure=true
    3. "expires" instead of "expirationDate"
    """
    try:
        # Read the input file
        with open(input_file, 'r') as f:
            browser_cookies = json.load(f)
        
        # Initialize a list to store the converted cookies
        playwright_cookies = []
        
        # Convert each cookie
        for cookie in browser_cookies:
            # Create a basic Playwright cookie
            playwright_cookie = {
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": cookie["path"],
            }
            
            # Handle expiration
            if "expirationDate" in cookie and not cookie.get("session", False):
                playwright_cookie["expires"] = cookie["expirationDate"]
            
            # Handle sameSite property - fix 'unspecified' to valid value
            if "sameSite" in cookie:
                sameSite = cookie["sameSite"]
                if sameSite == "unspecified" or sameSite == "":
                    playwright_cookie["sameSite"] = "None"
                    # Cookies with sameSite="None" must have secure=true
                    playwright_cookie["secure"] = True
                else:
                    # Convert first letter to uppercase for Playwright convention
                    playwright_cookie["sameSite"] = sameSite[0].upper() + sameSite[1:].lower()
            
            # Copy other relevant flags
            if "httpOnly" in cookie:
                playwright_cookie["httpOnly"] = cookie["httpOnly"]
                
            # Handle secure flag - ensure it's true if sameSite is None
            if "secure" in cookie and cookie["secure"]:
                playwright_cookie["secure"] = cookie["secure"]
            elif playwright_cookie.get("sameSite") == "None":
                playwright_cookie["secure"] = True
            
            playwright_cookies.append(playwright_cookie)
        
        # Write to output file
        with open(output_file, 'w') as f:
            json.dump(playwright_cookies, f, indent=2)
        
        print(f"Successfully converted {len(playwright_cookies)} cookies from {input_file} to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error converting cookies: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_cookies.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    success = convert_cookies(input_file, output_file)
    sys.exit(0 if success else 1) 