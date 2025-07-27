import os

from ayon_core.addon import (
    AYONAddon,
    IPluginPaths,
)
from ayon_core.lib import Logger

from .version import __version__

log = Logger.get_logger(__name__)

AIRTABLE_ADDON_DIR = os.path.dirname(os.path.abspath(__file__))


class AirtableAddon(AYONAddon, IPluginPaths):
    name = "airtable"
    version = __version__

    def initialize(self, studio_settings):
        addon_settings = studio_settings[self.name]

        log.debug(
            f"Initializing {self.name} addon with "
            "settings: {addon_settings}"
        )
        server_settings = addon_settings["service_settings"]
        os.environ["AIRTABLE_API_KEY"] = server_settings["script_key"]
        os.environ["AIRTABLE_BASE_NAME"] = server_settings["base_name"]

    def get_plugin_paths(self):
        return {
            "publish": [
                os.path.join(AIRTABLE_ADDON_DIR, "plugins", "publish")
            ]
        }
