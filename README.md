# pmctl

A CLI tool for managing Postman collections, environments, and workspaces.

The official Postman CLI only supports running collections. `pmctl` fills the gap by wrapping the [Postman API](https://www.postman.com/postman/postman-public-workspace/documentation/12946884/postman-api) to let you browse and manage your Postman resources from the terminal.

## Features

- 🔑 **Multi-profile support** — manage multiple Postman accounts (personal, work, etc.)
- 📦 **Browse collections** — list and inspect collections with a beautiful tree view
- 🌍 **Environments** — list environments and view variables
- 🏢 **Workspaces** — list all accessible workspaces
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

### 2. Browse your resources

```bash
# List collections
pmctl collections list

# List collections in a specific workspace
pmctl collections list --workspace <workspace-id>

# Show all requests in a collection (tree view)
pmctl collections show <collection-uid>

# List environments
pmctl environments list

# Show environment variables
pmctl environments show <env-id> --values

# List workspaces
pmctl workspaces list
```

### 3. Switch between profiles

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
pmctl profile list          # List all profiles
pmctl profile add <name>    # Add a new profile
pmctl profile remove <name> # Remove a profile
pmctl profile switch <name> # Set default profile
pmctl profile whoami        # Show current user info
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

default_profile = "work"
```

## Getting a Postman API Key

1. Go to [Postman API Keys](https://go.postman.co/settings/me/api-keys)
2. Click **Generate API Key**
3. Copy the key and add it with `pmctl profile add`

> **Note:** If you have multiple Postman accounts (e.g., personal + company SSO), each account has its own API keys page. Log into the correct account first.

## License

MIT
