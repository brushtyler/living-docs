# Upgrading from Living Docs 1.x

Skip this guide if you are installing Living Docs for the first time.

Living Docs 1.x was distributed primarily as a Gemini CLI Agent Skill. Most
1.x users do not call its bundled Python and Bash scripts themselves. For
those users, upgrading means replacing the old Gemini skill with the 2.0
package, skill, and MCP registration.

Existing `living-docs-config.json` files and Markdown `snapshot-recipe`
comments remain compatible. This is an installation and integration upgrade,
not a data conversion.

## If 1.x was installed as a Gemini skill

Remove the old skill before registering 2.0. Both versions use the
`living-docs` skill name, and `living-docs init` does not uninstall legacy
skill installations or files automatically.

1. In Gemini CLI, check whether the skill is currently discovered:

   ```text
   /skills list
   ```

2. From the system terminal, uninstall the old skill:

   ```bash
   gemini skills uninstall living-docs
   ```

3. Install Living Docs 2.0 and register the new Gemini skill and MCP server:

   ```bash
   uv tool install living-docs
   living-docs --version
   living-docs init --gemini
   ```

   Use `living-docs init -g --gemini` instead when the new integration should
   apply to every project for the current user.

4. Restart Gemini CLI, or reload skills and restart its MCP servers:

   ```text
   /skills reload
   ```

5. Start the configured development app, then verify the existing project
   data:

   ```bash
   living-docs doctor
   living-docs validate-recipes
   living-docs plan-sync
   ```

Uninstall the 1.x skill before running `living-docs init --gemini`.
Uninstalling `living-docs` afterward may remove the newly installed 2.0 skill
because it has the same name.

If `/skills list` no longer shows a 1.x Living Docs skill, no uninstall is
needed. A source directory from which the old skill was installed or linked
can be removed after 2.0 is verified; preserve the project-root
`living-docs-config.json` and Markdown documentation.

### Why remove the old skill?

Leaving 1.x installed can produce different outcomes depending on its scope
and installation method:

- a same-scope 2.0 initialization can replace `SKILL.md` while leaving unused
  1.x scripts and environment files behind;
- a 1.x skill at another scope or a still-linked source directory can remain
  discoverable alongside 2.0; and
- Gemini can load stale instructions that invoke the old scripts instead of
  the typed MCP tools.

The old skill does not corrupt compatible configuration or recipes, but it
can cause ambiguous activation, outdated behavior, missing-script failures,
or bypass 2.0 review, provenance, and security controls.

## If scripts are called directly

This section applies only when CI workflows, shell scripts, task runners, or
other automation invoke the implementation files bundled with the 1.x skill.
Normal Gemini Skill users do not need to translate these commands.

| Direct 1.x invocation | 2.0 command |
| --- | --- |
| `python living-docs/scripts/git_helper.py staleness` | `living-docs check-staleness` |
| `python living-docs/scripts/resolver.py FILE` | `living-docs resolve-route FILE` |
| `python living-docs/scripts/updater.py` | `living-docs apply-sync` |
| `python living-docs/scripts/orchestrator.py --force-sync` | `living-docs apply-sync` |
| `bash living-docs/scripts/run_bot.sh --tasks ...` | `living-docs capture --recipe ...` |

Install the package in the CI environment and replace each direct script
reference. There is no 2.0 activation script, skill-managed virtual
environment, or first-use dependency installation. For automation, use
`--json` and check the command exit status.

If these references are not replaced, that automation will fail once the old
skill directory or its scripts are removed. A copied 1.x installation might
continue temporarily, but it remains on the unsupported implementation and
does not gain 2.0 validation, filesystem/network boundaries, review artifacts,
or provenance.

## Compatibility notes

- Omitted `schema_version` is interpreted as version 1.
- Existing flows, mappings, and embedded recipes remain data-compatible.
- The new browser and security sections are optional.
- `security.allowed_origins` defaults to the configured `base_url` origin.
- Outputs default to the project root while enforcing path-traversal checks.
- `living-docs init` registers an already-installed executable; it does not
  install the Python package.

After upgrading, use the [five-minute quick start](README.md#five-minute-quick-start)
and [Gemini integration guidance](INTEGRATIONS.md#gemini-cli) for normal 2.0
operation.
