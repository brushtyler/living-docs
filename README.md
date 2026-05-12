# Gemini CLI Skills

A collection of specialized skills for the Gemini CLI to automate miscellaneous tasks.

## How to Install a Skill

To install a skill from this repository, use the `gemini skills install` command pointing to the `.skill` file of the desired skill.

Example for the Web Snapshot skill:

```bash
gemini skills install path/my.skill --scope workspace
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
