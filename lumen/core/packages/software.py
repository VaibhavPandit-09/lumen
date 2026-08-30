from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class SoftwareKind(str, Enum):
    APPLICATION = "APPLICATION"
    PACKAGE = "PACKAGE"
    RUNTIME = "RUNTIME"
    LIBRARY = "LIBRARY"
    CLI = "CLI"


@dataclass
class SoftwareCapabilities:
    can_install: bool = True
    can_remove: bool = True  
    can_update: bool = True
    can_launch: bool = False
    can_purge: bool = False
    can_show_details: bool = False


@dataclass
class SoftwareItem:
    id: str
    name: str
    display_name: str = ""
    description: str = ""
    icon: str = "package-x-generic"
    kind: SoftwareKind = SoftwareKind.PACKAGE
    source: str = ""
    installed: bool = False
    version: str = ""
    available_version: str = ""
    update_available: bool = False
    launchable: bool = False
    desktop_entry: Optional[str] = None
    capabilities: SoftwareCapabilities = field(default_factory=SoftwareCapabilities)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "kind": self.kind.value,
            "source": self.source,
            "installed": self.installed,
            "version": self.version,
            "available_version": self.available_version,
            "update_available": self.update_available,
            "launchable": self.launchable,
            "desktop_entry": self.desktop_entry,
            "capabilities": {
                "can_install": self.capabilities.can_install,
                "can_remove": self.capabilities.can_remove,
                "can_update": self.capabilities.can_update,
                "can_launch": self.capabilities.can_launch,
                "can_purge": self.capabilities.can_purge,
                "can_show_details": self.capabilities.can_show_details,
            }
        }

    @classmethod
    def from_package_info(cls, pkg: 'PackageInfo') -> SoftwareItem:
        from lumen.core.packages.base import PackageInfo
        
        return cls(
            id=getattr(pkg, 'id', getattr(pkg, 'name', '')),
            name=getattr(pkg, 'name', ''),
            display_name=getattr(pkg, 'display_name', getattr(pkg, 'name', '')),
            description=getattr(pkg, 'description', ""),
            icon=getattr(pkg, 'icon', "package-x-generic"),
            source=getattr(pkg, 'source', ""),
            installed=getattr(pkg, 'installed', False),
            version=getattr(pkg, 'version', ""),
            available_version=getattr(pkg, 'available_version', ""),
            update_available=getattr(pkg, 'update_available', False)
        )
