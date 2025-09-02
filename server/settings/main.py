"""Settings for the addon."""

from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
)
from ayon_server.settings.enum import secrets_enum


class AirtableAttributeSettings(BaseSettingsModel):
    """Settings for Airtable attributes mapping."""
    project: str = SettingsField(
        default="Project", title="Project Name",
        description="Name of the project to sync with Airtable."
    )
    assignee: str = SettingsField(
        default="Assignee", title="Assignee",
        description="Name of the assignee in Airtable."
    )
    version: str = SettingsField(
        default="V", title="Version",
        description="Version number in Airtable."
    )
    status: str = SettingsField(
        default="Status", title="Status",
        description="Status of the project in Airtable."
    )
    tags: str = SettingsField(
        default="Types", title="Tags",
        description="Comma-separated list of tags in Airtable."
    )
    product_name: str = SettingsField(
        default="VFX_ID", title="Product Name",
        description="Name of the product in Airtable."
    )
    version_id: str = SettingsField(
        default="VersionId", title="Version ID",
        description="ID of the version in Airtable."
    )


class AirtableServiceSettings(BaseSettingsModel):
    """Settings for the addon."""
    base_name: str = SettingsField(
        "", title="Base Name",
        description="Name of the Airtable Base to sync with AYON.")
    table_name: str = SettingsField(
        "Shots", title="Table Name",
        description="Name of the Airtable Table to sync with AYON.")
    script_key: str = SettingsField(
    default="",
    enum_resolver=secrets_enum,
    title="Airtable's Script api key",
    description=(
        "AYON Secret used for Service related server operations "
        "Secret should lead to Airtable's Script api key. "
        "See more at:https://support.airtable.com/docs/"
        "creating-personal-access-tokens"
    ))
    poll_interval: int = SettingsField(title="Poll Interval")


class AirtableSettings(BaseSettingsModel):
    """Settings for the Airtable integration."""
    attribute_maps: AirtableAttributeSettings = SettingsField(
        default_factory=AirtableAttributeSettings,
        title="Airtable <-> AYON Attributes Mapping",
        description=(
            "Mapping of AYON attributes to Airtable fields. "
            "This is used to sync data between AYON and Airtable."
        )
    )
    service_settings: AirtableServiceSettings = SettingsField(
        default_factory=AirtableServiceSettings,
        title="Service settings"
    )


AIRTABLE_DEFAULT_VALUES = {
    "attribute_maps": {
        "project": "Project",
        "assignee": "Assignee",
        "version": "V",
        "status": "Status",
        "tags": "Types",
        "product_name": "VFX_ID",
        "version_id": "VersionId",
    },
    "service_settings": {
        "base_name": "",
        "table_name": "Shots",
        "script_key": "",
        "poll_interval": 10
    }
}
