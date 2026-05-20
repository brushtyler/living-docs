import subprocess
import sys
import os
import json

def find_script_path(skill_name, relative_path, dev_fallback_paths=None):
    # 1. Try finding in the sibling directory (under .gemini/skills or .agents/skills or development setup)
    try:
        skills_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(skills_dir, skill_name, relative_path)
        if os.path.exists(path):
            return path
    except Exception:
        pass

    # 2. Try directly relative to the current working directory
    fallback_path = os.path.join(skill_name, relative_path)
    if os.path.exists(fallback_path):
        return fallback_path

    # 3. Try dev fallback paths relative to CWD
    if dev_fallback_paths:
        for dev_path in dev_fallback_paths:
            if os.path.exists(dev_path):
                return dev_path

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
    git_helper_path = find_script_path("doc-discovery", "scripts/git_helper.py")
    if not git_helper_path:
        print("Error: Could not find doc-discovery git_helper.py script.")
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
        
        updater_path = find_script_path("ui-doc-sync", "scripts/updater.py", [
            "web-doc-tools/skills/ui-doc-sync/scripts/updater.py"
        ])
        bot_path = find_script_path("web-snapshot", "scripts/browser_bot.py", [
            "web-doc-tools/browser_bot.py"
        ])
        
        if updater_path and bot_path:
            # Try to use the venv if it exists, else use current python
            python_bin = "web-doc-tools/venv/bin/python3"
            if not os.path.exists(python_bin):
                # check if there's a venv in the sibling ui-doc-sync folder
                ui_doc_sync_dir = os.path.dirname(os.path.dirname(updater_path))
                sibling_python_bin = os.path.join(ui_doc_sync_dir, "venv", "bin", "python3")
                if os.path.exists(sibling_python_bin):
                    python_bin = sibling_python_bin
                else:
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
            print("\nError: Could not find ui-doc-sync or browser_bot scripts. Skipping visual sync.")

if __name__ == "__main__":
    main()
