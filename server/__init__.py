"""Server package."""
from typing import Type, Dict
import requests
from ayon_server.addons import BaseServerAddon
from ayon_server.exceptions import InvalidSettingsException
from ayon_server.secrets import Secrets
from ayon_server.lib.postgres import Postgres

from .settings import (
    AirtableSettings,
    AIRTABLE_DEFAULT_VALUES
)


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

    async def setup(self):
        need_restart = await self.create_airtable_attributes()
        if need_restart:
            self.request_server_restart()

    def initialize(self) -> None:
        self.add_endpoint(
            "/AirtableBase",
            self.get_airtable_base,
            method="GET",
        )

    async def get_airtable_base(
        self, variant: str, settings_model: AirtableSettings
    ) -> Dict:
        # TODO validate user permissions
        # - What permissions user must have to allow this endpoint?
        if settings_model is None:
            settings_model = await self.get_studio_settings(variant)
        service_settings = settings_model.service_settings
        api_key_secret = service_settings.script_key
        airtable_base_name = service_settings.base_name

        if not api_key_secret or not airtable_base_name:
            raise InvalidSettingsException("Required settings are not set.")

        airtable_api_key = await Secrets.get(api_key_secret)

        if not airtable_api_key:
            raise InvalidSettingsException(
                "Invalid service settings, secrets are not set."
            )
        airtable_token = self.check_airtable_token(airtable_api_key)

        return airtable_token

    async def create_airtable_attributes(self) -> bool:
        """Make sure there are required attributes which airtable addon needs.

        Returns:
            bool: 'True' if an attribute was created or updated.
        """

        query = "SELECT name, position, scope, data from public.attributes"
        artable_id_attribute_data = {
            "type": "string",
            "title": "airtable id",
            "inherit": False,
        }
        artable_path_attribute_data = {
            "type": "string",
            "title": "airtable path",
            "inherit": False,
        }
        airtable_push_attribute_data = {
            "type": "boolean",
            "title": "airtable push",
            "inherit": False,
            "default": True,
        }
        # Only sync the version-related entity to/from airtable
        artable_id_expected_scope = ["project", "folder", "task", "version"]
        artable_path_expected_scope = ["project", "folder", "task", "version"]
        artable_push_expected_scope = ["project"]

        artable_id_match_position = None
        artable_id_matches = False
        artable_path_match_position = None
        artable_path_matches = False
        airtable_push_match_position = None
        airtable_push_matches = False
        position = 1
        if Postgres.pool is None:
            await Postgres.connect()
        async for row in Postgres.iterate(query):
            position += 1
            if row["name"] == AIRTABLE_ID_ATTRIB:
                # Check if scope is matching airtable addon requirements
                if not set(artable_id_expected_scope) - set(row["scope"]):
                    artable_id_matches = True
                artable_id_match_position = row["position"]

            elif row["name"] == AIRTABLE_PATH_ATTRIB:
                if not set(artable_path_expected_scope) - set(row["scope"]):
                    artable_path_matches = True
                artable_path_match_position = row["position"]
            elif row["name"] == AIRTABLE_PUSH_ATTRIB:
                if not set(artable_push_expected_scope) - set(row["scope"]):
                    airtable_push_matches = True
                airtable_push_match_position = row["position"]

        if artable_id_matches and artable_path_matches and airtable_push_matches:
            return False

        postgre_query = "\n".join((
            "INSERT INTO public.attributes",
            "    (name, position, scope, data)",
            "VALUES",
            "    ($1, $2, $3, $4)",
            "ON CONFLICT (name)",
            "DO UPDATE SET",
            "    scope = $3,",
            "    data = $4",
        ))
        if not artable_id_matches:
            # Reuse position from found attribute
            if artable_id_match_position is None:
                artable_id_match_position = position
                position += 1

            await Postgres.execute(
                postgre_query,
                AIRTABLE_ID_ATTRIB,
                artable_id_match_position,
                artable_id_expected_scope,
                artable_id_attribute_data,
            )

        if not artable_path_matches:
            if artable_path_match_position is None:
                artable_path_match_position = position
                position += 1

            await Postgres.execute(
                postgre_query,
                AIRTABLE_PATH_ATTRIB,
                artable_path_match_position,
                artable_path_expected_scope,
                artable_path_attribute_data,
            )
        if not airtable_push_matches:
            if airtable_push_match_position is None:
                airtable_push_match_position = position
                position += 1

            await Postgres.execute(
                postgre_query,
                AIRTABLE_PUSH_ATTRIB,
                airtable_push_match_position,
                artable_push_expected_scope,
                airtable_push_attribute_data,
            )
        return True

    async def check_airtable_token(self, api_key: str) -> Dict:
        """
        Verify if an Airtable API key is valid by listing bases.

        Args:
            api_key: Your Airtable API key

        Returns:
            Dict: A dictionary with the validity of the API key and scopes.
        """
        url = "https://api.airtable.com/v0/meta/bases"
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.ok:
                return {
                    "valid": True,
                    "scopes": response.json().get("scopes", []),
                    "error": None
                }
            else:
                return {
                    "valid": False,
                    "scopes": [],
                    "error": f"HTTPS {response.status_code}: {response.text}"
                }
        except requests.exceptions.RequestException as e:
            return {
                "valid": False,
                "scopes": [],
                "error": f"Connection error: {e}"
            }
