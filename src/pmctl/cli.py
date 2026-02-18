"""pmctl - CLI entry point."""

from __future__ import annotations

import json as json_mod
import sys
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
    no_args_is_help=True,
)
console = Console()

_json_output: bool = False


@app.callback()
def main_callback(
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON instead of formatted text"),
):
    """A CLI tool for managing Postman collections, environments, and workspaces."""
    global _json_output
    _json_output = json_output


def _set_json_output(value: bool) -> bool:
    global _json_output
    if value:
        _json_output = True
    return value


def _print_json(data: dict | list) -> None:
    sys.stdout.write(json_mod.dumps(data, indent=2, default=str) + "\n")
    sys.stdout.flush()

# --- Profile subcommand ---

profile_app = typer.Typer(help="Manage Postman API key profiles.", no_args_is_help=True)
app.add_typer(profile_app, name="profile")


@profile_app.command("list")
def profile_list(
    json: bool = typer.Option(False, "--json", help="Output raw JSON instead of formatted text", callback=_set_json_output, is_eager=True),
):
    """List all configured profiles."""
    config = load_config()

    if _json_output:
        data = {
            "default_profile": config.default_profile,
            "profiles": {
                name: {
                    "label": prof.label,
                    "api_key": prof.api_key,
                    "workspace": prof.workspace,
                }
                for name, prof in config.profiles.items()
            },
        }
        _print_json(data)
        raise typer.Exit()

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
    json: bool = typer.Option(False, "--json", help="Output raw JSON instead of formatted text", callback=_set_json_output, is_eager=True),
):
    """Show current user info for the active profile."""
    config = load_config()
    p = config.get_profile(profile)
    with PostmanClient(p.api_key) as client:
        me = client.get_me()

    if _json_output:
        _print_json(me)
        raise typer.Exit()

    user = me.get("user", {})
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
    json: bool = typer.Option(False, "--json", help="Output raw JSON instead of formatted text", callback=_set_json_output, is_eager=True),
):
    """List all accessible workspaces."""
    config = load_config()
    p = config.get_profile(profile)
    with PostmanClient(p.api_key) as client:
        workspaces = client.list_workspaces()

    if search:
        keyword = search.lower()
        workspaces = [ws for ws in workspaces if keyword in ws["name"].lower()]

    if _json_output:
        _print_json(workspaces)
        raise typer.Exit()

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
    json: bool = typer.Option(False, "--json", help="Output raw JSON instead of formatted text", callback=_set_json_output, is_eager=True),
):
    """List collections."""
    config = load_config()
    p = config.get_profile(profile)
    effective_workspace = workspace or (None if all_workspaces else p.workspace or None)
    with PostmanClient(p.api_key) as client:
        collections = client.list_collections(workspace_id=effective_workspace)

    if _json_output:
        _print_json(collections)
        raise typer.Exit()

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
    json: bool = typer.Option(False, "--json", help="Output raw JSON instead of formatted text", callback=_set_json_output, is_eager=True),
):
    """Show all requests in a collection as a tree."""
    config = load_config()
    p = config.get_profile(profile)
    with PostmanClient(p.api_key) as client:
        collection = client.get_collection(uid)

    if _json_output:
        _print_json(collection)
        raise typer.Exit()

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


@collection_app.command("request")
def collections_request(
    uid: str = typer.Argument(help="Collection UID"),
    name: str = typer.Argument(help="Request name (case-insensitive substring match)"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
    json: bool = typer.Option(False, "--json", help="Output raw JSON instead of formatted text", callback=_set_json_output, is_eager=True),
):
    """Show details of a specific request in a collection."""
    config = load_config()
    p = config.get_profile(profile)
    with PostmanClient(p.api_key) as client:
        collection = client.get_collection(uid)

    matches = _find_requests(collection.get("item", []), name)
    if not matches:
        if _json_output:
            _print_json([])
            raise typer.Exit(1)
        console.print(f"[red]No request matching '{name}' found.[/]")
        raise typer.Exit(1)

    if _json_output:
        data = [{"path": path, **item} for path, item in matches]
        _print_json(data)
        raise typer.Exit()

    if len(matches) > 1:
        console.print(f"[yellow]Multiple matches found ({len(matches)}). Showing first match.[/]")
        for i, (path, _) in enumerate(matches):
            console.print(f"  [dim]{i + 1}. {path}[/]")
        console.print()

    path, item = matches[0]
    req = item.get("request", {})
    method = req.get("method", "?")
    url = req.get("url", {})
    raw_url = url.get("raw", url) if isinstance(url, dict) else url

    method_colors = {
        "GET": "green", "POST": "yellow", "PUT": "blue",
        "PATCH": "magenta", "DELETE": "red",
    }
    color = method_colors.get(method, "white")

    console.print(f"[bold]{path}[/]\n")
    console.print(f"[bold {color}]{method}[/] {raw_url}\n")

    # Auth
    auth = req.get("auth")
    if auth:
        auth_type = auth.get("type", "unknown")
        console.print(f"[cyan]Auth:[/] {auth_type}")

    # Headers
    headers = req.get("header", [])
    if headers:
        table = Table(title="Headers", show_edge=False)
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        table.add_column("Enabled", style="dim")
        for h in headers:
            enabled = "✗" if h.get("disabled") else "✓"
            table.add_row(h.get("key", ""), h.get("value", ""), enabled)
        console.print(table)

    # Query params
    if isinstance(url, dict):
        query = url.get("query", [])
        if query:
            table = Table(title="Query Params", show_edge=False)
            table.add_column("Key", style="cyan")
            table.add_column("Value")
            table.add_column("Enabled", style="dim")
            for q in query:
                enabled = "✗" if q.get("disabled") else "✓"
                table.add_row(q.get("key", ""), q.get("value", ""), enabled)
            console.print(table)

        # Path variables
        variables = url.get("variable", [])
        if variables:
            table = Table(title="Path Variables", show_edge=False)
            table.add_column("Key", style="cyan")
            table.add_column("Value")
            for v in variables:
                table.add_row(v.get("key", ""), v.get("value", ""))
            console.print(table)

    # Body
    body = req.get("body")
    if body:
        mode = body.get("mode", "")
        console.print(f"\n[cyan]Body[/] [dim]({mode})[/]")
        if mode == "raw":
            raw = body.get("raw", "")
            if raw:
                console.print(raw)
        elif mode == "formdata":
            table = Table(show_edge=False)
            table.add_column("Key", style="cyan")
            table.add_column("Value")
            table.add_column("Type", style="dim")
            for fd in body.get("formdata", []):
                table.add_row(fd.get("key", ""), fd.get("value", ""), fd.get("type", "text"))
            console.print(table)
        elif mode == "urlencoded":
            table = Table(show_edge=False)
            table.add_column("Key", style="cyan")
            table.add_column("Value")
            for ue in body.get("urlencoded", []):
                table.add_row(ue.get("key", ""), ue.get("value", ""))
            console.print(table)


def _find_requests(items: list, name: str, prefix: str = "") -> list[tuple[str, dict]]:
    """Recursively find requests matching a name (case-insensitive substring)."""
    matches = []
    keyword = name.lower()
    for item in items:
        path = f"{prefix}/{item['name']}" if prefix else item["name"]
        if "item" in item:
            matches.extend(_find_requests(item["item"], name, path))
        elif keyword in item["name"].lower():
            matches.append((path, item))
    return matches


# --- Environments subcommand ---


def _resolve_and_get_environment(client: PostmanClient, id_or_name: str, workspace_id: Optional[str] = None) -> dict:
    """Resolve an environment by ID or name, then fetch its details."""
    # Try direct ID lookup first
    try:
        return client.get_environment(id_or_name)
    except Exception:
        pass

    # Fall back to name matching via list
    environments = client.list_environments(workspace_id=workspace_id)
    matches = [e for e in environments if e["name"].lower() == id_or_name.lower()]
    if len(matches) == 1:
        return client.get_environment(matches[0]["id"])
    if len(matches) > 1:
        names = ", ".join(f'{m["name"]} ({m["id"]})' for m in matches)
        raise typer.BadParameter(f"Multiple environments match '{id_or_name}': {names}. Use the ID instead.")
    raise typer.BadParameter(f"Environment '{id_or_name}' not found. Run 'pmctl environments list' to see available environments.")


env_app = typer.Typer(help="Manage Postman environments.", no_args_is_help=True)
app.add_typer(env_app, name="environments")


@env_app.command("list")
def environments_list(
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Filter by workspace ID"),
    all_workspaces: bool = typer.Option(False, "--all", "-a", help="Show environments from all workspaces"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
    json: bool = typer.Option(False, "--json", help="Output raw JSON instead of formatted text", callback=_set_json_output, is_eager=True),
):
    """List environments."""
    config = load_config()
    p = config.get_profile(profile)
    effective_workspace = workspace or (None if all_workspaces else p.workspace or None)
    with PostmanClient(p.api_key) as client:
        environments = client.list_environments(workspace_id=effective_workspace)

    if _json_output:
        _print_json(environments)
        raise typer.Exit()

    table = Table(title=f"Environments ({p.label or p.name})")
    table.add_column("Name", style="cyan")
    table.add_column("ID", style="dim")

    for env in sorted(environments, key=lambda e: e["name"].lower()):
        table.add_row(env["name"], env["id"])

    console.print(table)
    console.print(f"\n[dim]Total: {len(environments)} environments[/]")


@env_app.command("show")
def environments_show(
    env_id_or_name: str = typer.Argument(help="Environment ID or name"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace ID (for name lookup)"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to use"),
    full: bool = typer.Option(False, "--full", "-f", help="Show full values on separate lines (no truncation)"),
    json: bool = typer.Option(False, "--json", help="Output raw JSON instead of formatted text", callback=_set_json_output, is_eager=True),
):
    """Show environment variables."""
    config = load_config()
    p = config.get_profile(profile)
    with PostmanClient(p.api_key) as client:
        env = _resolve_and_get_environment(client, env_id_or_name, workspace or p.workspace)

    if _json_output:
        _print_json(env)
        raise typer.Exit()

    console.print(f"[bold cyan]{env.get('name', 'Environment')}[/]\n")

    values = env.get("values", [])
    for var in values:
        value = var.get("value", "")
        if any(k in var["key"].lower() for k in ("password", "secret", "token", "key")):
            value = value[:4] + "****" if len(value) > 4 else "****"
        var["_display_value"] = value

    if full:
        for var in values:
            var_type = var.get("type", "default")
            console.print(f"[cyan]{var['key']}[/] [dim]({var_type})[/]")
            console.print(f"  {var['_display_value']}", soft_wrap=True)
            console.print()
    else:
        table = Table()
        table.add_column("Variable", style="cyan")
        table.add_column("Type", style="dim")
        table.add_column("Value")

        for var in values:
            table.add_row(var["key"], var.get("type", "default"), var["_display_value"])

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
