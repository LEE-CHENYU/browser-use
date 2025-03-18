from playwright.sync_api import sync_playwright
import json

# Your cookies data
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

# Convert cookies to the format Playwright expects
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

with sync_playwright() as p:
    # Launch the browser in headless mode (no UI)
    browser = p.chromium.launch(headless=False)
    
    # Create a new browser context
    context = browser.new_context()
    
    # Add the cookies to the context
    context.add_cookies(playwright_cookies)
    
    # Create a new page
    page = context.new_page()
    
    # Navigate to the website
    page.goto("https://www.yingjiesheng.com/")
    
    # Wait for the page to load
    page.wait_for_load_state("networkidle")
    
    # Check if we're logged in by looking for elements that would only appear when logged in
    # For example, you might look for a username element or a logout button
    logged_in = page.is_visible("text=我的应届生")  # Adjust this selector based on the actual page
    
    print(f"Logged in: {logged_in}")
    
    # You can also save the page content to verify what you're seeing
    with open("page_content.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    
    # Optionally, take a screenshot
    page.screenshot(path="screenshot.png")
    
    # You can also extract specific information from the page
    # For example, if you want to get the username displayed on the page:
    # username = page.text_content(".username-selector")  # Replace with actual selector
    # print(f"Username: {username}")
    
    # Close the browser
    browser.close()