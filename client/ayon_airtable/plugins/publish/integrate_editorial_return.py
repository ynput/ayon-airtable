"""Plugin for collecting editorial return information from Airtable records.

This module defines a Pyblish plugin that updates Airtable records
with editorial return data.
"""
from typing import ClassVar

import pyblish.api
from ayon_airtable.backend.rest_stub import AirtableRestStub


class CollectEditorialReturn(pyblish.api.InstancePlugin):
    """Publish editorial return information from the context."""
    order = pyblish.api.IntegratorOrder + 0.499
    label = "Collect Editorial Return"
    families: ClassVar[list[str]] = ["editorial", "editorial_pkg"]

    def process(self, instance: pyblish.api.Instance) -> None:
        """Collect editorial return information from the instance."""
        useful_data = self.get_data(instance)
        for product_name in instance.data.get("productNames", []):
            record_id = AirtableRestStub.get_record_id(
                api_key=useful_data["api_key"],
                base_name=useful_data["base_name"],
                table_name=useful_data["table_name"],
                project_name=useful_data["project_name"],
                product_name=product_name,
                project_name_field=useful_data["project_name_field"],
                product_name_field=useful_data["product_name_field"]
            )

            AirtableRestStub.update_record(
                api_key=useful_data["api_key"],
                base_name=useful_data["base_name"],
                table_name=useful_data["table_name"],
                record_id=record_id,
                fields={"Editorial_Return": instance.name},
                replace=True
            )

    @staticmethod
    def get_data(instance: pyblish.api.Instance) -> dict:
        """Get useful data from the instance.

        Args:
            instance: The Pyblish instance to extract data from.

        Returns:
            dict: A dictionary containing Airtable and project information.
        """
        return {
            "api_key": instance.context.data.get("airtableApi"),
            "base_name": instance.context.data.get("airtableBase"),
            "table_name": instance.context.data.get("airtableTable"),
            "project_name": instance.context.data.get("projectName"),
            "project_name_field": instance.context.data.get(
                "airtableProjectNameField"
            ),
            "product_name_field": instance.context.data.get(
                "airtableProductNameField"
            ),
        }
