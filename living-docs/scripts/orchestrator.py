import subprocess
import sys
import os
import json

def get_script_path(script_name):
    """Get the path to a script in the same directory as this orchestrator."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, script_name)
    if os.path.exists(path):
        return path
    return None

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
    
    config_path = "doc-sync-config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            cfg = json.load(f)
            base_url = cfg.get("base_url", "http://localhost:3000")
            print(f"  [ INFO ] Base URL: {base_url}")
    
    if check_only:
        print("\nReadiness check complete.")
        return

    # Find git_helper.py
    git_helper_path = get_script_path("git_helper.py")
    if not git_helper_path:
        print("Error: Could not find git_helper.py script.")
        sys.exit(1)

    # 1. Check for staleness
    staleness_output = run_command(
        [sys.executable, git_helper_path, "staleness"],
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
        [sys.executable, git_helper_path, "check-recipes"],
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
        
        updater_path = get_script_path("updater.py")
        bot_wrapper = get_script_path("run_bot.sh")
        
        if updater_path and bot_wrapper:
            # We call the updater, which will internally use run_bot.sh
            # The updater handles the bot path resolution itself now
            sync_result = subprocess.run(
                [sys.executable, updater_path],
                capture_output=False # Let it stream to console
            )
            if sync_result.returncode == 0:
                print("\nSuccess: Documentation visuals synchronized.")
            else:
                print("\nWarning: UI Sync failed. Ensure the local dev server is running.")
        else:
            print("\nError: Could not find updater or run_bot wrapper scripts. Skipping visual sync.")

if __name__ == "__main__":
    main()
