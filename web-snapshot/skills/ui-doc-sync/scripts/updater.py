import os
import re
import json
import subprocess
import argparse
import sys

# Regex to find images followed by recipes
# Matches: ![Alt](path) followed by <!-- snapshot-recipe: {JSON} -->
RECIPE_PATTERN = re.compile(
    r'!\[(?P<alt>.*?)\]\((?P<path>.*?)\)\s*\n\s*<!--\s*snapshot-recipe:\s*(?P<json>\{.*?\})\s*-->' ,
    re.DOTALL
)

def find_markdown_files(root_dir):
    md_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
    return md_files

def extract_recipes(md_file_path):
    with open(md_file_path, "r") as f:
        content = f.read()
    
    recipes = []
    for match in RECIPE_PATTERN.finditer(content):
        try:
            recipe_data = json.loads(match.group("json"))
            recipes.append({
                "alt": match.group("alt"),
                "image_path": match.group("path"),
                "tasks": recipe_data.get("tasks", []),
                "file": md_file_path,
                "span": match.span()
            })
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse JSON recipe in {md_file_path}")
            
    return recipes

def run_bot(bot_path, tasks, output_metadata=None):
    tasks_file = "temp_tasks.json"
    with open(tasks_file, "w") as f:
        json.dump(tasks, f)
    
    cmd = [sys.executable, bot_path, "--tasks", tasks_file]
    if output_metadata:
        cmd.extend(["--output-metadata", output_metadata])
    
    print(f"Running bot with {len(tasks)} tasks...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(tasks_file):
        os.remove(tasks_file)
        
    return result

def main():
    parser = argparse.ArgumentParser(description="Documentation Screenshot Updater")
    parser.add_argument("--dir", default=".", help="Directory to scan for Markdown files")
    parser.add_argument("--bot", required=True, help="Path to browser_bot.py")
    args = parser.parse_args()
    
    md_files = find_markdown_files(args.dir)
    all_recipes = []
    for md_file in md_files:
        recipes = extract_recipes(md_file)
        all_recipes.extend(recipes)
    
    if not all_recipes:
        print("No snapshot recipes found.")
        return

    print(f"Found {len(all_recipes)} recipes in {len(md_files)} files.")
    
    for i, recipe in enumerate(all_recipes):
        print(f"[{i+1}/{len(all_recipes)}] Updating {recipe['image_path']} for {recipe['file']}...")
        
        # Ensure image directory exists
        img_dir = os.path.dirname(os.path.join(os.path.dirname(recipe['file']), recipe['image_path']))
        if img_dir and not os.path.exists(img_dir):
            os.makedirs(img_dir)
            
        metadata_file = f"metadata_{i}.json"
        
        # Prepare tasks (ensure paths are correct relative to where the bot runs)
        # For simplicity, we assume the bot runs from the root and paths in recipes are root-relative or handled.
        # But usually they are relative to the MD file.
        md_dir = os.path.dirname(recipe['file'])
        adjusted_tasks = []
        for task in recipe['tasks']:
            new_task = task.copy()
            if 'filename' in new_task:
                new_task['filename'] = os.path.join(md_dir, new_task['filename'])
            adjusted_tasks.append(new_task)
            
        result = run_bot(args.bot, adjusted_tasks, metadata_file)
        
        if result.returncode != 0:
            print(f"Error updating {recipe['image_path']}: {result.stderr}")
        else:
            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as f:
                    meta = json.load(f)
                    print(f"  Extracted info: {json.dumps(meta, indent=2)}")
                os.remove(metadata_file)
            print(f"  Successfully updated {recipe['image_path']}")

if __name__ == "__main__":
    main()
