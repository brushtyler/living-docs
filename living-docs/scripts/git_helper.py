import subprocess
import json
import sys
import os

def run_git(args):
    try:
        result = subprocess.run(['git'] + args, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def is_git_repo():
    return run_git(['rev-parse', '--is-inside-work-tree']) == 'true'

def get_last_commit(file_path):
    commit = run_git(['log', '-n', '1', '--pretty=format:%H', '--', file_path])
    if not commit:
        # If the file is not in git history, try to find the first commit of the repo
        commit = run_git(['rev-list', '--max-parents=0', 'HEAD'])
    return commit

def get_changed_files(since_commit, include_uncommitted=True):
    args = ['diff', '--name-only', since_commit]
    if not include_uncommitted:
        args = ['diff', '--name-only', f'{since_commit}..HEAD']
    
    output = run_git(args)
    if output:
        return [f for f in output.split('\n') if f]
    return []

def main():
    if not is_git_repo():
        print(json.dumps({"error": "Not a git repository"}))
        sys.exit(0)

    command = sys.argv[1] if len(sys.argv) > 1 else 'status'

    if command == 'staleness':
        # Find all markdown files
        md_files = []
        for root, _, files in os.walk('.'):
            if '.git' in root or 'venv' in root or 'node_modules' in root:
                continue
            for f in files:
                if f.endswith('.md'):
                    md_files.append(os.path.relpath(os.path.join(root, f), '.'))
        
        results = []
        for doc in md_files:
            last_commit = get_last_commit(doc)
            if not last_commit:
                continue
            
            changed = get_changed_files(last_commit)
            if changed:
                results.append({
                    "file": doc,
                    "last_commit": last_commit,
                    "changes_count": len(changed),
                    "changed_files": changed
                })
        
        print(json.dumps(results, indent=2))

    elif command == 'diff':
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing file path for diff"}))
            sys.exit(1)
        
        doc_file = sys.argv[2]
        last_commit = get_last_commit(doc_file)
        if not last_commit:
            print(json.dumps({"error": f"Could not find git history for {doc_file}"}))
            sys.exit(1)
            
        # Get diff of all changes since then (including uncommitted)
        diff_text = run_git(['diff', last_commit])
        print(diff_text)

    elif command == 'check-recipes':
        # Check if any snapshot-recipe blocks were added or modified in unstaged/staged changes
        diff_text = run_git(['diff', 'HEAD'])
        staged_diff = run_git(['diff', '--cached'])
        
        full_diff = (diff_text or "") + "\n" + (staged_diff or "")
        
        # Look for "snapshot-recipe" in added lines (starting with +)
        recipe_changes = []
        for line in full_diff.split('\n'):
            if line.startswith('+') and 'snapshot-recipe' in line:
                recipe_changes.append(line)
        
        result = {
            "ui_sync_recommended": len(recipe_changes) > 0,
            "changes_detected": len(recipe_changes),
            "summary": f"Detected {len(recipe_changes)} new or modified snapshot-recipes."
        }
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
