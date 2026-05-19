import os
import sys
import json
import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def execute_tasks(driver, tasks):
    for task in tasks:
        action = task.get("action")
        try:
            if action == "goto":
                url = task.get("url")
                print(f"Navigating to {url}")
                driver.get(url)
            
            elif action == "click":
                selector = task.get("selector")
                print(f"Clicking {selector}")
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                element.click()
            
            elif action == "type":
                selector = task.get("selector")
                text = task.get("text")
                print(f"Typing '{text}' into {selector}")
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                element.clear()
                element.send_keys(text)
            
            elif action == "wait":
                seconds = task.get("seconds", 1)
                print(f"Waiting for {seconds} seconds")
                time.sleep(seconds)
            
            elif action == "snapshot_page":
                filename = task.get("filename", "screenshot.png")
                print(f"Saving full page snapshot to {filename}")
                driver.save_screenshot(filename)
            
            elif action == "snapshot_element":
                selector = task.get("selector")
                filename = task.get("filename", "element.png")
                print(f"Saving element snapshot ({selector}) to {filename}")
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                element.screenshot(filename)
            
            else:
                print(f"Unknown action: {action}")
                
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error: Element not found or timeout for action '{action}'", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error executing action '{action}': {str(e)}", file=sys.stderr)
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Web Snapshot Browser Bot")
    parser.add_argument("--tasks", required=True, help="Path to JSON file containing tasks")
    args = parser.parse_args()
    
    if not os.path.exists(args.tasks):
        print(f"Error: Task file {args.tasks} not found", file=sys.stderr)
        sys.exit(1)
        
    with open(args.tasks, "r") as f:
        tasks = json.load(f)
        
    driver = setup_driver()
    try:
        execute_tasks(driver, tasks)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
