"""Controller for the changes viewer."""

from __future__ import annotations

import os
from logging import getLogger
from typing import Union

import requests

log = getLogger(__name__)


class AirtableRestStub:
    """Airtable REST API stub."""

    @staticmethod
    def _wrap_call(command: str, **kwargs: Union[str]) -> dict:
        """Wrap the call to the Airtable REST API.

        Args:
            command (str): Command to call.
            kwargs: Arguments for the command.

        Returns:
            dict: Response from the server.

        Raises:
            RuntimeError: If the server response is not OK.

        """
        webserver_url = os.environ.get("AIRTABLE_WEBSERVER_URL")
        if not webserver_url:
            msg = "Unknown url for Airtable"
            raise RuntimeError(msg)

        action_url = f"{webserver_url}/airtable/{command}"

        response = requests.post(action_url, json=kwargs, timeout=10)
        if not response.ok:
            log.debug(response.content)
            raise RuntimeError(response.text)
        return response.json()

    @staticmethod
    def api(api_key: str) -> dict:
        """Check if the API key is in any workspace.

        Args:
            api_key (str): API key to check.

        Returns:
            dict: Response from the server.

        """
        return AirtableRestStub._wrap_call("api", api_key=api_key)

    @staticmethod
    def get_table(api_key: str, base_name: str) -> dict:
        """Get tables from the Airtable base.

        Args:
            api_key (str): The Airtable API key to use.
            base_name (str): The name of the Airtable base.

        Returns:
            dict: Response from the server.

        """
        return AirtableRestStub._wrap_call(
            "get_table", api_key=api_key, base_name=base_name
        )

    @staticmethod
    def update_record(
        api_key: str, base_name: str, table_name: str,
        record_id: str, fields: dict
    ) -> dict:
        """Update a record in the Airtable table.

        Args:
            api_key (str): The Airtable API key to use.
            base_name (str): The name of the Airtable base.
            table_name (str): The name of the Airtable table.
            record_id (str): The ID of the record to update.
            fields (dict): The fields to update in the record.

        Returns:
            dict: Response from the server.

        """
        return AirtableRestStub._wrap_call(
            "update_record",
            api_key=api_key,
            base_name=base_name,
            table_name=table_name,
            record_id=record_id,
            fields=fields
        )

    @staticmethod
    def get_record_id(**kwargs: str) -> dict:
        """Get the record ID for the given data.

        Args:
            **kwargs: Arbitrary keyword arguments containing:
                api_key (str): The Airtable API key to use.
                base_name (str): The name of the Airtable base.
                table_name (str): The name of the Airtable table.
                project_name (str): The name of the project to match.
                product_name (str): The name of the product to match.
                project_name_field (str): The field name for the project
                    in Airtable.
                product_name_field (str): The field name for the product
                    in Airtable.

        Returns:
            Union[str, None]: The record ID if found, otherwise None.

        """
        return AirtableRestStub._wrap_call("get_record_id", **kwargs)

    @staticmethod
    def get_product_name_field(**kwargs: str) -> dict:
        """Get the product name field from the Airtable table.

        Args:
            **kwargs: Arbitrary keyword arguments containing:
                api_key (str): The Airtable API key to use.
                base_name (str): The name of the Airtable base.
                table_name (str): The name of the Airtable table.
                project_name (str): The name of the project to match.
                project_name_field (str): The field name for the project
                    in Airtable.
                product_name_field (str): The field name for the product
                    in Airtable.

        Returns:
            dict: Response from the server.

        """
        return AirtableRestStub._wrap_call("get_product_name_field", **kwargs)
