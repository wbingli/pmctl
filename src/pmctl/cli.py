"""pmctl - CLI entry point."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from pmctl.api import PostmanClient
from pmctl.config import (
    add_profile,
    load_config,
    remove_profile,
    set_default_profile,
    set_profile_workspace,
)

app = typer.Typer(
    name="pmctl",
    help="A CLI tool for managing Postman collections, environments, and workspaces.",
    no_args_is_help=True,
)
console = Console()

# --- Profile subcommand ---

profile_app = typer.Typer(help="Manage Postman API key profiles.", no_args_is_help=True)
app.add_typer(profile_app, name="profile")


@profile_app.command("list")
def profile_list():
    """List all configured profiles."""
    config = load_config()
    table = Table(title="Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Label", style="dim")
    table.add_column("Default", style="green")
    table.add_column("Workspace", style="dim")
    table.add_column("API Key", style="dim")

    for prof_name, profile in config.profiles.items():
        is_default = "✓" if prof_name == config.default_profile else ""
        masked_key = profile.api_key[:12] + "..." + profile.api_key[-4:]
        ws = profile.workspace[:12] + "..." if len(profile.workspace) > 12 else profile.workspace
        table.add_row(prof_name, profile.label, is_default, ws, masked_key)

    console.print(table)


@profile_app.command("add")
def profile_add(
    name: str = typer.Argument(help="Profile name"),
    api_key: str = typer.Option(..., "--api-key", "-k", help="Postman API key"),
    label: str = typer.Option("", "--label", "-l", help="Description label"),
    default: bool = typer.Option(False, "--default", "-d", help="Set as default profile"),
):
    """Add a new profile."""
    config = add_profile(name, api_key, label, set_default=default)
    console.print(f"[green]✓[/] Profile '{name}' added.")
    if name == config.default_profile:
        console.print(f"[green]✓[/] Set as default profile.")


@profile_app.command("remove")
def profile_remove(name: str = typer.Argument(help="Profile name to remove")):
    """Remove a profile."""
    remove_profile(name)
    console.print(f"[green]✓[/] Profile '{name}' removed.")


@profile_app.command("switch")
def profile_switch(name: str = typer.Argument(help="Profile name to set as default")):
    """Switch the default profile."""
    set_default_profile(name)
    console.print(f"[green]✓[/] Default profile switched to '{name}'.")


@profile_app.command("set-workspace")
def profile_set_workspace(
    workspace_id: str = typer.Argument(help="Default workspace ID for this profile"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to update (default: current default)"),
):
    """Set the default workspace for a profile."""
    config = set_profile_workspace(profile or "", workspace_id)
    name = profile or config.default_profile
    console.print(f"[green]✓[/] Default workspace for '{name}' set to '{workspace_id}'.")


@profile_app.command("whoami")
def profile_whoami(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
):
    """Show current user info for the active profile."""
    config = load_config()
    p = config.get_profile(profile)
    with PostmanClient(p.api_key) as client:
        user = client.get_me().get("user", {})
    console.print(f"[cyan]Email:[/]  {user.get('email', 'N/A')}")
    console.print(f"[cyan]Name:[/]   {user.get('fullName', 'N/A')}")
    console.print(f"[cyan]Team:[/]   {user.get('teamName', 'N/A')}")
    console.print(f"[cyan]Domain:[/] {user.get('teamDomain', 'N/A')}")


# --- Workspaces subcommand ---

workspace_app = typer.Typer(help="Manage Postman workspaces.", no_args_is_help=True)
app.add_typer(workspace_app, name="workspaces")


@workspace_app.command("list")
def workspaces_list(
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Filter workspaces by name (case-insensitive)"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
):
    """List all accessible workspaces."""
    config = load_config()
    p = config.get_profile(profile)
    with PostmanClient(p.api_key) as client:
        workspaces = client.list_workspaces()

    if search:
        keyword = search.lower()
        workspaces = [ws for ws in workspaces if keyword in ws["name"].lower()]

    table = Table(title=f"Workspaces ({p.label or p.name})")
    table.add_column("Name", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Type", style="green")

    for ws in sorted(workspaces, key=lambda w: w["name"].lower()):
        table.add_row(ws["name"], ws["id"], ws.get("type", ""))

    console.print(table)
    console.print(f"\n[dim]Total: {len(workspaces)} workspaces[/]")


# --- Collections subcommand ---

collection_app = typer.Typer(help="Manage Postman collections.", no_args_is_help=True)
app.add_typer(collection_app, name="collections")


@collection_app.command("list")
def collections_list(
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Filter by workspace ID"),
    all_workspaces: bool = typer.Option(False, "--all", "-a", help="Show collections from all workspaces"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
):
    """List collections."""
    config = load_config()
    p = config.get_profile(profile)
    effective_workspace = workspace or (None if all_workspaces else p.workspace or None)
    with PostmanClient(p.api_key) as client:
        collections = client.list_collections(workspace_id=effective_workspace)

    table = Table(title=f"Collections ({p.label or p.name})")
    table.add_column("Name", style="cyan")
    table.add_column("UID", style="dim")
    table.add_column("Updated", style="dim")

    for col in sorted(collections, key=lambda c: c["name"].lower()):
        updated = col.get("updatedAt", "")[:10]
        table.add_row(col["name"], col["uid"], updated)

    console.print(table)
    console.print(f"\n[dim]Total: {len(collections)} collections[/]")


@collection_app.command("show")
def collections_show(
    uid: str = typer.Argument(help="Collection UID"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
):
    """Show all requests in a collection as a tree."""
    config = load_config()
    p = config.get_profile(profile)
    with PostmanClient(p.api_key) as client:
        collection = client.get_collection(uid)

    tree = Tree(f"[bold cyan]{collection.get('info', {}).get('name', 'Collection')}[/]")
    _build_tree(tree, collection.get("item", []))
    console.print(tree)


def _build_tree(tree: Tree, items: list) -> None:
    """Recursively build a Rich tree from collection items."""
    for item in items:
        if "item" in item:
            # It's a folder
            branch = tree.add(f"📁 [bold]{item['name']}[/]")
            _build_tree(branch, item["item"])
        else:
            # It's a request
            req = item.get("request", {})
            method = req.get("method", "?")
            url = req.get("url", {})
            raw_url = url.get("raw", url) if isinstance(url, dict) else url

            method_colors = {
                "GET": "green",
                "POST": "yellow",
                "PUT": "blue",
                "PATCH": "magenta",
                "DELETE": "red",
            }
            color = method_colors.get(method, "white")
            tree.add(f"[bold {color}]{method:7s}[/] {item['name']}  [dim]{raw_url}[/]")


# --- Environments subcommand ---

env_app = typer.Typer(help="Manage Postman environments.", no_args_is_help=True)
app.add_typer(env_app, name="environments")


@env_app.command("list")
def environments_list(
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Filter by workspace ID"),
    all_workspaces: bool = typer.Option(False, "--all", "-a", help="Show environments from all workspaces"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
):
    """List environments."""
    config = load_config()
    p = config.get_profile(profile)
    effective_workspace = workspace or (None if all_workspaces else p.workspace or None)
    with PostmanClient(p.api_key) as client:
        environments = client.list_environments(workspace_id=effective_workspace)

    table = Table(title=f"Environments ({p.label or p.name})")
    table.add_column("Name", style="cyan")
    table.add_column("ID", style="dim")

    for env in sorted(environments, key=lambda e: e["name"].lower()):
        table.add_row(env["name"], env["id"])

    console.print(table)
    console.print(f"\n[dim]Total: {len(environments)} environments[/]")


@env_app.command("show")
def environments_show(
    env_id: str = typer.Argument(help="Environment ID"),
    show_values: bool = typer.Option(False, "--values", "-v", help="Show variable values"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
):
    """Show environment variables."""
    config = load_config()
    p = config.get_profile(profile)
    with PostmanClient(p.api_key) as client:
        env = client.get_environment(env_id)

    console.print(f"[bold cyan]{env.get('name', 'Environment')}[/]\n")

    table = Table()
    table.add_column("Variable", style="cyan")
    table.add_column("Type", style="dim")
    if show_values:
        table.add_column("Value")

    for var in env.get("values", []):
        row = [var["key"], var.get("type", "default")]
        if show_values:
            value = var.get("value", "")
            # Mask sensitive-looking values
            if any(k in var["key"].lower() for k in ("password", "secret", "token", "key")):
                value = value[:4] + "****" if len(value) > 4 else "****"
            row.append(value)
        table.add_row(*row)

    console.print(table)


# --- Completion subcommand ---

completion_app = typer.Typer(help="Generate shell completion scripts.", no_args_is_help=True)
app.add_typer(completion_app, name="completion")


def _print_completion_script(shell: str) -> None:
    """Generate and print a shell completion script."""
    from click.shell_completion import get_completion_class

    click_app = typer.main.get_command(app)
    comp_cls = get_completion_class(shell)
    if comp_cls is None:
        console.print(f"[red]Error:[/] Unsupported shell '{shell}'.")
        raise typer.Exit(1)
    comp = comp_cls(click_app, {}, "pmctl", "_PMCTL_COMPLETE")
    typer.echo(comp.source())


@completion_app.command("bash")
def completion_bash():
    """Generate bash completion script.

    Usage:  eval "$(pmctl completion bash)"
    """
    _print_completion_script("bash")


@completion_app.command("zsh")
def completion_zsh():
    """Generate zsh completion script.

    Usage:  eval "$(pmctl completion zsh)"
    """
    _print_completion_script("zsh")


@completion_app.command("fish")
def completion_fish():
    """Generate fish completion script.

    Usage:  pmctl completion fish > ~/.config/fish/completions/pmctl.fish
    """
    _print_completion_script("fish")


if __name__ == "__main__":
    app()
