"""AYON Airtable Addon module.

This module provides the AirtableAddon class for integrating Airtable
functionality with AYON, including initialization and plugin path
management.
"""

from __future__ import annotations

import os
from typing import Any

import ayon_api
from ayon_core.addon import AYONAddon, IPluginPaths, ITrayService
from ayon_core.lib import Logger

from .version import __version__

log = Logger.get_logger(__name__)

AIRTABLE_ADDON_DIR = os.path.dirname(os.path.abspath(__file__))


class AirtableAddon(AYONAddon, ITrayService, IPluginPaths):
    """AYON Airtable Addon class.

    Integrates Airtable functionality with AYON, handles initialization,
    environment variable setup, and plugin path management.
    """

    name = "airtable"
    label = "Airtable"
    version = __version__
    webserver = None

    def initialize(self, settings: dict) -> None:
        """Initialize the Airtable addon.

        Args:
            settings (dict): AYON settings.
        """
        self.settings: dict[str, Any] = settings[self.name]
        log.debug(
            "Initializing %s addon with settings: %s",
            self.name,
            self.settings
        )
        self.webserver = None

    def add_implementation_envs(self, env, app) -> None:
        """Add implementation-specific environment variables.

        Args:
            env (dict): The environment variables to update.
            app: The application instance (unused).
        """
        # Set default environments if are not set via settings
        server_settings = self.get_service_settings()
        attribs_map = self.get_attrib_maps_settings()
        defaults = {
            "AYON_LOG_NO_COLORS": "1",
            "AIRTABLE_API_KEY": self.get_api_secret(),
            "AIRTABLE_BASE_NAME": server_settings.get(
                "base_name", ""),
            "AIRTABLE_TABLE_NAME": server_settings.get(
                "table_name", ""),
            "AIRTABLE_PROJECT_FIELD": attribs_map.get(
                "project", ""),
            "AIRTABLE_PRODUCT_NAME_FIELD": attribs_map.get(
                "product_name", ""),
            "AIRTABLE_VERSION_FIELD": attribs_map.get(
                "version", ""),
        }
        for key, value in defaults.items():
            if not env.get(key):
                env[key] = value

        # Remove auto screen scale factor for Qt
        env.pop("QT_AUTO_SCREEN_SCALE_FACTOR", None)

    def tray_init(self) -> None:
        """Called when the tray is initializing."""
        from ayon_airtable.tray.dialog import AirtableTrayDialog
        self.tray_ui = AirtableTrayDialog(self)

    def tray_exit(self) -> None:
        """Called when the tray is exiting."""
        if self.webserver and self.webserver.server_is_running:
            self.webserver.stop()

    def tray_start(self) -> None:
        """Called when the tray is starting."""
        from ayon_airtable.backend.communication_server import WebServer
        self.webserver = WebServer()
        self.webserver.start()

    def tray_menu(self, tray_menu: dict[str, Any]) -> None:
        """Add Airtable menu to the tray.

        Args:
            tray_menu (dict[str, Any]): Tray menu.

        """
        if self.enabled:
            self.tray_ui.tray_menu(tray_menu)

    def get_plugin_paths(self) -> dict[str, Any]:  # noqa: PLR6301
        """Get the plugin paths for the Airtable addon.

        Returns:
            dict: A dictionary containing the plugin paths.
        """
        return {
            "publish": [
                os.path.join(AIRTABLE_ADDON_DIR, "plugins", "publish")
            ]
        }

    def get_attrib_maps_settings(self) -> dict[str, Any]:
        """Get the attribute maps settings for the Airtable addon.

        Returns:
            dict: A dictionary containing the attribute maps settings.
        """
        return self.settings.get("attribute_maps", {})

    def get_service_settings(self) -> dict[str, Any]:
        """Get the service settings for the Airtable addon.

        Returns:
            dict: A dictionary containing the service settings.
        """
        return self.settings.get("service_settings", {})

    def get_api_secret(self) -> str:
        """Get the Airtable API secret.

        Returns:
            str: The Airtable API secret.
        """
        service_settings = self.get_service_settings()
        return ayon_api.get_secret(
            service_settings["script_key"]).get("value", "")
