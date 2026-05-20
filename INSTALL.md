# Installation Guide: Living Docs

Follow these steps to set up the Living Docs pipeline in your local development environment.

## 1. System Requirements

Ensure your system meets the following prerequisites:
- **Git**: Required for change detection.
- **Python 3.12+**: Required for the orchestration and analysis scripts.
- **Google Chrome / Chromium**: Required for the visual snapshot engine (Selenium).

## 2. Project Environment Setup

Clone the repository and set up a virtual environment to manage dependencies.

```bash
# Clone the repository
git clone <repository-url> living-docs
cd living-docs

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install -r web-doc-tools/requirements.txt
```

## 3. Installing Gemini CLI Skills

Living Docs is composed of several specialized skills. For the best experience, you should install the **Master Orchestrator** and its supporting skills.

### Option A: The Full Pipeline (Recommended)
This installs all components needed for both text and visual synchronization.

```bash
# Install the Master Orchestrator (doc-regen)
gemini skills install doc-regen/ --scope workspace

# Install supporting skills
gemini skills install doc-sync/doc-sync.skill --scope workspace
gemini skills install doc-discovery/ --scope workspace
gemini skills install web-doc-tools/ui-doc-sync.skill --scope workspace
gemini skills install web-doc-tools/web-snapshot.skill --scope workspace

# Reload skills in your current session
/skills reload
```

### Option B: Individual Component Installation
If you only need specific capabilities, you can install skills individually.

- **doc-regen**: Master orchestrator (Pipeline).
- **doc-sync**: Technical text synchronization.
- **doc-discovery**: Documentation staleness and mapping.
- **ui-doc-sync**: Visual asset synchronization.
- **web-snapshot**: Low-level browser automation.

## 4. Post-Installation Verification

After installing the skills, verify that the environment is ready:

```bash
# Run the readiness check
python3 doc-regen/scripts/orchestrator.py --check-only
```

You should see an `[ OK ]` status for the Git Repository and a confirmed `Base URL`.

## 5. Connecting Your Project

To enable the pipeline for your specific project, ensure you have a `doc-sync-config.json` in your project root.

```json
{
  "base_url": "http://localhost:3000",
  "mappings": []
}
```

> [!IMPORTANT]
> The **Visual Sync** requires a running local development server. Ensure your app is running on the port specified in `base_url` before triggering a full sync.
