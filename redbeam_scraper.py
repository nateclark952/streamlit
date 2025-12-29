"""
Redbeam Data Scraper
Scrapes data from Redbeam account and saves to Excel file on desktop.
Can be scheduled to run daily.
"""

import os
import time
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('redbeam_scraper.log'),
        logging.StreamHandler()
    ]
)

# Redbeam Credentials
REDBEAM_URL = "https://redbeam.com/login"  # Will redirect to Auth0 login
REDBEAM_AUTH0_LOGIN = "https://login.app.redbeam.com/u/login/identifier"  # Direct Auth0 login page
REDBEAM_USERNAME = "nsclark@bechtel.com"
REDBEAM_PASSWORD = "Axel123$"
REDBEAM_REPORTS_PAGE_URL = "https://app.redbeam.com/g/0/Reports/All Assets"  # Reports page with export feature


def get_desktop_path():
    """Get the output directory path for saving Excel files."""
    output_dir = Path(r"C:\Users\natec\OneDrive\Desktop\redbeam scraper")
    # Create directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def setup_driver():
    """Setup and return a Chrome WebDriver instance with download preferences."""
    # Set up download directory
    download_dir = str(Path.home() / "Downloads")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Set download preferences
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        # Use webdriver-manager to automatically handle ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize Chrome driver with webdriver-manager: {e}")
        logging.info("Attempting to use system ChromeDriver...")
        try:
            # Fallback to system ChromeDriver
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e2:
            logging.error(f"Failed to initialize Chrome driver: {e2}")
            raise


def login_to_redbeam(driver):
    """Login to Redbeam with provided credentials."""
    try:
        # Try going to redbeam.com/login first (will redirect to Auth0 with correct state)
        logging.info(f"Navigating to {REDBEAM_URL}")
        driver.get(REDBEAM_URL)
        
        # Wait for redirect to Auth0 login page
        logging.info("Waiting for redirect to Auth0 login page...")
        try:
            WebDriverWait(driver, 30).until(
                lambda d: "login.app.redbeam.com" in d.current_url or "auth0" in d.current_url.lower()
            )
        except TimeoutException:
            # If no redirect, try going directly to Auth0 login
            logging.info("No redirect detected, trying direct Auth0 login URL...")
            driver.get(REDBEAM_AUTH0_LOGIN)
        
        # Wait for page to fully load and handle redirects (Auth0)
        logging.info("Waiting for Auth0 login page to load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for Auth0 login page to fully render
        time.sleep(10)  # Auth0 pages need more time to load
        
        # Wait for Auth0 form to be ready
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Additional wait for Auth0 JavaScript to initialize
        time.sleep(5)
        
        # Check if we're on Auth0 login page
        current_url = driver.current_url
        logging.info(f"Current URL: {current_url}")
        
        if "login.app.redbeam.com" in current_url or "auth0" in current_url.lower():
            logging.info("Detected Auth0 login page")
        else:
            logging.warning(f"Unexpected URL, but continuing: {current_url}")
        
        # Save page source for debugging
        page_source = driver.page_source
        with open("login_page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        logging.info("Saved login page source to login_page_source.html")
        
        # Find and fill username field - comprehensive search (including Auth0)
        logging.info("Looking for username field...")
        username_selectors = [
            # Auth0 specific selectors
            "input[name='username']",
            "input[name='email']",
            "input[id='username']",
            "input[id='email']",
            "input[type='email']",
            "input[autocomplete='username']",
            "input[autocomplete='email']",
            # CSS Selectors
            "input[name='user']",
            "input[type='text']",
            "input[id*='user']",
            "input[id*='email']",
            "input[id*='login']",
            "input[class*='user']",
            "input[class*='email']",
            # XPath selectors
            "//input[@name='username']",
            "//input[@name='email']",
            "//input[@id='username']",
            "//input[@id='email']",
            "//input[@type='email']",
            "//input[@autocomplete='username']",
            "//input[@autocomplete='email']",
            "//input[contains(@id, 'user')]",
            "//input[contains(@id, 'email')]",
            "//input[contains(@id, 'login')]",
            "//input[contains(@class, 'user')]",
            "//input[contains(@class, 'email')]",
            "//input[contains(@placeholder, 'user')]",
            "//input[contains(@placeholder, 'email')]",
            "//input[contains(@placeholder, 'Email')]",
            "//input[contains(@placeholder, 'Username')]",
            "//input[@type='text' and not @type='password']",
        ]
        
        username_field = None
        for selector in username_selectors:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for elem in elements:
                    try:
                        if elem.is_displayed() and elem.is_enabled():
                            # Make sure it's not the password field
                            if elem.get_attribute("type") != "password":
                                username_field = elem
                                logging.info(f"Found username field with selector: {selector}")
                                break
                    except:
                        continue
                
                if username_field:
                    break
            except Exception as e:
                continue
        
        # If still not found, try to find all input fields and identify the first non-password one
        if not username_field:
            logging.info("Trying alternative method: finding all input fields...")
            try:
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                logging.info(f"Found {len(all_inputs)} input fields on the page")
                for idx, inp in enumerate(all_inputs):
                    try:
                        inp_type = inp.get_attribute("type") or ""
                        inp_name = inp.get_attribute("name") or ""
                        inp_id = inp.get_attribute("id") or ""
                        if inp.is_displayed() and inp.is_enabled() and inp_type != "password" and inp_type != "hidden" and inp_type != "submit" and inp_type != "button":
                            logging.info(f"Trying input field {idx}: type={inp_type}, name={inp_name}, id={inp_id}")
                            username_field = inp
                            break
                    except:
                        continue
            except Exception as e:
                logging.warning(f"Error finding all inputs: {e}")
        
        if not username_field:
            logging.error("Could not find username field. Taking screenshot and saving page info...")
            driver.save_screenshot("login_page_error.png")
            
            # Log all input fields for debugging
            try:
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                logging.error(f"Found {len(all_inputs)} input elements on page:")
                for idx, inp in enumerate(all_inputs):
                    try:
                        logging.error(f"  Input {idx}: type={inp.get_attribute('type')}, name={inp.get_attribute('name')}, id={inp.get_attribute('id')}, class={inp.get_attribute('class')}")
                    except:
                        pass
            except:
                pass
            
            raise Exception("Username field not found")
        
        username_field.clear()
        username_field.send_keys(REDBEAM_USERNAME)
        logging.info("Username entered")
        time.sleep(2)
        
        # STEP 1: Click Continue button after entering username (Auth0 two-step process)
        logging.info("Looking for Continue button after username entry...")
        continue_button_selectors = [
            # Auth0 specific
            "button[type='submit']",
            "button[data-action-button-primary='true']",
            "button[class*='continue']",
            "button[class*='submit']",
            "//button[@type='submit']",
            "//button[@data-action-button-primary='true']",
            "//button[contains(text(), 'Continue')]",
            "//button[contains(text(), 'CONTINUE')]",
            "//button[contains(@class, 'continue')]",
            "//button[contains(@class, 'submit')]",
            "//*[@type='submit']",
        ]
        
        continue_button = None
        for selector in continue_button_selectors:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for elem in elements:
                    try:
                        if elem.is_displayed() and elem.is_enabled():
                            continue_button = elem
                            logging.info(f"Found Continue button with selector: {selector}")
                            break
                    except:
                        continue
                
                if continue_button:
                    break
            except Exception as e:
                continue
        
        if not continue_button:
            # Try pressing Enter on the username field
            logging.warning("Continue button not found. Trying to submit by pressing Enter on username field...")
            username_field.send_keys(Keys.RETURN)
        else:
            continue_button.click()
            logging.info("Continue button clicked")
        
        # Wait for password field to appear (Auth0 shows it after Continue)
        logging.info("Waiting for password field to appear...")
        time.sleep(3)
        
        # Wait for password field to be visible
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
        except TimeoutException:
            logging.warning("Password field not immediately visible, continuing...")
        
        time.sleep(2)
        
        # STEP 2: Find and fill password field
        logging.info("Looking for password field...")
        password_selectors = [
            "input[name='password']",
            "input[type='password']",
            "input[id*='pass']",
            "input[autocomplete='current-password']",
            "//input[@type='password']",
            "//input[@name='password']",
            "//input[@autocomplete='current-password']",
            "//input[contains(@id, 'pass')]",
            "//input[contains(@name, 'pass')]",
        ]
        
        password_field = None
        for selector in password_selectors:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for elem in elements:
                    try:
                        if elem.is_displayed() and elem.is_enabled():
                            password_field = elem
                            logging.info(f"Found password field with selector: {selector}")
                            break
                    except:
                        continue
                
                if password_field:
                    break
            except Exception as e:
                continue
        
        # If still not found, find the password input by type
        if not password_field:
            try:
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in all_inputs:
                    try:
                        if inp.get_attribute("type") == "password" and inp.is_displayed():
                            password_field = inp
                            break
                    except:
                        continue
            except:
                pass
        
        if not password_field:
            raise Exception("Password field not found after clicking Continue")
        
        password_field.clear()
        password_field.send_keys(REDBEAM_PASSWORD)
        logging.info("Password entered")
        time.sleep(2)
        
        # STEP 3: Find and click final Continue/Login button
        logging.info("Looking for final Continue/Login button...")
        login_button_selectors = [
            # Auth0 specific
            "button[type='submit']",
            "button[data-action-button-primary='true']",
            "button[class*='continue']",
            "button[class*='submit']",
            # General selectors
            "input[type='submit']",
            "//button[@type='submit']",
            "//button[@data-action-button-primary='true']",
            "//input[@type='submit']",
            "//button[contains(text(), 'Continue')]",
            "//button[contains(text(), 'CONTINUE')]",
            "//button[contains(text(), 'Login')]",
            "//button[contains(text(), 'Sign in')]",
            "//button[contains(text(), 'Log in')]",
            "//button[contains(text(), 'Sign In')]",
            "//input[@value='Login']",
            "//input[@value='Sign in']",
            "//input[@value='Continue']",
            "//button[contains(@class, 'login')]",
            "//button[contains(@class, 'submit')]",
            "//button[contains(@class, 'continue')]",
            "//*[@type='submit']",
        ]
        
        login_button = None
        for selector in login_button_selectors:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for elem in elements:
                    try:
                        if elem.is_displayed() and elem.is_enabled():
                            login_button = elem
                            logging.info(f"Found login button with selector: {selector}")
                            break
                    except:
                        continue
                
                if login_button:
                    break
            except Exception as e:
                continue
        
        if not login_button:
            # Try to find any submit button
            try:
                submit_buttons = driver.find_elements(By.XPATH, "//*[@type='submit']")
                for btn in submit_buttons:
                    if btn.is_displayed():
                        login_button = btn
                        break
            except:
                pass
        
        if not login_button:
            # Try pressing Enter on the password field
            logging.warning("Login button not found. Trying to submit by pressing Enter on password field...")
            password_field.send_keys(Keys.RETURN)
            time.sleep(5)
        else:
            login_button.click()
            logging.info("Login button clicked")
            time.sleep(5)
        
        # Wait for login to complete (handle Auth0 redirect flow)
        logging.info("Waiting for login to complete...")
        try:
            # Wait for redirect to app.redbeam.com (successful login)
            WebDriverWait(driver, 45).until(
                lambda d: "app.redbeam.com" in d.current_url
            )
            logging.info("Redirected to app.redbeam.com - login successful!")
        except TimeoutException:
            logging.warning("Timeout waiting for redirect to app.redbeam.com, checking current state...")
            current_url = driver.current_url
            logging.info(f"Current URL: {current_url}")
            
            # Check if we're still on a login page
            if ("login.app.redbeam.com" in current_url or 
                "/u/login" in current_url or
                "login" in current_url.lower()):
                logging.warning("Still on login page. Login might have failed.")
                driver.save_screenshot("login_failed.png")
                # Check for error messages (Auth0 style)
                try:
                    error_selectors = [
                        "//*[contains(@class, 'error')]",
                        "//*[contains(@class, 'alert')]",
                        "//*[contains(@class, 'message')]",
                        "//*[contains(@id, 'error')]",
                        "//*[contains(text(), 'error')]",
                        "//*[contains(text(), 'invalid')]",
                        "//*[contains(text(), 'incorrect')]",
                    ]
                    for selector in error_selectors:
                        error_elements = driver.find_elements(By.XPATH, selector)
                        if error_elements:
                            for err in error_elements:
                                try:
                                    if err.is_displayed() and err.text.strip():
                                        logging.error(f"Error message found: {err.text}")
                                except:
                                    pass
                except:
                    pass
                raise Exception("Login failed - still on login page")
        
        time.sleep(5)  # Additional wait for page to fully load
        
        # Check if login was successful
        current_url = driver.current_url
        logging.info(f"Login successful. Current URL: {current_url}")
        
        # Verify we're on the app domain
        if "app.redbeam.com" not in current_url:
            logging.warning(f"Unexpected URL after login: {current_url}")
        
        return True
        
    except Exception as e:
        logging.error(f"Login error: {e}")
        driver.save_screenshot("login_error.png")
        raise


def export_reports_data(driver):
    """Navigate to Reports page and export data to Excel."""
    try:
        logging.info(f"Navigating to Reports page: {REDBEAM_REPORTS_PAGE_URL}")
        driver.get(REDBEAM_REPORTS_PAGE_URL)
        
        # Wait for page to fully load (React/SPA apps need more time)
        logging.info("Waiting for Reports page to load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for dynamic content to load
        time.sleep(10)  # SPA apps need time to render
        
        # Wait for page to be interactive
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(5)
        
        # Wait for the data table/report to load
        logging.info("Waiting for report data to load...")
        time.sleep(5)
        
        # Find the export button (circular blue button with cloud and down arrow icon)
        logging.info("Looking for export button (cloud icon with down arrow)...")
        
        export_button = None
        
        # Strategy 1: Look for buttons containing SVG icons (cloud + arrow)
        logging.info("Searching for buttons with SVG icons...")
        try:
            # Find all buttons on the page
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            logging.info(f"Found {len(all_buttons)} buttons on the page")
            
            for btn in all_buttons:
                try:
                    if not btn.is_displayed():
                        continue
                    
                    # Check if button contains SVG (icon buttons)
                    svg_elements = btn.find_elements(By.TAG_NAME, "svg")
                    if svg_elements:
                        # Check button attributes
                        btn_title = (btn.get_attribute("title") or "").lower()
                        btn_aria = (btn.get_attribute("aria-label") or "").lower()
                        btn_class = (btn.get_attribute("class") or "").lower()
                        
                        # Look for export/download related attributes
                        if any(keyword in btn_title or keyword in btn_aria or keyword in btn_class 
                               for keyword in ["export", "download", "cloud", "arrow"]):
                            export_button = btn
                            logging.info(f"Found export button by attributes: title={btn_title}, aria={btn_aria}")
                            break
                        
                        # Check SVG content for cloud/arrow patterns
                        for svg in svg_elements:
                            svg_html = svg.get_attribute("outerHTML") or ""
                            svg_html_lower = svg_html.lower()
                            # Look for common patterns in SVG that might indicate cloud/download
                            if any(pattern in svg_html_lower for pattern in ["path", "polygon", "circle"]):
                                # This is likely an icon button, check if it's near Records text
                                try:
                                    # Check if button is in the header area near Records
                                    records_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Records')]")
                                    if records_elements:
                                        for rec_elem in records_elements:
                                            try:
                                                # Check if button is in same container or nearby
                                                rec_parent = rec_elem.find_element(By.XPATH, "./ancestor::*[contains(@class, 'header') or contains(@class, 'toolbar') or contains(@class, 'action')]")
                                                if rec_parent:
                                                    parent_buttons = rec_parent.find_elements(By.TAG_NAME, "button")
                                                    if btn in parent_buttons:
                                                        export_button = btn
                                                        logging.info("Found export button near Records text by SVG icon")
                                                        break
                                            except:
                                                continue
                                        if export_button:
                                            break
                                except:
                                    pass
                except Exception as e:
                    continue
                
                if export_button:
                    break
        except Exception as e:
            logging.warning(f"Error searching for buttons with SVG: {e}")
        
        # Strategy 2: Look for buttons near "Records" text
        if not export_button:
            logging.info("Searching for buttons near Records text...")
            try:
                records_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Records')]")
                if records_elements:
                    for records_elem in records_elements:
                        try:
                            # Look in the same parent container
                            parent = records_elem.find_element(By.XPATH, "./ancestor::*[1]")
                            # Also check siblings and nearby elements
                            nearby_buttons = parent.find_elements(By.XPATH, ".//button | ./following-sibling::*//button | ./preceding-sibling::*//button")
                            
                            for btn in nearby_buttons:
                                try:
                                    if btn.is_displayed():
                                        # Prefer buttons with SVG/icons
                                        svgs = btn.find_elements(By.TAG_NAME, "svg")
                                        if svgs or btn.get_attribute("class"):
                                            export_button = btn
                                            logging.info("Found button near Records text")
                                            break
                                except:
                                    continue
                            
                            if export_button:
                                break
                        except:
                            continue
            except Exception as e:
                logging.warning(f"Error searching near Records: {e}")
        
        # Strategy 3: Look for buttons with specific class patterns
        if not export_button:
            logging.info("Searching for buttons with export/download classes...")
            export_class_selectors = [
                "button[class*='export']",
                "button[class*='download']",
                "button[class*='icon']",
                "button[title*='Export']",
                "button[title*='Download']",
                "button[aria-label*='Export']",
                "button[aria-label*='Download']",
            ]
            
            for selector in export_class_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            export_button = elem
                            logging.info(f"Found export button with selector: {selector}")
                            break
                    if export_button:
                        break
                except:
                    continue
        
        if not export_button:
            # Take screenshot for debugging
            driver.save_screenshot("export_button_not_found.png")
            logging.error("Export button not found. Screenshot saved.")
            raise Exception("Export button not found on Reports page")
        
        # Click the export button to open dropdown
        logging.info("Clicking export button...")
        try:
            # Try using ActionChains for more reliable clicking
            actions = ActionChains(driver)
            actions.move_to_element(export_button).click().perform()
        except:
            # Fallback to regular click
            export_button.click()
        
        # Wait for the dropdown menu to appear
        logging.info("Waiting for export menu to appear...")
        time.sleep(5)  # Give React more time to render the menu
        
        # Use keyboard navigation: down arrow 3 times, then Enter
        logging.info("Using keyboard navigation: Down arrow 3 times, then Enter...")
        try:
            # Ensure the export button or body has focus for keyboard events
            driver.execute_script("document.body.focus();")
            time.sleep(0.5)
            
            # Press down arrow 3 times to navigate to CSV option (3rd option)
            actions = ActionChains(driver)
            actions.send_keys(Keys.ARROW_DOWN).perform()  # 1st down - skip Excel 2007+
            time.sleep(0.3)
            actions.send_keys(Keys.ARROW_DOWN).perform()  # 2nd down - skip Excel 97-2004
            time.sleep(0.3)
            actions.send_keys(Keys.ARROW_DOWN).perform()  # 3rd down - select CSV
            time.sleep(0.3)
            actions.send_keys(Keys.ENTER).perform()  # Enter to confirm and start download
            logging.info("Completed keyboard navigation: 3x Down Arrow + Enter")
            time.sleep(5)  # Wait for download to start
            
            # Check for downloaded file
            logging.info("Checking for downloaded CSV file...")
            download_dir = Path.home() / "Downloads"
            max_wait = 60
            wait_time = 0
            
            while wait_time < max_wait:
                csv_files = list(download_dir.glob("*.csv"))
                if csv_files:
                    csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    most_recent = csv_files[0]
                    file_age = time.time() - most_recent.stat().st_mtime
                    if file_age < 60:  # File modified in last 60 seconds
                        logging.info(f"Found downloaded CSV file: {most_recent}")
                        return most_recent
                time.sleep(2)
                wait_time += 2
            
            # If file not found, raise error
            raise Exception("CSV file not found in Downloads folder after keyboard navigation")
            
        except Exception as e:
            logging.error(f"Keyboard navigation failed: {e}")
            # Take screenshot for debugging
            driver.save_screenshot("keyboard_nav_error.png")
            raise Exception(f"Failed to download CSV using keyboard navigation: {e}")
        
        # Find and click the CSV (Comma Separated Values) export option
        logging.info("Looking for CSV export option...")
        
        csv_option = None
        
        # Method 1: Use JavaScript to find all elements with CSV text (works with portals)
        logging.info("Searching for CSV option using JavaScript...")
        try:
            csv_elements = driver.execute_script("""
                var allElements = document.querySelectorAll('*');
                var csvElements = [];
                for (var i = 0; i < allElements.length; i++) {
                    var elem = allElements[i];
                    var text = (elem.textContent || elem.innerText || '').toLowerCase();
                    if ((text.includes('csv') || text.includes('comma separated')) && 
                        elem.offsetParent !== null) { // Check if visible
                        csvElements.push(elem);
                    }
                }
                return csvElements;
            """)
            
            if csv_elements:
                logging.info(f"Found {len(csv_elements)} elements with CSV text via JavaScript")
                # Get the first visible one that's likely a menu item
                for elem in csv_elements:
                    try:
                        # Check if it's a menu item or clickable
                        tag = elem.tag_name.lower()
                        role = elem.get_attribute("role") or ""
                        class_attr = (elem.get_attribute("class") or "").lower()
                        if "menu" in class_attr or role == "menuitem" or tag in ["a", "button", "li", "div"]:
                            csv_option = elem
                            logging.info(f"Found CSV option via JavaScript: {elem.text}")
                            break
                    except:
                        continue
        except Exception as e:
            logging.warning(f"JavaScript search failed: {e}")
        
        # Method 2: Try standard selectors
        if not csv_option:
            csv_option_selectors = [
                # szh-menu specific selectors
                "//*[contains(@class, 'szh-menu__item') and contains(text(), 'Comma Separated Values (CSV)')]",
                "//*[contains(@class, 'szh-menu__item') and contains(text(), 'Comma Separated Values')]",
                "//*[contains(@class, 'szh-menu__item') and contains(text(), 'CSV')]",
                # General selectors
                "//*[contains(text(), 'Comma Separated Values (CSV)')]",
                "//*[contains(text(), 'Comma Separated Values')]",
                "//*[contains(text(), 'CSV')]",
                "//*[contains(text(), 'csv')]",
                "//a[contains(text(), 'CSV')]",
                "//a[contains(text(), 'Comma')]",
                "//button[contains(text(), 'CSV')]",
                "//li[contains(text(), 'CSV')]",
                "//li[contains(text(), 'Comma')]",
                "//div[contains(text(), 'CSV')]",
                "//div[contains(text(), 'Comma')]",
                "//*[@role='menuitem' and contains(text(), 'CSV')]",
                "//*[@role='menuitem' and contains(text(), 'Comma')]",
                "//*[@role='option' and contains(text(), 'CSV')]",
                "//*[@role='option' and contains(text(), 'Comma')]",
            ]
            
            for selector in csv_option_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        try:
                            if elem.is_displayed():
                                text = elem.text.strip()
                                # Make sure it's actually the CSV option
                                if "csv" in text.lower() or "comma" in text.lower():
                                    csv_option = elem
                                    logging.info(f"Found CSV export option with selector: {selector}, text: {text}")
                                    break
                        except:
                            continue
                    if csv_option:
                        break
                except:
                    continue
        
        # If still not found, try to find all menu items using JavaScript (for React portals)
        if not csv_option:
            logging.info("Trying to find menu items using JavaScript (for React portals)...")
            try:
                # Use JavaScript to find all menu items (works with portals)
                menu_items_js = driver.execute_script("""
                    var items = [];
                    var selectors = ['.szh-menu__item', '[role="menuitem"]', '.menu-item', 'li'];
                    selectors.forEach(function(selector) {
                        var elements = document.querySelectorAll(selector);
                        for (var i = 0; i < elements.length; i++) {
                            if (elements[i].offsetParent !== null) { // Check if visible
                                items.push(elements[i]);
                            }
                        }
                    });
                    return items;
                """)
                
                if menu_items_js:
                    logging.info(f"Found {len(menu_items_js)} menu items via JavaScript")
                    for item in menu_items_js:
                        try:
                            text = item.text.strip().lower()
                            if "csv" in text or ("comma" in text and "separated" in text):
                                csv_option = item
                                logging.info(f"Found CSV option via JavaScript: {item.text}")
                                break
                        except:
                            continue
            except Exception as e:
                logging.warning(f"Error finding menu items via JavaScript: {e}")
        
        # Final fallback: find all menu items using standard Selenium
        if not csv_option:
            logging.info("Trying to find all menu items using Selenium...")
            try:
                menu_items = driver.find_elements(By.CSS_SELECTOR, ".szh-menu__item, [role='menuitem'], li, .menu-item, div[class*='menu']")
                logging.info(f"Found {len(menu_items)} menu items")
                for item in menu_items:
                    try:
                        if item.is_displayed():
                            text = item.text.strip().lower()
                            if "csv" in text or ("comma" in text and "separated" in text):
                                csv_option = item
                                logging.info(f"Found CSV option in menu items: {item.text}")
                                break
                    except:
                        continue
            except Exception as e:
                logging.warning(f"Error finding menu items: {e}")
        
        if not csv_option:
            # Take screenshot for debugging
            driver.save_screenshot("csv_option_not_found.png")
            # Save page source after clicking
            with open("menu_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logging.error("CSV export option not found. Screenshot and page source saved.")
            raise Exception("CSV export option not found in dropdown")
        
        # Click the CSV option using multiple methods
        logging.info("Clicking CSV export option...")
        try:
            # Method 1: Try JavaScript click (works with React portals)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", csv_option)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", csv_option)
            logging.info("Clicked CSV option using JavaScript")
        except Exception as e:
            logging.warning(f"JavaScript click failed: {e}, trying ActionChains...")
            try:
                # Method 2: Try ActionChains
                actions = ActionChains(driver)
                actions.move_to_element(csv_option).click().perform()
                logging.info("Clicked CSV option using ActionChains")
            except Exception as e2:
                logging.warning(f"ActionChains click failed: {e2}, trying regular click...")
                # Method 3: Regular click
                csv_option.click()
                logging.info("Clicked CSV option using regular click")
        
        time.sleep(1)  # Wait for click to register
        
        # Wait for download to complete
        logging.info("Waiting for file download...")
        time.sleep(10)  # Wait for download to start
        
        # Check Downloads folder for the file
        download_dir = Path.home() / "Downloads"
        logging.info(f"Checking Downloads folder: {download_dir}")
        
        # Wait for file to appear (up to 60 seconds)
        max_wait = 60
        wait_time = 0
        downloaded_file = None
        
        while wait_time < max_wait:
            # Look for CSV files that were recently downloaded
            csv_files = list(download_dir.glob("*.csv"))
            if csv_files:
                # Get the most recently modified file
                csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                most_recent = csv_files[0]
                # Check if it was modified in the last minute
                file_age = time.time() - most_recent.stat().st_mtime
                if file_age < 60:  # File modified in last 60 seconds
                    downloaded_file = most_recent
                    logging.info(f"Found downloaded CSV file: {downloaded_file}")
                    break
            time.sleep(2)
            wait_time += 2
        
        if not downloaded_file:
            raise Exception("Downloaded file not found in Downloads folder")
        
        return downloaded_file
        
    except Exception as e:
        logging.error(f"Error exporting data: {e}")
        driver.save_screenshot("export_error.png")
        with open("export_error_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise


def save_to_excel(dataframes, output_path):
    """Save scraped data to Excel file."""
    try:
        desktop = get_desktop_path()
        excel_path = desktop / output_path
        
        if not dataframes:
            logging.warning("No data to save")
            return
        
        # If multiple dataframes, save to different sheets
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for idx, df in enumerate(dataframes):
                sheet_name = f"Sheet{idx + 1}" if len(dataframes) > 1 else "Data"
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logging.info(f"Data saved to {excel_path}")
        return excel_path
        
    except Exception as e:
        logging.error(f"Error saving to Excel: {e}")
        raise


def main():
    """Main function to run the scraper."""
    driver = None
    try:
        logging.info("=" * 50)
        logging.info("Starting Redbeam Scraper")
        logging.info("=" * 50)
        
        # Setup driver
        driver = setup_driver()
        logging.info("Chrome driver initialized")
        
        # Login
        login_to_redbeam(driver)
        
        # Export data from Reports page
        downloaded_file = export_reports_data(driver)
        
        # Move file to destination directory with timestamp
        output_dir = get_desktop_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"redbeam_data_{timestamp}.csv"
        final_path = output_dir / filename
        
        # Move the downloaded file to the final location
        shutil.move(str(downloaded_file), str(final_path))
        logging.info(f"Moved file from {downloaded_file} to {final_path}")
        
        logging.info("=" * 50)
        logging.info(f"Export completed successfully!")
        logging.info(f"Data saved to: {final_path}")
        logging.info("=" * 50)
        
        return final_path
        
    except Exception as e:
        logging.error(f"Scraper failed: {e}")
        raise
        
    finally:
        if driver:
            driver.quit()
            logging.info("Browser closed")


if __name__ == "__main__":
    main()

