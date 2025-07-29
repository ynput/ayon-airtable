"""AYON Airtable Addon module.

This module provides the AirtableAddon class for integrating Airtable
functionality with AYON, including initialization and plugin path
management.
"""

import os
from typing import Any, Dict

from ayon_core.addon import (
    AYONAddon,
    IPluginPaths,
)
from ayon_core.lib import Logger

from .version import __version__

log = Logger.get_logger(__name__)

AIRTABLE_ADDON_DIR = os.path.dirname(os.path.abspath(__file__))


class AirtableAddon(AYONAddon, IPluginPaths):
    """AYON Airtable Addon class.

    Integrates Airtable functionality with AYON, handles initialization,
    environment variable setup, and plugin path management.
    """

    name = "airtable"
    version = __version__

    def initialize(self, studio_settings: Dict) -> None:
        """Initialize the Airtable addon.

        Args:
            studio_settings (Dict): AYON studio settings.
        """
        addon_settings = studio_settings[self.name]
        log.debug(
            "Initializing %s addon with settings: %s",
            self.name,
            addon_settings
        )
        server_settings = addon_settings["service_settings"]
        os.environ["AIRTABLE_API_KEY"] = server_settings["script_key"]
        os.environ["AIRTABLE_BASE_NAME"] = server_settings["base_name"]
        os.environ["AIRTABLE_TABLE_NAME"] = server_settings["table_name"]

    def get_plugin_paths(self) -> Dict[str, Any]:  # noqa: PLR6301
        """Get the plugin paths for the Airtable addon.

        Returns:
            dict: A dictionary containing the plugin paths.
        """
        return {
            "publish": [
                os.path.join(AIRTABLE_ADDON_DIR, "plugins", "publish")
            ]
        }
