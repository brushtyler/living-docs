import sys
import os
import re
import json

def suggest_selectors(file_path):
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r', errors='ignore') as f:
        content = f.read()

    selectors = []
    
    # 1. Look for id="..."
    ids = re.findall(r'id=["\'](.*?)["\']', content)
    for i in ids:
        selectors.append(f"#{i}")

    # 2. Look for data-testid="..." or data-test="..."
    test_ids = re.findall(r'data-test(?:id)?=["\'](.*?)["\']', content)
    for ti in test_ids:
        selectors.append(f"[data-testid='{ti}']" if 'testid' in content else f"[data-test='{ti}']")

    # 3. Look for unique-looking class names
    # Simple heuristic: classes that aren't common utility classes (like mt-4, flex, etc.)
    classes = re.findall(r'className=["\'](.*?)["\']', content)
    for cl_list in classes:
        for cl in cl_list.split():
            if len(cl) > 3 and cl not in ['flex', 'grid', 'hidden', 'block', 'relative', 'absolute']:
                selectors.append(f".{cl}")

    return list(set(selectors))

def guess_component_name(file_path):
    # Use filename as base
    base = os.path.basename(file_path)
    name = os.path.splitext(base)[0]
    if name == 'page' or name == 'index':
        # Use parent directory name
        name = os.path.basename(os.path.dirname(file_path))
    
    # CamelCase to Space Case
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', name)
    return name.title()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python discovery_helper.py <file_path>")
        sys.exit(1)
    
    target = sys.argv[1]
    result = {
        "component_name": guess_component_name(target),
        "suggested_selectors": suggest_selectors(target)
    }
    print(json.dumps(result, indent=2))
