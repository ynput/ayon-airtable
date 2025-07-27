"""Server package."""
from typing import Dict, Type

import httpx
from ayon_server.addons import BaseServerAddon
from ayon_server.exceptions import InvalidSettingsException
from ayon_server.lib.postgres import Postgres
from ayon_server.secrets import Secrets

from .settings import AIRTABLE_DEFAULT_VALUES, AirtableSettings

AIRTABLE_ID_ATTRIB = "airtableId"
AIRTABLE_PATH_ATTRIB = "airtablePath"
AIRTABLE_PUSH_ATTRIB = "airtablePush"


class AirtableAddon(BaseServerAddon):
    """Add-on class for the server."""
    settings_model: Type[AirtableSettings] = AirtableSettings

    async def get_default_settings(self) -> AirtableSettings:
        """Return default settings."""
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**AIRTABLE_DEFAULT_VALUES)

    async def setup(self) -> None:
        """Set up the Airtable add-on."""
        need_restart = await self.create_airtable_attributes()
        if need_restart:
            self.request_server_restart()

    def initialize(self) -> None:
        """Initialize the Airtable add-on."""
        self.add_endpoint(
            "/AirtableBase",
            self.get_airtable_base,
            method="GET",
        )

    async def get_airtable_base(
        self, variant: str, settings_model: AirtableSettings
    ) -> Dict:
        """Get the Airtable base name from the settings.

        Args:
            variant (str): The variant to use.
            settings_model (AirtableSettings): The settings model instance.

        Returns:
            Dict: The Airtable token information.

        Raises:
            InvalidSettingsException: If required settings or secrets
            are not set.
        """
        if settings_model is None:
            settings_model = await self.get_studio_settings(variant)
        service_settings = settings_model.service_settings
        api_key_secret = service_settings.script_key
        airtable_base_name = service_settings.base_name

        if not api_key_secret or not airtable_base_name:
            msg = "Required settings are not set."
            raise InvalidSettingsException(msg)

        airtable_api_key = await Secrets.get(api_key_secret)

        if not airtable_api_key:
            msg = "Invalid service settings, secrets are not set."
            raise InvalidSettingsException(msg)

        return self.check_airtable_token(airtable_api_key)

    @staticmethod
    async def create_airtable_attributes() -> bool:
        """Ensure required Airtable attributes exist, with reduced complexity.

        Returns:
            bool: True if attributes were created or updated, False otherwise.
        """
        query = "SELECT name, position, scope, data from public.attributes"
        attribute_defs = {
            AIRTABLE_ID_ATTRIB: {
                "data": {"type": "string", "title": "airtable id",
                         "inherit": False},
                "scope": ["project", "folder", "task", "version"],
            },
            AIRTABLE_PATH_ATTRIB: {
                "data": {"type": "string", "title": "airtable path",
                         "inherit": False},
                "scope": ["project", "folder", "task", "version"],
            },
            AIRTABLE_PUSH_ATTRIB: {
                "data": {"type": "boolean", "title": "airtable push",
                         "inherit": False, "default": True},
                "scope": ["project"],
            },
        }

        found = {
            name: {"position": None, "matches": False}
            for name in attribute_defs
        }
        position = 1

        if Postgres.pool is None:
            await Postgres.connect()
        async for row in Postgres.iterate(query):
            position += 1
            if row["name"] in attribute_defs:
                expected_scope = set(attribute_defs[row["name"]]["scope"])
                if not expected_scope - set(row["scope"]):
                    found[row["name"]]["matches"] = True
                found[row["name"]]["position"] = row["position"]

        # If all attributes match, nothing to do
        if all(attr["matches"] for attr in found.values()):
            return False

        postgre_query = "\n".join(  # noqa: FLY002
            [
                "INSERT INTO public.attributes",
                "    (name, position, scope, data)",
                "VALUES",
                "    ($1, $2, $3, $4)",
                "ON CONFLICT (name)",
                "DO UPDATE SET",
                "    scope = $3,",
                "    data = $4",
            ]
        )

        for name, attr_def in attribute_defs.items():
            if not found[name]["matches"]:
                pos = (
                    found[name]["position"]
                    if found[name]["position"] is not None
                    else position
                )
                if found[name]["position"] is None:
                    position += 1
                await Postgres.execute(
                    postgre_query,
                    name,
                    pos,
                    attr_def["scope"],
                    attr_def["data"],
                )
        return True

    @staticmethod
    async def check_airtable_token(api_key: str) -> Dict:
        """Verify if an Airtable API key is valid by listing bases.

        Args:
            api_key: Your Airtable API key

        Returns:
            Dict: A dictionary with the validity of the API key and scopes.
        """
        url = "https://api.airtable.com/v0/meta/bases"
        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient() as client:
            http_response = await client.get(url, headers=headers)
        if http_response.status_code != 200:  # noqa: PLR2004
            return {
                "valid": False,
                "scopes": [],
                "message": "Invalid API key or insufficient permissions."
            }
        data = http_response.json()
        return {
            "valid": True,
            "scopes": data.get("scopes", []),
            "message": None
        }
