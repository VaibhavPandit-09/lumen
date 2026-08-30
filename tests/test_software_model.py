from __future__ import annotations

import unittest

from lumen.core.packages.base import PackageInfo
from lumen.core.packages.software import (
    SoftwareCapabilities,
    SoftwareItem,
    SoftwareKind,
)


class TestSoftwareModel(unittest.TestCase):
    """Tests for lumen.core.packages.software data models."""

    def test_software_kind_enum(self) -> None:
        expected_kinds = {
            "APPLICATION": "APPLICATION",
            "PACKAGE": "PACKAGE",
            "RUNTIME": "RUNTIME",
            "LIBRARY": "LIBRARY",
            "CLI": "CLI",
        }
        for name, value in expected_kinds.items():
            kind = getattr(SoftwareKind, name)
            self.assertEqual(kind.value, value)

        all_values = {k.value for k in SoftwareKind}
        self.assertEqual(all_values, set(expected_kinds.values()))

    def test_software_capabilities_defaults(self) -> None:
        caps = SoftwareCapabilities()
        self.assertTrue(caps.can_install)
        self.assertTrue(caps.can_remove)
        self.assertTrue(caps.can_update)
        self.assertFalse(caps.can_launch)
        self.assertFalse(caps.can_purge)
        self.assertFalse(caps.can_show_details)

        # Custom capabilities
        custom_caps = SoftwareCapabilities(
            can_install=False,
            can_remove=False,
            can_update=False,
            can_launch=True,
            can_purge=True,
            can_show_details=True,
        )
        self.assertFalse(custom_caps.can_install)
        self.assertFalse(custom_caps.can_remove)
        self.assertFalse(custom_caps.can_update)
        self.assertTrue(custom_caps.can_launch)
        self.assertTrue(custom_caps.can_purge)
        self.assertTrue(custom_caps.can_show_details)

    def test_software_item_creation_and_dict(self) -> None:
        caps = SoftwareCapabilities(can_launch=True, can_show_details=True)
        item = SoftwareItem(
            id="pkg:vlc",
            name="vlc",
            display_name="VLC Media Player",
            description="Multimedia player and framework",
            icon="vlc",
            kind=SoftwareKind.APPLICATION,
            source="flatpak",
            installed=True,
            version="3.0.18",
            available_version="3.0.19",
            update_available=True,
            launchable=True,
            desktop_entry="/usr/share/applications/vlc.desktop",
            capabilities=caps,
        )

        self.assertEqual(item.id, "pkg:vlc")
        self.assertEqual(item.name, "vlc")
        self.assertEqual(item.display_name, "VLC Media Player")
        self.assertEqual(item.kind, SoftwareKind.APPLICATION)
        self.assertTrue(item.installed)
        self.assertTrue(item.update_available)

        expected_dict = {
            "id": "pkg:vlc",
            "name": "vlc",
            "display_name": "VLC Media Player",
            "description": "Multimedia player and framework",
            "icon": "vlc",
            "kind": "APPLICATION",
            "source": "flatpak",
            "installed": True,
            "version": "3.0.18",
            "available_version": "3.0.19",
            "update_available": True,
            "launchable": True,
            "desktop_entry": "/usr/share/applications/vlc.desktop",
            "capabilities": {
                "can_install": True,
                "can_remove": True,
                "can_update": True,
                "can_launch": True,
                "can_purge": False,
                "can_show_details": True,
            },
        }
        self.assertEqual(item.to_dict(), expected_dict)

    def test_from_package_info(self) -> None:
        pkg = PackageInfo(
            name="htop",
            version="3.2.2",
            summary="Interactive process viewer",
            description="htop is an interactive text-mode process viewer",
            source_backend="apt",
            installed=True,
            update_available=True,
            new_version="3.3.0",
        )
        # SoftwareItem.from_package_info looks for source, available_version, etc.
        # Let's set attributes if available
        setattr(pkg, "source", "apt")
        setattr(pkg, "available_version", "3.3.0")

        item = SoftwareItem.from_package_info(pkg)
        self.assertEqual(item.id, "htop")
        self.assertEqual(item.name, "htop")
        self.assertEqual(item.version, "3.2.2")
        self.assertEqual(item.source, "apt")
        self.assertTrue(item.installed)
        self.assertTrue(item.update_available)
        self.assertEqual(item.available_version, "3.3.0")
        self.assertEqual(item.description, "htop is an interactive text-mode process viewer")


if __name__ == "__main__":
    unittest.main()
