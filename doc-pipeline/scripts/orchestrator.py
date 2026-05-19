import subprocess
import sys
import os
import json

def run_command(cmd, description):
    print(f"\n>>> {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None

def main():
    check_only = "--check-only" in sys.argv
    print("=== Living Docs: Unified Sync Manager ===")
    
    # 0. Check Environment
    print("\n>>> Verifying environment...")
    git_ready = os.path.exists(".git")
    print(f"  [ {'OK' if git_ready else 'FAIL'} ] Git Repository")
    
    dev_server_ready = False
    # Simple check for common ports or config
    config_path = "doc-sync-config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            cfg = json.load(f)
            base_url = cfg.get("base_url", "http://localhost:3000")
            print(f"  [ INFO ] Base URL: {base_url}")
    
    if check_only:
        print("\nReadiness check complete.")
        return

    # 1. Check for staleness
    staleness_output = run_command(
        [sys.executable, "doc-regen/scripts/git_helper.py", "staleness"],
        "Checking documentation staleness"
    )
    
    if staleness_output:
        try:
            stale_docs = json.loads(staleness_output)
            if stale_docs:
                print(f"Found {len(stale_docs)} stale documents.")
                for doc in stale_docs:
                    print(f"  - {doc['file']} ({doc['changes_count']} changes)")
            else:
                print("All documentation is up to date with code changes.")
        except json.JSONDecodeError:
            print("Failed to parse staleness output.")

    # 2. Check for recipe changes
    recipe_output = run_command(
        [sys.executable, "doc-regen/scripts/git_helper.py", "check-recipes"],
        "Scanning for snapshot-recipe changes"
    )
    
    sync_needed = False
    if recipe_output:
        try:
            recipe_data = json.loads(recipe_output)
            if recipe_data.get("ui_sync_recommended"):
                print("!!! New or modified snapshot-recipes detected.")
                sync_needed = True
            else:
                print("No recent snapshot-recipe changes detected.")
        except json.JSONDecodeError:
            print("Failed to parse recipe check output.")

    # 3. Trigger UI Sync if needed or requested
    if sync_needed or "--force-sync" in sys.argv:
        print("\n>>> Triggering UI Documentation Sync...")
        # Assuming web-doc-tools is installed and has its venv
        updater_path = "web-doc-tools/skills/ui-doc-sync/scripts/updater.py"
        bot_path = "web-doc-tools/browser_bot.py"
        
        if os.path.exists(updater_path):
            # Try to use the venv if it exists, else use current python
            python_bin = "web-doc-tools/venv/bin/python3"
            if not os.path.exists(python_bin):
                python_bin = sys.executable
                
            sync_result = subprocess.run(
                [python_bin, updater_path, "--bot", bot_path],
                capture_output=False # Let it stream to console
            )
            if sync_result.returncode == 0:
                print("\nSuccess: Documentation visuals synchronized.")
            else:
                print("\nWarning: UI Sync failed. Ensure the local dev server is running.")
        else:
            print("\nError: web-doc-tools not found. Skipping visual sync.")

if __name__ == "__main__":
    main()
