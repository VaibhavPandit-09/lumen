"""
Base contracts and data models for package management backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class PackageInfo:
    """Represents software metadata from a package manager backend."""
    name: str
    version: str = ""
    summary: str = ""
    description: str = ""
    source_backend: str = "system"   # apt, flatpak, snap, pacman
    installed: bool = False
    update_available: bool = False
    new_version: str = ""
    icon_name: str = "package-x-generic"
    is_gui_app: bool = False
    installed_size: str = ""
    homepage: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "summary": self.summary,
            "description": self.description,
            "source_backend": self.source_backend,
            "installed": self.installed,
            "update_available": self.update_available,
            "new_version": self.new_version,
            "icon_name": self.icon_name,
            "is_gui_app": self.is_gui_app,
            "installed_size": self.installed_size,
            "homepage": self.homepage,
        }


@dataclass
class PackageOperationResult:
    """Outcome of a package management transaction (install, remove, update)."""
    success: bool
    message: str
    raw_output: str = ""
    error_details: Optional[str] = None
    affected_packages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "raw_output": self.raw_output,
            "error_details": self.error_details,
            "affected_packages": self.affected_packages,
        }


class BasePackageBackend(ABC):
    """Abstract base class for package manager integration."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the package manager (e.g. 'APT', 'Flatpak', 'Snap', 'Pacman')."""
        pass

    @property
    @abstractmethod
    def backend_id(self) -> str:
        """Short identifier (e.g. 'apt', 'flatpak', 'snap', 'pacman')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Whether this package manager is installed and usable on the current host."""
        pass

    @abstractmethod
    def is_locked(self) -> bool:
        """Whether the package manager is currently busy/locked by another process."""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 15) -> List[PackageInfo]:
        """Searches for packages by name or keyword."""
        pass

    @abstractmethod
    def list_installed(self, query: str = "", limit: int = 30) -> List[PackageInfo]:
        """Lists installed packages matching query."""
        pass

    @abstractmethod
    def check_updates(self) -> List[PackageInfo]:
        """Queries for available software updates."""
        pass

    @abstractmethod
    def install(self, package_name: str, on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        """Installs a package with PolicyKit elevation if required."""
        pass

    @abstractmethod
    def remove(self, package_name: str, purge: bool = False, on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        """Removes a package with PolicyKit elevation if required."""
        pass

    @abstractmethod
    def update(self, package_name: str = "", on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        """Updates a specific package or all packages managed by this backend."""
        pass
