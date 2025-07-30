

"""Plugin to collect product names for editorial return from Airtable.

This module defines a Pyblish context plugin that retrieves product names
from Airtable records based on the current project and exposes them for
user selection during the publishing process.
"""

import os

import pyblish.api
from ayon_airtable.common.airtable_api_handlers import get_airtable_table
from ayon_core.lib import EnumDef
from ayon_core.pipeline import get_current_project_name


class CollectProductNameForEditorialReturn(pyblish.api.ContextPlugin):
    """Collects product name from users for editorial return."""
    order = pyblish.api.CollectorOrder
    label = "Collect Product Name For Editorial Return (Airtable)"
    families = ["editorial", "editorial_pkg"]  # noqa: RUF012

    def process(self, context: pyblish.api.Context) -> None:
        """Collect product names from the user's preference.

        Args:
            context (pyblish.api.Context): The context of the plugin.
        """
        airtable_table = get_airtable_table()
        if not airtable_table:
            self.log.debug("Airtable table is not set in the context data.")
            return
        attr_values = self.get_attr_values_from_data(context.data)
        context.data["productNames"] = attr_values.get("productNames", [])


    @classmethod
    def get_attribute_defs(cls) -> list:
        """Return attribute definitions for product names selection.

        Returns:
        -------
        list
            List of EnumDef objects for product name selection.
        """
        export_texture_set_enum = []
        project_field = os.getenv("AIRTABLE_PROJECT_FIELD", "")
        product_name_field = os.getenv("AIRTABLE_PRODUCT_NAME_FIELD", "")

        airtable_table = get_airtable_table()
        if airtable_table:
            for record in airtable_table.all():
                fields = record.get("fields", {})
                if not fields:
                    continue
                if fields.get(project_field) == get_current_project_name():
                    product_name = fields.get(product_name_field, "")
                    if product_name:
                        export_texture_set_enum.append(product_name)

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
