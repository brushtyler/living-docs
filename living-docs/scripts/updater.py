import os
import re
import json
import subprocess
import argparse
import sys

# Regex to find images followed by recipes
# Matches: ![Alt](path) followed by <!-- snapshot-recipe: {JSON} -->
RECIPE_PATTERN = re.compile(
    r'!\[(?P<alt>.*?)\]\((?P<path>.*?)\)\s*[\n\r]*\s*<!--\s*snapshot-recipe:\s*(?P<json>\{.*?\})\s*-->' ,
    re.DOTALL
)

def find_markdown_files(root_dir):
    md_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
    return md_files

def load_config(explicit_path=None, search_dir=None):
    if explicit_path:
        if os.path.exists(explicit_path):
            try:
                with open(explicit_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config from {explicit_path}: {e}")
        else:
            print(f"Warning: Explicit config path {explicit_path} not found.")

    # Search strategy: check search_dir, then CWD
    search_paths = []
    if search_dir:
        search_paths.append(os.path.join(search_dir, "doc-sync-config.json"))
    search_paths.append("doc-sync-config.json")

    for path in search_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config from {path}: {e}")
    
    return {}

def extract_recipes(md_file_path):
    with open(md_file_path, "r") as f:
        content = f.read()
    
    recipes = []
    for match in RECIPE_PATTERN.finditer(content):
        try:
            recipe_data = json.loads(match.group("json"))
            
            # Ensure prerequisites exists as a list, default to ['login'] if missing
            if "prerequisites" not in recipe_data:
                recipe_data["prerequisites"] = ["login"]
            
            recipe_data.update({
                "alt": match.group("alt"),
                "image_path": match.group("path"),
                "file": md_file_path,
                "span": match.span()
            })
            recipes.append(recipe_data)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse JSON recipe in {md_file_path}")
            
    return recipes

def run_bot(tasks, output_metadata=None):
    tasks_file = "temp_tasks.json"
    with open(tasks_file, "w") as f:
        json.dump(tasks, f)
    
    # Use the run_bot.sh wrapper located in the same scripts directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    run_bot_path = os.path.join(script_dir, "run_bot.sh")
    
    cmd = ["bash", run_bot_path, "--tasks", tasks_file]
    if output_metadata:
        cmd.extend(["--output-metadata", output_metadata])
    
    print(f"Running bot with {len(tasks)} tasks via {run_bot_path}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(tasks_file):
        os.remove(tasks_file)
        
    return result

def main():
    parser = argparse.ArgumentParser(description="Documentation Screenshot Updater")
    parser.add_argument("--dir", default=".", help="Directory to scan for Markdown files")
    parser.add_argument("--bot", help="Path to browser_bot.py (Legacy, no longer used as primary)")
    parser.add_argument("--config", help="Explicit path to doc-sync-config.json")
    parser.add_argument("--metadata", help="Path to save extracted UI metadata")
    args = parser.parse_args()
    
    config = load_config(explicit_path=args.config, search_dir=args.dir)
    base_url = config.get("base_url", "").rstrip("/")
    flows = config.get("flows", {})

    md_files = find_markdown_files(args.dir)
    all_recipes = []
    for md_file in md_files:
        recipes = extract_recipes(md_file)
        all_recipes.extend(recipes)
    
    if not all_recipes:
        print("No snapshot recipes found.")
        return

    print(f"Found {len(all_recipes)} recipes in {len(md_files)} files.")
    
    master_tasks = []
    
    for i, recipe in enumerate(all_recipes):
        md_dir = os.path.dirname(recipe['file'])
        
        # Ensure image directory exists
        img_full_path = os.path.join(md_dir, recipe['image_path'])
        img_dir = os.path.dirname(img_full_path)
        if img_dir and not os.path.exists(img_dir):
            os.makedirs(img_dir)
            
        # Expand tasks
        recipe_tasks = []
        
        # 1. Add flow tasks from prerequisites if they exist in config
        for flow_name in recipe.get("prerequisites", []):
            if flow_name in flows:
                recipe_tasks.extend(flows[flow_name])
        
        # 2. Add specific recipe tasks
        recipe_tasks.extend(recipe["tasks"])
        
        # Adjust tasks (resolve URLs and filenames)
        for task in recipe_tasks:
            new_task = task.copy()
            
            # Resolve relative URLs
            if 'url' in new_task and new_task['url'].startswith("/") and base_url:
                new_task['url'] = base_url + new_task['url']
                
            # Resolve filenames relative to MD file
            if 'filename' in new_task:
                new_task['filename'] = os.path.join(md_dir, new_task['filename'])
            
            master_tasks.append(new_task)

    if master_tasks:
        result = run_bot(master_tasks, args.metadata)
        
        if result.returncode != 0:
            print(f"Error updating screenshots: {result.stderr}")
        else:
            print(result.stdout)
            if args.metadata and os.path.exists(args.metadata):
                with open(args.metadata, "r") as f:
                    meta = json.load(f)
                    print(f"Successfully updated screenshots. Extracted metadata saved to {args.metadata}")
                    print(f"Extracted info: {json.dumps(meta, indent=2)}")
            else:
                print("Successfully updated all screenshots.")

if __name__ == "__main__":
    main()
