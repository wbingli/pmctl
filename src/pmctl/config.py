"""Configuration management for pmctl.

Manages multiple Postman API key profiles stored in ~/.config/pmctl/config.toml.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".config" / "pmctl"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass
class Profile:
    """A Postman API key profile."""

    name: str
    api_key: str
    label: str = ""


@dataclass
class Config:
    """Application configuration."""

    profiles: dict[str, Profile]
    default_profile: str

    def get_profile(self, name: Optional[str] = None) -> Profile:
        """Get a profile by name, or the default profile."""
        profile_name = name or self.default_profile
        if profile_name not in self.profiles:
            available = ", ".join(self.profiles.keys())
            raise ValueError(
                f"Profile '{profile_name}' not found. Available profiles: {available}"
            )
        return self.profiles[profile_name]


def _ensure_config_dir() -> None:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    """Load configuration from TOML file."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Config file not found at {CONFIG_FILE}\n"
            f"Run 'pmctl profile add <name> --api-key <key>' to create one."
        )

    with open(CONFIG_FILE, "rb") as f:
        data = tomllib.load(f)

    profiles = {}
    for name, profile_data in data.get("profiles", {}).items():
        profiles[name] = Profile(
            name=name,
            api_key=profile_data["api_key"],
            label=profile_data.get("label", ""),
        )

    if not profiles:
        raise ValueError("No profiles found in config file.")

    default = data.get("default_profile", next(iter(profiles)))
    return Config(profiles=profiles, default_profile=default)


def save_config(config: Config) -> None:
    """Save configuration to TOML file."""
    _ensure_config_dir()

    lines = []
    # Write top-level keys first (before any table sections)
    lines.append(f'default_profile = "{config.default_profile}"')
    lines.append("")

    for name, profile in config.profiles.items():
        lines.append(f"[profiles.{name}]")
        lines.append(f'api_key = "{profile.api_key}"')
        if profile.label:
            lines.append(f'label = "{profile.label}"')
        lines.append("")

    CONFIG_FILE.write_text("\n".join(lines))


def add_profile(name: str, api_key: str, label: str = "", set_default: bool = False) -> Config:
    """Add a new profile to the config."""
    try:
        config = load_config()
    except FileNotFoundError:
        config = Config(profiles={}, default_profile=name)

    config.profiles[name] = Profile(name=name, api_key=api_key, label=label)

    if set_default or len(config.profiles) == 1:
        config.default_profile = name

    save_config(config)
    return config


def remove_profile(name: str) -> Config:
    """Remove a profile from the config."""
    config = load_config()

    if name not in config.profiles:
        raise ValueError(f"Profile '{name}' not found.")

    del config.profiles[name]

    if config.default_profile == name:
        config.default_profile = next(iter(config.profiles), "")

    save_config(config)
    return config


def set_default_profile(name: str) -> Config:
    """Set the default profile."""
    config = load_config()

    if name not in config.profiles:
        available = ", ".join(config.profiles.keys())
        raise ValueError(f"Profile '{name}' not found. Available: {available}")

    config.default_profile = name
    save_config(config)
    return config
