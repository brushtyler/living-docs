# Living Docs

**The Automated Documentation Pipeline for Gemini CLI**

*Documentation that stays in sync with code logic and UI visuals.*

## The Unified Documentation Pipeline

This repository provides a coordinated pipeline that bridges the gap between codebase changes and documentation accuracy. The pipeline automates three critical tasks:
1.  **Code-to-Text**: Synchronizing technical logic and API changes with Markdown text.
2.  **Code-to-Recipe**: Automatically discovering where UI components appear (URLs) and how to target them (CSS selectors).
3.  **UI-to-Snapshot**: Regenerating visual assets (screenshots) using a headless browser.

### Key Skills

#### [Codebase Documentation Synchronizer](./doc-regen)
The "Brain" of the pipeline. It uses Git history to detect stale documentation and orchestrates the update process.
- **Trigger**: "Regen documentation", "Update docs based on recent changes".
- **Capabilities**: Staleness detection, surgical text updates, and automated UI recipe generation.

#### [Web Documentation Tools](./web-doc-tools)
The "Execution" layer for visual documentation.
- **Web Snapshot**: A browser-automation engine powered by Selenium.
- **UI Doc Sync**: Scans documentation for `snapshot-recipe` blocks and refreshes image assets.

---

## How to Use the Pipeline

1.  **Installation**:
    ```bash
    gemini skills install doc-regen/doc-regen.skill --scope workspace
    gemini skills install web-doc-tools/web-snapshot.skill --scope workspace
    /skills reload
    ```

2.  **Standard Sync**: Simply ask the Gemini CLI:
    > "Update my documentation to reflect the latest changes in the codebase."

3.  **Extensible Mapping**: To support custom frameworks (non-Next.js), create a `doc-sync-config.json` in your project root:
    ```json
    {
      "base_url": "http://localhost:3000",
      "mappings": [
        {
          "pattern": "src/components/(.*)\\.tsx",
          "urls": ["/preview/{1}"]
        }
      ]
    }
    ```

---

## Testing & Sandbox

We provide a **Sandbox Environment** to verify the pipeline without impacting your main codebase.

### Running the Sandbox Test

1.  **Initial Setup** (First time only):
    ```bash
    virtualenv sandbox/venv
    sandbox/venv/bin/pip install -r sandbox/requirements.txt
    ```

2.  **Start the Mock Server**:
    ```bash
    sandbox/venv/bin/python3 sandbox/mock_server.py
    ```

3.  **Modify a Component**: Change a color or text in `sandbox/app/page.tsx`.

4.  **Trigger Sync**: Ask the CLI to "Update sandbox documentation".

5.  **Verify**: Check `sandbox/docs/assets/sandbox.png` for the updated visual.

---

## How to Install a Skill

To install a skill from this repository, use the `gemini skills install` command pointing to the `.skill` file of the desired skill.

Example for the Web Snapshot skill:

```bash
gemini skills install web-doc-tools/web-snapshot.skill --scope workspace
```

After installation, you can reload the skills in your Gemini CLI session:

```bash
/skills reload
```
## Contributing

We welcome contributions of new skills! To add a new skill:

1. Create a new directory for your skill.
2. Follow the standard skill structure (including `SKILL.md`, scripts, and necessary assets).
3. Package your skill into a `.skill` file.
4. Provide a `README.md` within the skill directory.
5. Update this root `README.md` to include your skill in the "Available Skills" list.

## License

This repository is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
