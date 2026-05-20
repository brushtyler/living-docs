import os
import json
import sys
import re

class RouteResolver:
    def __init__(self, root_dir=".", config_file="living-docs-config.json"):
        self.root_dir = root_dir
        self.config_path = os.path.join(root_dir, config_file)
        self.config = self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}", file=sys.stderr)
        return {}

    def resolve(self, file_path):
        urls = set()
        
        # 1. Custom Mappings from Config
        custom_mappings = self.config.get("mappings", [])
        for mapping in custom_mappings:
            pattern = mapping.get("pattern")
            if pattern and re.search(pattern, file_path):
                mapping_urls = mapping.get("urls", [])
                for u in mapping_urls:
                    urls.add(u)

        # 2. Next.js App Router Logic
        if "app/" in file_path and (file_path.endswith("page.tsx") or file_path.endswith("page.js")):
            # Convert app/login/page.tsx -> /login
            # Handle (groups) like app/(auth)/login/page.tsx -> /login
            rel_path = os.path.relpath(file_path, start="app" if "app/" in file_path[:4] else ".")
            if rel_path.startswith("app/"):
                rel_path = rel_path[4:]
            
            route = "/" + os.path.dirname(rel_path)
            route = re.sub(r'/\(.*\)', '', route) # Remove (groups)
            route = route.replace("\\", "/")
            if route == "/.": route = "/"
            urls.add(route)

        # 3. Next.js Pages Router Logic
        if "pages/" in file_path:
            rel_path = os.path.relpath(file_path, start="pages" if "pages/" in file_path[:6] else ".")
            if rel_path.startswith("pages/"):
                rel_path = rel_path[6:]
                
            route = "/" + os.path.splitext(rel_path)[0]
            route = route.replace("/index", "")
            route = route.replace("\\", "/")
            if route == "": route = "/"
            urls.add(route)

        return list(urls)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python resolver.py <file_path>")
        sys.exit(1)
    
    resolver = RouteResolver()
    file_to_resolve = sys.argv[1]
    results = resolver.resolve(file_to_resolve)
    print(json.dumps(results))
