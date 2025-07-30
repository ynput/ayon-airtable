"""Plugin for collecting editorial return information from Airtable records.

This module defines a Pyblish plugin that updates Airtable records
with editorial return data.
"""

import operator

import pyairtable
import pyblish.api


class CollectEditorialReturn(pyblish.api.InstancePlugin):
    """Publish editorial return information from the context."""
    order = pyblish.api.IntegratorOrder + 0.499
    label = "Collect Editorial Return"
    families = ["editorial", "editorial_pkg"]  # noqa: RUF012

    def process(self, instance: pyblish.api.Instance) -> None:  # noqa: PLR6301
        """Collect editorial return information from the instance."""
        airtable_table = instance.context.data.get("airtableTable")
        if not airtable_table:
            self.log.debug(
                "Airtable table is not set in the context data."
            )
            return
        if not instance.data.get("productNames"):
            self.log.debug(
                "No product names found in the instance data."
            )
            return

        for product_name in instance.data.get("productNames", []):
            record_id = self.get_record_id(
                airtable_table, product_name,
                instance.context.data.get("airtableVersionField"),
                instance.context.data.get("airtableProductNameField"),
            )

            airtable_table.update(
                record_id, {"Editorial_Return": instance.name}, replace=True
            )

    @staticmethod
    def get_record_id(table: pyairtable.Table, product_name: str,
                      version_map: str, product_name_map: str) -> str:
        """Retrieve the record ID from the Airtable table.

        Args:
            table: The Airtable table to search.
            product_name: The product name to match.
            version_map: The field name for the version.
            product_name_map: The field name for the product name.

        Returns:
            The record ID as a string if found, otherwise an empty string.
        """
        records = []
        for record in table.all():
            fields = record.get("fields", {})
            if not fields:
                continue
            if fields.get(product_name_map) == product_name and \
                fields.get(version_map):
                records.append({
                    "id": record["id"],
                    "version": fields[version_map]
            })
        if records:
            latest = max(records, key=operator.itemgetter("version"))
            return latest["id"]
        return ""
