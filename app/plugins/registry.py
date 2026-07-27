from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Plugin(Protocol):
    key: str
    name: str

    def is_available(self) -> bool: ...


@dataclass(slots=True)
class PluginStatus:
    key: str
    name: str
    available: bool


class PluginRegistry:
    """Registre minimal pour les futurs connecteurs Plex, Radarr, Jellyfin et Trakt."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        self._plugins[plugin.key] = plugin

    def statuses(self) -> list[PluginStatus]:
        return [
            PluginStatus(p.key, p.name, bool(p.is_available()))
            for p in self._plugins.values()
        ]
