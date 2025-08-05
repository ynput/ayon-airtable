"""Handlers for interacting with the Airtable API.

including authentication and table access.
"""

import logging
import os
from typing import Optional

import pyairtable

log = logging.getLogger(__name__)


def get_api(api_key: Optional[str] = None) -> str:
    """Retrieve the Airtable API token from environment variables.

    Returns:
        str: The Airtable API token.

    Raises:
        RuntimeError: The Airtable API key is not set in
        Ayon settings
    """
    if not api_key:
        msg = "The Airtable API key is not set in Ayon settings."
        raise RuntimeError(msg)

    return pyairtable.Api(api_key)


def get_airtable_base(base_name: Optional[str] = None) -> pyairtable.Base:
    """Retrieve the Airtable base instance.

    Returns:
        pyairtable.Base: The Airtable base instance.

    Raises:
        RuntimeError: The Airtable API key is not set in
        Ayon settings
    """
    api = get_api()
    if not base_name:
        msg = "Airtable base ID is not set in Ayon settings."
        raise RuntimeError(msg)

    return api.base(base_name)


def get_airtable_table(table_name: Optional[str] = None) -> pyairtable.Table:
    """Retrieve the Airtable table instance.

    Returns:
        pyairtable.Table: The Airtable table instance.

    Raises:
        RuntimeError: If the Airtable table name is not set in
        Ayon settings.
    """
    base = get_airtable_base()
    if not table_name:
        msg = "Airtable table name is not set in Ayon settings."
        raise RuntimeError(msg)
    return base.table(table_name)
