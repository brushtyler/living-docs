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
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-site-isolation-trials")
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def wait_for_network_idle(driver, timeout=10, idle_time=0.5):
    """
    Wait for the network to be idle for at least idle_time seconds.
    Uses JavaScript performance entries to estimate network activity.
    """
    # Shorter initial sleep for better responsiveness
    time.sleep(0.1)
    
    start_time = time.time()
    # Initialize last_resource_count with current count to return faster if no activity
    last_resource_count = driver.execute_script("return window.performance.getEntriesByType('resource').length")
    last_activity_time = time.time()
    
    while time.time() - start_time < timeout:
        # Get count of finished resources
        resource_count = driver.execute_script("return window.performance.getEntriesByType('resource').length")
        
        if resource_count != last_resource_count:
            last_resource_count = resource_count
            last_activity_time = time.time()
        
        # If no new resources for idle_time, we consider it idle
        if time.time() - last_activity_time >= idle_time:
            # Only print if we actually waited more than the minimum
            total_wait = time.time() - start_time
            if total_wait > 0.2:
                print(f"Network idle reached (total wait: {total_wait:.2f}s)", flush=True)
            return True
            
        time.sleep(0.1)
    
    print("Warning: Timed out waiting for network idle.", flush=True)
    return False

def execute_tasks(driver, task_input, metadata_output=None):
    metadata = []
    has_failed = False

    # Normalize input: always work with a list of batches (lists of tasks)
    if not task_input:
        return

    if isinstance(task_input[0], dict):
        batches = [task_input]
    else:
        batches = task_input

    for batch_idx, tasks in enumerate(batches):
        print(f"\n--- Executing Batch {batch_idx + 1}/{len(batches)} ({len(tasks)} tasks) ---", flush=True)
        # Clear cookies and local storage to isolate each batch's session
        try:
            driver.delete_all_cookies()
            if driver.current_url and not (driver.current_url.startswith("data:") or driver.current_url.startswith("about:")):
                driver.execute_script("window.localStorage.clear();")
        except Exception as e:
            pass
        batch_failed = False
        for task in tasks:
            if batch_failed:
                break

            action = task.get("action")
            try:
                if action == "goto":
                    url = task.get("url")
                    print(f"Navigating to {url}", flush=True)
                    driver.get(url)
                    # Use a safer idle_time for navigation
                    wait_for_network_idle(driver, idle_time=0.8)

                elif action == "click":
                    selector = task.get("selector")
                    print(f"Clicking {selector}", flush=True)
                    element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.click()
                    # Wait for network idle with medium threshold
                    wait_for_network_idle(driver, idle_time=0.4)

                elif action == "type":
                    selector = task.get("selector")
                    text = task.get("text")
                    print(f"Typing '{text}' into {selector}", flush=True)
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(text)
                    # Short idle time for typing (likely no network or just a small JSON fetch)
                    wait_for_network_idle(driver, idle_time=0.2)

                elif action == "wait":
                    seconds = task.get("seconds", 1)
                    print(f"Waiting for {seconds} seconds", flush=True)
                    time.sleep(seconds)

                elif action == "wait_for_selector":
                    selector = task.get("selector")
                    timeout = task.get("timeout", 10)
                    print(f"Waiting for selector {selector} for up to {timeout} seconds", flush=True)
                    WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )

                elif action == "wait_for_hidden":
                    selector = task.get("selector")
                    timeout = task.get("timeout", 10)
                    print(f"Waiting for selector {selector} to be hidden for up to {timeout} seconds", flush=True)
                    WebDriverWait(driver, timeout).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
                    )

                elif action == "wait_for_text":
                    selector = task.get("selector")
                    text = task.get("text")
                    timeout = task.get("timeout", 10)
                    print(f"Waiting for text '{text}' in {selector} for up to {timeout} seconds", flush=True)
                    WebDriverWait(driver, timeout).until(
                        EC.text_to_be_present_in_element((By.CSS_SELECTOR, selector), text)
                    )

                elif action == "highlight":
                    selector = task.get("selector")
                    style_type = task.get("style", "outline")
                    color = task.get("color", "#ff3366")
                    print(f"Highlighting element {selector} with style '{style_type}' and color '{color}'", flush=True)
                    # Wait for element to be present
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    js_highlight = """
                    const selector = arguments[0];
                    const styleType = arguments[1];
                    const color = arguments[2];
                    const el = document.querySelector(selector);
                    if (!el) return;

                    // Preserve original styling variables
                    if (!el.dataset.origOutline) {
                        el.dataset.origOutline = el.style.outline || '';
                        el.dataset.origOutlineOffset = el.style.outlineOffset || '';
                        el.dataset.origBoxShadow = el.style.boxShadow || '';
                        el.dataset.origPosition = el.style.position || '';
                        el.dataset.origZIndex = el.style.zIndex || '';
                    }

                    if (styleType === 'outline') {
                        el.style.outline = '4px solid ' + color;
                        el.style.outlineOffset = '4px';
                        el.style.boxShadow = '0 0 10px ' + color;
                    } else if (styleType === 'spotlight') {
                        el.style.position = 'relative';
                        el.style.zIndex = '999999';
                        el.style.outline = '4px solid ' + color;
                        el.style.outlineOffset = '4px';
                        el.style.boxShadow = '0 0 0 99999px rgba(0, 0, 0, 0.5), 0 0 15px ' + color;
                    } else if (styleType === 'badge') {
                        const isVoid = ['INPUT', 'IMG', 'BR', 'HR'].includes(el.tagName);
                        const badge = document.createElement('div');
                        badge.className = 'living-docs-highlight-badge';
                        badge.style.position = 'absolute';
                        badge.style.width = '20px';
                        badge.style.height = '20px';
                        badge.style.borderRadius = '50%';
                        badge.style.backgroundColor = color;
                        badge.style.border = '2px solid white';
                        badge.style.boxShadow = '0 2px 6px rgba(0,0,0,0.4)';
                        badge.style.zIndex = '1000000';
                        
                        if (isVoid) {
                            // Position absolute on body matching the element coordinates
                            const rect = el.getBoundingClientRect();
                            badge.style.position = 'absolute';
                            badge.style.top = (rect.top + window.scrollY - 8) + 'px';
                            badge.style.left = (rect.left + window.scrollX - 8) + 'px';
                            document.body.appendChild(badge);
                        } else {
                            // Append inside the element
                            const origPos = el.style.position;
                            if (!origPos || origPos === 'static') {
                                el.style.position = 'relative';
                            }
                            badge.style.top = '-8px';
                            badge.style.left = '-8px';
                            el.appendChild(badge);
                        }

                        // Add pulse animation style if not already added
                        if (!document.getElementById('living-docs-pulse-style')) {
                            const styleEl = document.createElement('style');
                            styleEl.id = 'living-docs-pulse-style';
                            styleEl.innerHTML = `
                                @keyframes pulse {
                                    0% { box-shadow: 0 0 0 0 rgba(255, 51, 102, 0.7); }
                                    70% { box-shadow: 0 0 0 8px rgba(255, 51, 102, 0); }
                                    100% { box-shadow: 0 0 0 0 rgba(255, 51, 102, 0); }
                                }
                                .living-docs-highlight-badge {
                                    animation: pulse 1.5s infinite;
                                }
                            `;
                            document.head.appendChild(styleEl);
                        }
                    }
                    """
                    driver.execute_script(js_highlight, selector, style_type, color)

                elif action == "clear_highlights":
                    print("Clearing all page highlights...", flush=True)
                    js_clear = """
                    const elements = document.querySelectorAll('[data-orig-outline]');
                    elements.forEach(el => {
                        el.style.outline = el.dataset.origOutline;
                        el.style.outlineOffset = el.dataset.origOutlineOffset;
                        el.style.boxShadow = el.dataset.origBoxShadow;
                        el.style.position = el.dataset.origPosition;
                        el.style.zIndex = el.dataset.origZIndex;
                        
                        delete el.dataset.origOutline;
                        delete el.dataset.origOutlineOffset;
                        delete el.dataset.origBoxShadow;
                        delete el.dataset.origPosition;
                        delete el.dataset.origZIndex;
                    });

                    document.querySelectorAll('.living-docs-highlight-badge').forEach(el => el.remove());
                    const pulseStyle = document.getElementById('living-docs-pulse-style');
                    if (pulseStyle) pulseStyle.remove();
                    """
                    driver.execute_script(js_clear)

                elif action == "snapshot_page" or action == "snapshot":
                    # Wait for network idle before taking snapshot
                    wait_for_network_idle(driver, idle_time=0.5)
                    filename = task.get("filename", "screenshot.png")
                    print(f"Saving full page snapshot to {filename}", flush=True)
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
                    if not driver.save_screenshot(filename):
                        raise Exception(f"Failed to save full page snapshot to {filename}")

                elif action == "snapshot_element":
                    # Wait for network idle before taking snapshot
                    wait_for_network_idle(driver, idle_time=0.5)
                    selector = task.get("selector")
                    filename = task.get("filename", "element.png")
                    print(f"Saving element snapshot ({selector}) to {filename}", flush=True)
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if not element.screenshot(filename):
                        raise Exception(f"Failed to save element snapshot to {filename}")

                elif action == "extract_info":
                    selector = task.get("selector")
                    print(f"Extracting info from {selector}", flush=True)
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
                    print(f"Unknown action: {action}", flush=True)

            except (TimeoutException, NoSuchElementException) as e:
                print(f"Error: Element not found or timeout for action '{action}' in batch {batch_idx + 1}", file=sys.stderr, flush=True)
                batch_failed = True
            except Exception as e:
                print(f"Error executing action '{action}' in batch {batch_idx + 1}: {str(e)}", file=sys.stderr, flush=True)
                batch_failed = True
        
        if batch_failed:
            has_failed = True
            
    if metadata_output and metadata:
        with open(metadata_output, "w") as f:
            json.dump(metadata, f, indent=2)

    return not has_failed

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
    success = False
    try:
        success = execute_tasks(driver, tasks, args.output_metadata)
    finally:
        driver.quit()

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
