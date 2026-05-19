# Documentation Regeneration Skill

The `doc-regen` skill automates the process of keeping your Markdown documentation in sync with your code. It uses Git history to detect when a document has become "stale" (i.e., when the codebase has changed since the document was last updated) and helps the AI agent perform surgical updates.

## Features

- **Automated Staleness Check**: Instantly see which docs are out of date.
- **Visual Sync**: Automatically identifies UI components, resolves their URLs (Next.js support), and generates/updates `snapshot-recipes`.
- **Context-Aware Diffs**: Pulls only the relevant code changes since the doc's last commit.
- **Style Preservation**: Designed to update content while respecting your existing documentation structure.
- **Git Fallback**: Works even in non-Git environments by analyzing the current session's modified files.

## Installation

```bash
gemini skills install doc-regen/doc-regen.skill --scope workspace
/skills reload
```

## Usage

Simply ask the Gemini CLI:
- "Are my docs up to date?"
- "Regen the user guide based on my last 5 commits."
- "Update the README to include the new API endpoints I just added."

## How it Works

1. **Detection**: The skill identifies the last commit hash for a specific `.md` file.
2. **Analysis**: It lists all files changed between that commit and `HEAD`.
3. **Filtering**: The agent filters these changes for relevance to the document.
4. **Synthesis**: The agent applies the relevant changes to the document content.

## Development

- `scripts/git_helper.py`: A Python utility for Git operations.
- `SKILL.md`: The "brain" of the skill, providing instructions to the AI agent.
- `doc-regen.skill`: The skill manifest for Gemini CLI.
