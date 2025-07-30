
import os

import pyblish.api

from ayon_airtable.common.BaseHandler import (
    get_airtable_base,
    get_airtable_table,
    get_api_token,
)


class CollectAirtableAPI(pyblish.api.ContextPlugin):
    """Collects Airtable API key and base name from the addon settings."""
    order = pyblish.api.CollectorOrder + 0.1
    label = "Collect Airtable API"
    families = ["editorial", "editorial_pkg"]  # noqa: RUF012

    def process(self, context: pyblish.api.Context) -> None:
        """Collect Airtable API related info from environment variables.

        Parameters
        ----------
        context : pyblish.api.Context
            The Pyblish context to store Airtable API, base,
            and table information.

        Raises:
        ------
        RuntimeError
            If collecting Airtable API information fails.
        """  # noqa: DOC501
        if not os.getenv("AIRTABLE_API_KEY"):
            self.log.debug(
                "Airtable API key is not set in the environment variables."
            )
            return

        if not os.getenv("AIRTABLE_BASE_NAME"):
            self.log.debug(
                "Airtable base name is not set in the environment variables."
            )
            return

        if not os.getenv("AIRTABLE_TABLE_NAME"):
            self.log.debug(
                "Airtable table name is not set in the environment variables."
            )
            return
        try:
            context.data["airtableApi"] = get_api_token()
            context.data["airtableBase"] = get_airtable_base()
            context.data["airtableTable"] = get_airtable_table()
            context.data["airtableProductNameField"] = (
                os.getenv("AIRTABLE_PRODUCT_NAME_FIELD")
            )
            context.data["airtableVersionField"] = (
                os.getenv("AIRTABLE_VERSION_FIELD")
            )

        except Exception as e:
            msg = f"Failed to collect Airtable API information: {e}"
            raise RuntimeError(msg) from e
