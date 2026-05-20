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

def execute_tasks(driver, task_input, metadata_output=None):
    metadata = []

    # Normalize input: always work with a list of batches (lists of tasks)
    if not task_input:
        return

    if isinstance(task_input[0], dict):
        batches = [task_input]
    else:
        batches = task_input

    for batch_idx, tasks in enumerate(batches):
        print(f"\n--- Executing Batch {batch_idx + 1}/{len(batches)} ({len(tasks)} tasks) ---")
        batch_failed = False
        for task in tasks:
            if batch_failed:
                break

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

                elif action == "wait_for_selector":
                    selector = task.get("selector")
                    timeout = task.get("timeout", 10)
                    print(f"Waiting for selector {selector} for up to {timeout} seconds")
                    WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )

                elif action == "snapshot_page" or action == "snapshot":
                    filename = task.get("filename", "screenshot.png")
                    print(f"Saving full page snapshot to {filename}")
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
                    if not driver.save_screenshot(filename):
                        raise Exception(f"Failed to save full page snapshot to {filename}")

                elif action == "snapshot_element":
                    selector = task.get("selector")
                    filename = task.get("filename", "element.png")
                    print(f"Saving element snapshot ({selector}) to {filename}")
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if not element.screenshot(filename):
                        raise Exception(f"Failed to save element snapshot to {filename}")

                elif action == "extract_info":
                    selector = task.get("selector")
                    print(f"Extracting info from {selector}")
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    info = {
                        "selector": selector,
                        "text": element.text,
                        "tag": element.tag_name,
                        "attributes": {
                            attr: element.get_attribute(attr)
                            for attr in ["aria-label", "alt", "title", "placeholder", "value"]
                            if element.get_attribute(attr)
                        }
                    }
                    metadata.append(info)

                else:
                    print(f"Unknown action: {action}")

            except (TimeoutException, NoSuchElementException) as e:
                print(f"Error: Element not found or timeout for action '{action}' in batch {batch_idx + 1}", file=sys.stderr)
                batch_failed = True
            except Exception as e:
                print(f"Error executing action '{action}' in batch {batch_idx + 1}: {str(e)}", file=sys.stderr)
                batch_failed = True
    if metadata_output and metadata:
        with open(metadata_output, "w") as f:
            json.dump(metadata, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Web Snapshot Browser Bot")
    parser.add_argument("--tasks", required=True, help="Path to JSON file containing tasks")
    parser.add_argument("--output-metadata", help="Path to save extracted metadata (JSON)")
    args = parser.parse_args()
    
    if not os.path.exists(args.tasks):
        print(f"Error: Task file {args.tasks} not found", file=sys.stderr)
        sys.exit(1)
        
    with open(args.tasks, "r") as f:
        tasks = json.load(f)
        
    driver = setup_driver()
    try:
        execute_tasks(driver, tasks, args.output_metadata)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
