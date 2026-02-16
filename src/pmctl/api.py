"""Postman API client."""

from __future__ import annotations

from typing import Any, Optional

import httpx

BASE_URL = "https://api.getpostman.com"


class PostmanClient:
    """HTTP client for the Postman API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={"X-Api-Key": api_key},
            timeout=30.0,
        )

    def _get(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Make a GET request to the Postman API."""
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PostmanClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # --- User ---

    def get_me(self) -> dict[str, Any]:
        """Get current user info."""
        return self._get("/me")

    # --- Workspaces ---

    def list_workspaces(self) -> list[dict[str, Any]]:
        """List all accessible workspaces."""
        return self._get("/workspaces").get("workspaces", [])

    def get_workspace(self, workspace_id: str) -> dict[str, Any]:
        """Get workspace details."""
        return self._get(f"/workspaces/{workspace_id}").get("workspace", {})

    # --- Collections ---

    def list_collections(self, workspace_id: Optional[str] = None) -> list[dict[str, Any]]:
        """List collections, optionally filtered by workspace."""
        params = {"workspace": workspace_id} if workspace_id else None
        return self._get("/collections", params=params).get("collections", [])

    def get_collection(self, collection_uid: str) -> dict[str, Any]:
        """Get full collection details including all requests."""
        return self._get(f"/collections/{collection_uid}").get("collection", {})

    # --- Environments ---

    def list_environments(self, workspace_id: Optional[str] = None) -> list[dict[str, Any]]:
        """List environments, optionally filtered by workspace."""
        params = {"workspace": workspace_id} if workspace_id else None
        return self._get("/environments", params=params).get("environments", [])

    def get_environment(self, environment_id: str) -> dict[str, Any]:
        """Get environment details including variables."""
        return self._get(f"/environments/{environment_id}").get("environment", {})
