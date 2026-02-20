# pmctl

A CLI tool for managing Postman collections, environments, and workspaces.

The official Postman CLI only supports running collections. `pmctl` fills the gap by wrapping the [Postman API](https://www.postman.com/postman/postman-public-workspace/documentation/12946884/postman-api) to let you browse and manage your Postman resources from the terminal.

## Features

- 🔑 **Multi-profile support** — manage multiple Postman accounts with default workspaces
- 📦 **Browse collections** — list collections and inspect with tree view
- 🔍 **Request browser** — list, search (fuzzy match), and inspect individual requests across collections
- 🌍 **Environments** — list environments and view variables by name or ID
- 🏢 **Workspaces** — list and search workspaces
- 🐚 **Shell completion** — tab completion for bash, zsh, and fish
- 🎨 **Rich output** — colored tables and trees powered by [Rich](https://github.com/Textualize/rich)

## Installation

```bash
pip install pmctl
```

Or install from source:

```bash
git clone https://github.com/wbingli/pmctl.git
cd pmctl
pip install -e .
```

## Quick Start

### 1. Add a profile

```bash
# Add your Postman API key (get one at https://go.postman.co/settings/me/api-keys)
pmctl profile add personal --api-key "PMAK-..." --label "Personal Account" --default

# Add another profile (e.g., work account)
pmctl profile add work --api-key "PMAK-..." --label "Work Account"
```

### 2. Set a default workspace

```bash
# Set default workspace for your profile (so list commands scope to it automatically)
pmctl profile set-workspace <workspace-id>
```

### 3. Browse your resources

```bash
# List collections (scoped to default workspace)
pmctl collections list

# List collections from all workspaces
pmctl collections list --all

# Show all requests in a collection (tree view)
pmctl collections show <collection-uid>

# List all requests in a collection (flat table, by name or UID)
pmctl requests list --collection "My Collection"
pmctl requests list -c <collection-uid>

# Fuzzy search requests (characters matched in order, e.g. "crtUsr" matches "Create User")
pmctl requests list -c "My Collection" --search "getUser"

# Inspect a specific request by name
pmctl requests show "Create User" --collection "My Collection"

# JSON output for scripting
pmctl requests list -c "My Collection" --json
pmctl requests show "Create User" -c "My Collection" --json

# List environments
pmctl environments list

# Show environment variables (by name or ID)
pmctl environments show "My Environment"
pmctl environments show <env-id>

# List workspaces
pmctl workspaces list

# Search workspaces by name
pmctl workspaces list --search "keyword"
```

### 4. Switch between profiles

```bash
# Switch default profile
pmctl profile switch work

# Or use --profile flag on any command
pmctl collections list --profile personal

# Check who you're logged in as
pmctl profile whoami
```

## Profile Management

```bash
pmctl profile list                        # List all profiles
pmctl profile add <name>                  # Add a new profile
pmctl profile remove <name>               # Remove a profile
pmctl profile switch <name>               # Set default profile
pmctl profile set-workspace <workspace>   # Set default workspace for profile
pmctl profile whoami                      # Show current user info
```

## Configuration

Profiles are stored in `~/.config/pmctl/config.toml`:

```toml
[profiles.personal]
api_key = "PMAK-..."
label = "personal@example.com"

[profiles.work]
api_key = "PMAK-..."
label = "work@company.com"
workspace = "your-workspace-id"

default_profile = "work"
```

## Getting a Postman API Key

1. Go to [Postman API Keys](https://go.postman.co/settings/me/api-keys)
2. Click **Generate API Key**
3. Copy the key and add it with `pmctl profile add`

> **Note:** If you have multiple Postman accounts (e.g., personal + company SSO), each account has its own API keys page. Log into the correct account first.

## Shell Completion

```bash
# Bash
eval "$(pmctl completion bash)"

# Zsh
eval "$(pmctl completion zsh)"

# Fish
pmctl completion fish > ~/.config/fish/completions/pmctl.fish
```

## AI Agent Integrations

pmctl is designed to be used by both humans and AI agents. It ships with skill/plugin definitions for all major AI coding tools.

### Claude Code Plugin

This repo is a [Claude Code plugin](https://code.claude.com/docs/en/plugins). Point Claude Code at this directory:

```bash
claude --plugin-dir /path/to/pmctl
```

Skills are in `skills/pmctl/SKILL.md`. Claude Code will namespace them as `/pmctl:pmctl`.

### OpenAI Codex Skill

Skills are in `.agents/skills/pmctl/SKILL.md` following the [Agent Skills standard](https://agentskills.io). Codex picks them up automatically when you work inside this repo, or copy the skill folder to `~/.agents/skills/pmctl/` for global access.

### Cursor Plugin

This repo is a [Cursor plugin](https://cursor.com/docs/plugins/building.md). It includes both the plugin manifest (`.cursor-plugin/plugin.json`) and a skill (`skills/pmctl/SKILL.md`). Additionally, a rule file at `.cursor/rules/pmctl.mdc` is auto-loaded when you open this repo.

### OpenClaw (ClawHub)

Published on [ClawHub](https://clawhub.ai/skills/pmctl):

```bash
clawhub install pmctl
```

### Other AI Tools

The `skill/SKILL.md` file is a standalone skill definition that works with any tool supporting the [Agent Skills spec](https://agentskills.io). Copy it into your tool's skill directory.

## Publishing to ClawHub

To publish a new version:

```bash
# Login (one-time)
clawhub login

# Publish
clawhub publish ./skill --slug pmctl --name "pmctl" --version <version> --changelog "description" --tags latest
```

## License

MIT
