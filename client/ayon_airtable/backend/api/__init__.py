"""Wrapper for PyAirtable.

An easier, more pythonic interface for working with Airtable,
built on PyAirtable.
Objects, methods and functions in this module handle connection
and errors automatically, managing the verbose approach required
in PyAirtable.
"""
import socket
from typing import Dict, Optional

import pyairtable


class AirtablePythonWrapper:
    """Airtable Python Wrapper.

    This class provides a simplified interface for interacting with Airtable
    using PyAirtable.
    """

    def __init__(
        self
    ) -> None:
        """Initialize the Airtable Python Wrapper."""
        self._host_name = None
        self._api = None
        self._table = None

    @property
    def host_name(self) -> str:
        """Get the host name of the current machine.

        Returns:
            str: The host name of the current machine.
        """
        if not self._host_name:
            self._host_name = socket.gethostname()
        return self._host_name

    def api(self, api_key: str) -> pyairtable.Api:
        """Get the PyAirtable API instance, initializing it if necessary.

        Args:
            api_key (str): The Airtable API key to use.

        Returns:
            pyairtable.Api: The initialized PyAirtable API instance.
        """
        if self._api is None:
            self._api = pyairtable.Api(api_key)
        return self._api

    def _get_bases_data_by_api_key(
            self, api_key: Optional[str] = None) -> Dict:
        """Get Airtable bases data by API key.

        Args:
            api_key (Optional[str]): The Airtable API key to use.
                If None, uses the instance's API key.

        Returns:
            Dict: The data of Airtable bases retrieved using the API key.
        """
        if self._api is None:
            self._api = self.api(api_key)
        base_urls = self._api.urls.bases
        return self._api.get(base_urls)

    def _get_base_id_by_name(
            self, api_key: str, base_name: str) -> str:
        """Get Airtable base ID by base name.

        Args:
            api_key (str): The Airtable API key to use.
            base_name (str): The name of the Airtable base.

        Returns:
            str: The ID of the Airtable base.
        """
        bases = self._get_bases_data_by_api_key(api_key)
        for base_set in bases.values():
            for base in base_set:
                if base_name in base["name"]:
                    return base["id"]
        return ""

    def get_base(
            self, api_key: str, base_name: str) -> pyairtable.Base:
        """Get the Airtable base by name.

        Args:
            api_key (str): The Airtable API key to use.
            base_name (str): The name of the Airtable base.

        Returns:
            pyairtable.Base: The Airtable base instance.

        Raises:
            RuntimeError: If the specified base name is not found.
        """
        base_id = self._get_base_id_by_name(api_key, base_name)
        if not base_id:
            msg = f"Base '{base_name}' not found."
            raise RuntimeError(msg)

        return self._api.base(base_id)

    def get_table(
            self, api_key: str,
            base_name: str, table_name: str) -> pyairtable.Table:
        """Get the Airtable table by name.

        Returns:
            pyairtable.Table: The Airtable table instance.

        Raises:
            RuntimeError: If the specified table name is not found.
        """
        base = self.get_base(api_key, base_name)
        try:
            self._table = base.table(table_name)

        except Exception as e:
            msg = (
                f"Table '{table_name}' not found in base "
                f"'{base_name}'."
            )
            raise RuntimeError(msg) from e
        return self._table

    def update_record(
        self,
        api_key: str,
        base_name: str,
        table_name: str,
        record_id: str,
        fields: Dict
    ) -> Dict:
        """Update a record in the Airtable table.

        Args:
            api_key (str): The Airtable API key to use.
            base_name (str): The name of the Airtable base.
            table_name (str): The name of the Airtable table.
            record_id (str): The ID of the record to update.
            fields (Dict): The fields to update in the record.

        Returns:
            Dict: The updated record data.
        """
        if self._table is None:
            self._table = self.get_table(api_key, base_name, table_name)
        return self._table.update(record_id, fields)

    def get_record_id(
        self,
        **kwargs: Dict[str, str],
    ) -> Optional[str]:
        """Get the record ID for the given data.

        Args:
            kwargs (Dict[str, str]): A dictionary containing the
            following keys:
                - api_key: The Airtable API key to use.
                - base_name: The name of the Airtable base.
                - table_name: The name of the Airtable table.
                - project_name: The name of the project to match.
                - product_name: The name of the product to match.
                - project_name_field: The field name for the project
                in the table.
                - product_name_field: The field name for the product
                in the table.

        Returns:
            Optional[str]: The record ID if found, otherwise None.
        """
        if self._table is None:
            self._table = self.get_table(
                kwargs["api_key"], kwargs["base_name"], kwargs["table_name"]
            )
        for record in self._table.all():
            field = record.get("fields", {})
            if not field:
                continue

            if (
                field.get(kwargs["product_name_field"]) == kwargs["product_name"]  # noqa: E501
                and
                field.get(kwargs["project_name_field"]) == kwargs["project_name"]  # noqa: E501
            ):
                return record["id"]
        return None

    def get_product_name_field(
        self,
        **kwargs: Dict[str, str],
    ) -> Optional[list]:
        """Get the product name field from the Airtable table.

        Args:
            kwargs (Dict[str, str]): A dictionary containing the
            following keys:
                - api_key: The Airtable API key to use.
                - base_name: The name of the Airtable base.
                - table_name: The name of the Airtable table.
                - project_name: The name of the project to match.
                - project_name_field: The field name for the project
                in the table.
                - product_name_field: The field name for the product
                in the table.

        Returns:
            Optional[list]: The list of product name field if found,
                otherwise None.
        """
        product_names = []
        if self._table is None:
            self._table = self.get_table(
                kwargs["api_key"], kwargs["base_name"], kwargs["table_name"]
            )
        for record in self._table.all():
            fields = record.get("fields", {})
            product_name_field = kwargs["product_name_field"]
            project_name_field = kwargs["project_name_field"]
            if (
                fields.get(product_name_field)
                and fields.get(project_name_field) == kwargs["project_name"]
            ):
                product_names.append(fields[product_name_field])

        return product_names
