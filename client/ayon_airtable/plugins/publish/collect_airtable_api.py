
"""Collects Airtable API and stores them in the context data."""

import os
from typing import ClassVar

import pyblish.api


class CollectAirtableAPI(pyblish.api.ContextPlugin):
    """Collects Airtable API key and base name from the addon settings."""
    order = pyblish.api.CollectorOrder + 0.1
    label = "Collect Airtable API"
    families: ClassVar[list[str]] = ["editorial", "editorial_pkg"]

    def process(self, context: pyblish.api.Context) -> None:
        """Collect Airtable API related info from environment variables.

        Args:
            context (pyblish.api.Context): The Pyblish context to
            store Airtable API, base, and table information.
        """
        self.log.info("Collecting Airtable API and base information.")
        context.data["airtableApi"] = os.getenv("AIRTABLE_API_KEY")
        context.data["airtableBase"] = os.getenv("AIRTABLE_BASE_NAME")
        context.data["airtableTable"] = os.getenv("AIRTABLE_TABLE_NAME")
        context.data["airtableProductNameField"] = (
            os.getenv("AIRTABLE_PRODUCT_NAME_FIELD")
        )
        context.data["airtableVersionField"] = (
            os.getenv("AIRTABLE_VERSION_FIELD")
        )
