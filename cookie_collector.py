#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import argparse
import sys

# Import the cookie converter
from convert_cookies import convert_cookies

def collect_cookies(headless=False, wait_time=300, manual_mode=False):
    """
    Open a browser window, guide the user to log in, and collect cookies.
    
    Args:
        headless (bool): Whether to run in headless mode
        wait_time (int): Maximum time to wait for user login in seconds
        manual_mode (bool): If True, allow user to manually browse before collecting cookies
    
    Returns:
        dict: Collected cookies or None if failed
    """
    print("===== 应招网用户登录与Cookie收集 =====")
    print("这个脚本将引导您登录应招网并收集您的登录凭证。")
    print("请准备好您的账号和密码。")
    
    # Setup Chrome options
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    # Create cookies directory if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cookies_dir = os.path.join(script_dir, "cookies")
    os.makedirs(cookies_dir, exist_ok=True)
    
    driver = None
    try:
        print("\n启动浏览器...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # First visit the main site to get initial cookies
        print("打开应招网主页...")
        driver.get("https://www.yingjiesheng.com/")
        time.sleep(5)  # Increased delay to ensure cookies are set (was 2)
        
        # Go to the login page
        print("打开应招网登录页面...")
        driver.get("https://q.yingjiesheng.com/login")
        
        # Wait for the user to complete login
        print("\n请在打开的浏览器窗口中完成登录。")
        print(f"脚本将等待最多 {wait_time} 秒让您完成登录。")
        print("完成登录后，脚本将自动收集您的登录凭证。")
        print("如果登录后脚本没有继续，请按Enter键手动继续...")
        
        # Multiple login detection methods
        login_detected = False
        start_time = time.time()
        
        while not login_detected and (time.time() - start_time) < wait_time:
            try:
                # Try multiple possible elements that might indicate successful login
                selectors = [
                    ".avatar-img", 
                    ".user-name", 
                    ".user-avatar",
                    ".user-info",
                    ".logout",
                    "a[href*='logout']"
                ]
                
                for selector in selectors:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        if element:
                            print(f"\n检测到登录元素: {selector}")
                            login_detected = True
                            break
                    except:
                        pass
                
                # Check if URL changed to a logged-in page
                current_url = driver.current_url
                if "login" not in current_url and login_detected == False:
                    if "q.yingjiesheng.com/jobs" in current_url or "yingjiesheng.com/mspace" in current_url:
                        print("\n检测到URL已更改，可能已登录")
                        login_detected = True
                
                # Check if we have specific cookies that indicate login
                cookies = driver.get_cookies()
                auth_cookies = [c for c in cookies if "Token" in c.get("name", "") or "UAccountId" in c.get("name", "")]
                if auth_cookies and login_detected == False:
                    print("\n检测到认证Cookie，认为已登录")
                    for c in auth_cookies:
                        print(f"- 发现Cookie: {c.get('name')}")
                    login_detected = True
                
                if login_detected:
                    break
                    
                # Small delay before checking again
                time.sleep(1)
                
            except Exception as e:
                print(f"\n登录检测出错: {str(e)}")
                time.sleep(1)
        
        # If we've waited and still no login detected, ask user to confirm
        if not login_detected:
            print("\n未自动检测到登录。")
            user_input = input("如果您已登录成功，请输入 'y' 继续；否则按Enter退出: ").strip().lower()
            if user_input != 'y':
                print("用户取消，退出脚本")
                return None
            print("用户确认已登录，继续执行...")
        else:
            print("已成功检测到登录！")
        
        if manual_mode:
            print("\n=== 手动浏览模式 ===")
            print("请在浏览器中手动访问需要的页面，以确保所有必要的Cookie都已设置。")
            print("浏览完成后，请按Enter键继续收集Cookie...")
            input()
        else:
            # Visit additional pages to ensure all cookies are collected
            print("\n访问额外页面以收集所有必要的Cookie...")
            
            # Visit the main site again after login
            print("访问主页...")
            driver.get("https://www.yingjiesheng.com/")
            time.sleep(2)
            
            # Visit the jobs search page
            print("访问职位搜索页面...")
            driver.get("https://q.yingjiesheng.com/jobs/search/")
            time.sleep(2)
            
            # Visit the user center/profile page if available
            print("访问用户中心页面...")
            driver.get("https://www.yingjiesheng.com/mspace/")
            time.sleep(2)
        
        # Get the cookies after visiting multiple pages
        print("\n开始收集Cookie...")
        cookies = driver.get_cookies()
        if not cookies:
            print("警告: 未能收集到任何Cookie，请确认是否已登录")
            return None
            
        print(f"成功收集到 {len(cookies)} 个cookie")
        
        # Compare with existing cookies if available
        default_cookies_path = os.path.join(script_dir, "cookies.json")
        if os.path.exists(default_cookies_path):
            try:
                with open(default_cookies_path, 'r', encoding='utf-8') as f:
                    existing_cookies = json.load(f)
                print(f"已有cookie文件包含 {len(existing_cookies)} 个cookie")
                
                # Extract cookie names for comparison
                new_names = {c['name'] for c in cookies}
                existing_names = {c['name'] for c in existing_cookies}
                
                missing = existing_names - new_names
                if missing:
                    print(f"警告: 以下cookie未能收集到: {', '.join(missing)}")
                    print("如需获取完整cookie，可能需要更多浏览操作或使用手动模式")
            except:
                print("无法读取现有cookie文件进行比较")
        
        # Ensure the cookies have all the required fields for convert_cookies.py
        for cookie in cookies:
            # Add session flag if not present
            if "session" not in cookie:
                cookie["session"] = "expirationDate" not in cookie

            # Make sure domain field exists
            if "domain" not in cookie:
                cookie["domain"] = ".yingjiesheng.com"

            # Make sure path field exists
            if "path" not in cookie:
                cookie["path"] = "/"

            # Make sure sameSite is in the right format
            if "sameSite" not in cookie:
                cookie["sameSite"] = "unspecified"

            # Ensure we handle cookies according to convert_cookies.py rules
            if cookie.get("sameSite") == "no_restriction":
                cookie["sameSite"] = "None"
                
            # Preserve any other attributes to avoid data loss
        
        print("Cookie数据已处理完成，准备保存...")
        return cookies
        
    except Exception as e:
        print(f"收集Cookie过程中发生错误: {str(e)}")
        return None
    finally:
        if driver:
            print("关闭浏览器...")
            driver.quit()

def save_cookies(cookies, username, merge_existing=True):
    """
    Save cookies with username and timestamp.
    
    Args:
        cookies (list): List of cookie dictionaries
        username (str): Username for the cookie file name
        merge_existing (bool): Whether to merge with existing cookies for completeness
    
    Returns:
        tuple: (original_file_path, converted_file_path) or (None, None) if failed
    """
    if not cookies:
        return None, None
        
    try:
        # Create cookies directory if it doesn't exist
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cookies_dir = os.path.join(script_dir, "cookies")
        os.makedirs(cookies_dir, exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean username (remove special characters)
        clean_username = ''.join(c for c in username if c.isalnum() or c in '_-')
        if not clean_username:
            clean_username = "anonymous"
        
        # Create file paths
        original_file = os.path.join(cookies_dir, f"{clean_username}_{timestamp}_original.json")
        converted_file = os.path.join(cookies_dir, f"{clean_username}_{timestamp}.json")
        
        # If merging with existing cookies from the cookies folder
        merged_cookies = cookies.copy()
        if merge_existing:
            # Try to find the most recent cookie file in the cookies directory
            cookie_files = [f for f in os.listdir(cookies_dir) 
                          if f.endswith('_original.json')]  # Use original files to ensure complete data
            
            if cookie_files:
                latest_cookie_file = os.path.join(cookies_dir, sorted(cookie_files)[-1])
                try:
                    with open(latest_cookie_file, 'r', encoding='utf-8') as f:
                        existing_cookies = json.load(f)
                    
                    # Create a dictionary of new cookies by name for easy lookup
                    new_cookies_dict = {cookie['name']: cookie for cookie in cookies}
                    
                    # Add any existing cookies that aren't in the new set
                    for existing_cookie in existing_cookies:
                        if existing_cookie['name'] not in new_cookies_dict:
                            merged_cookies.append(existing_cookie)
                            print(f"合并现有Cookie: {existing_cookie['name']}")
                    
                    print(f"合并后共有 {len(merged_cookies)} 个Cookie")
                except Exception as e:
                    print(f"合并Cookie失败: {str(e)}")
                    # Continue with just the new cookies
        
        # Save original cookies with all properties intact
        with open(original_file, 'w', encoding='utf-8') as f:
            json.dump(merged_cookies, f, ensure_ascii=False, indent=2)
        
        print(f"\n原始Cookie已保存至: {original_file}")
        
        # Convert cookies using convert_cookies.py
        if convert_cookies(original_file, converted_file):
            print(f"转换后的Cookie已保存至: {converted_file}")
            print("\n注意：默认的cookies.json文件未被修改，将从cookies目录随机使用Cookie文件")
            
            # Verify conversion didn't lose data
            try:
                with open(converted_file, 'r', encoding='utf-8') as f:
                    converted = json.load(f)
                print(f"转换后共有 {len(converted)} 个Cookie")
                
                if len(converted) < len(merged_cookies):
                    print(f"警告: 转换后Cookie数量减少 ({len(merged_cookies)} -> {len(converted)})")
                    
                    # Show which cookies were lost
                    original_names = {c['name'] for c in merged_cookies}
                    converted_names = {c['name'] for c in converted}
                    lost = original_names - converted_names
                    
                    if lost:
                        print(f"丢失的Cookie: {', '.join(lost)}")
            except:
                print("无法验证转换后的Cookie文件")
            
            return original_file, converted_file
        else:
            print("Cookie转换失败")
            return original_file, None
            
    except Exception as e:
        print(f"保存Cookie时发生错误: {str(e)}")
        return None, None

def main():
    parser = argparse.ArgumentParser(description='应招网登录与Cookie收集工具')
    parser.add_argument('--headless', action='store_true', help='使用无头模式（不显示浏览器窗口）')
    parser.add_argument('--wait', type=int, default=300, help='等待用户登录的最大时间（秒）')
    parser.add_argument('--username', type=str, help='用户名（用于命名Cookie文件）')
    parser.add_argument('--no-merge', action='store_true', help='不合并现有Cookie（仅使用新收集的）')
    parser.add_argument('--manual', action='store_true', help='手动浏览模式（允许用户自行浏览网站收集Cookie）')
    
    args = parser.parse_args()
    
    # Ensure headless and manual mode aren't used together
    if args.headless and args.manual:
        print("错误: 手动模式不能与无头模式一起使用")
        sys.exit(1)
    
    # Collect cookies
    cookies = collect_cookies(headless=args.headless, wait_time=args.wait, manual_mode=args.manual)
    
    if cookies:
        # Get username if not provided
        username = args.username
        if not username:
            username = input("\n请输入您的用户名（用于Cookie文件命名）: ")
            if not username.strip():
                username = "user"
        
        # Save cookies with merge option (default to True unless --no-merge flag is used)
        original_file, converted_file = save_cookies(cookies, username, merge_existing=not args.no_merge)
        
        if converted_file:
            print("\n=== Cookie收集完成 ===")
            print("您现在可以使用爬虫脚本获取职位信息了")
            print(f"Cookie已保存在: {converted_file}")
            print("提示: 如果您的登录状态过期，请重新运行此脚本以更新Cookie")
        else:
            print("\n=== Cookie收集失败 ===")
            print("请重试或联系开发者获取帮助")
    else:
        print("\n=== Cookie收集失败 ===")
        print("未能收集到有效的Cookie，请确保成功登录")

if __name__ == "__main__":
    main() 