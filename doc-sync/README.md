# Documentation Sync Skill

The `doc-sync` skill automates the process of keeping your technical Markdown documentation in sync with your code. It focuses on technical accuracy and surgical text updates based on code changes.

## Features

- **Automated Text Sync**: Performs surgical updates to technical details in documentation.
- **Context-Aware Diffs**: Uses `doc-discovery` to pull relevant code changes since the doc's last commit.
- **Style Preservation**: Designed to update content while respecting your existing documentation structure.
- **Minimalist**: Focuses on text only; for visual snapshots, use the `ui-doc-sync` skill.

## Installation

```bash
gemini skills install doc-sync/doc-sync.skill --scope workspace
/skills reload
```

## Usage

Simply ask the Gemini CLI:
- "Sync code changes to markdown"
- "Update technical document text"
- "Update the README to include the new API endpoints I just added."

## How it Works

1. **Discovery**: Uses `doc-discovery` to identify the last commit for a document and list relevant code changes.
2. **Analysis**: The agent filters these changes for relevance to the document.
3. **Synthesis**: The agent applies the relevant changes to the technical sections of the Markdown content.

## Development

- `doc-sync.skill`: The skill manifest for Gemini CLI.
- `SKILL.md`: Instructions for the AI agent on how to perform text synchronization.
