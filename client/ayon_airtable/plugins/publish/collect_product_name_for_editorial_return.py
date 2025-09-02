

"""Plugin to collect product names for editorial return from Airtable.

This module defines a Pyblish context plugin that retrieves product names
from Airtable records based on the current project and exposes them for
user selection during the publishing process.
"""

import os
from typing import ClassVar

import pyblish.api
from ayon_airtable.backend.rest_stub import AirtableRestStub
from ayon_core.lib import EnumDef
from ayon_core.pipeline import get_current_project_name
from ayon_core.pipeline.publish import PublishError


class CollectProductNameForEditorialReturn(pyblish.api.ContextPlugin):
    """Collects product name from users for editorial return."""
    order = pyblish.api.CollectorOrder
    label = "Collect Product Name For Editorial Return (Airtable)"
    families: ClassVar[list[str]] = ["editorial", "editorial_pkg"]

    def process(self, context: pyblish.api.Context) -> None:
        """Collect product names from the user's preference.

        Args:
            context (pyblish.api.Context): The context of the plugin.

        Raises:
            PublishError: If the Airtable table is not set in the context data.
        """
        airtable_table = AirtableRestStub.get_table(
            context.data.get("airtableApi"),
            context.data.get("airtableBase"),
            context.data.get("airtableTable")
        )
        if not airtable_table:
            msg = "Airtable table is not set in the context data."
            raise PublishError(msg)
        attr_values = self.get_attr_values_from_data(context.data)
        context.data["productNames"] = attr_values.get("productNames", [])

    @classmethod
    def get_attribute_defs(cls) -> list:
        """Return attribute definitions for product names selection.

        Returns:
        list: List of EnumDef objects for product name selection.
        """
        airtable_data = {
            "api_key": os.getenv("AIRTABLE_API_KEY"),
            "base_name": os.getenv("AIRTABLE_BASE_NAME"),
            "table_name": os.getenv("AIRTABLE_TABLE_NAME"),
            "project_name": get_current_project_name(),
            "product_name_field": os.getenv("AIRTABLE_PRODUCT_NAME_FIELD"),
            "project_name_field": os.getenv("AIRTABLE_PROJECT_NAME_FIELD"),
        }

        export_texture_set_enum = (
            AirtableRestStub.get_product_name_field(**airtable_data)
        ) or []

        return [
                EnumDef(
                    "productNames",
                    items=export_texture_set_enum,
                    multiselection=True,
                    default=None,
                    label="Product Name for Editorial Return",
                    tooltip="Choose the texture set(s) which "
                            "you want to export."
                ),
        ]
