"""Handlers for interacting with the Airtable API.

including authentication and table access.
"""

import logging
import os
from typing import Optional

import pyairtable

log = logging.getLogger(__name__)


def get_api_token(api_key: Optional[str] = None) -> str:
    """Retrieve the Airtable API token from environment variables.

    Returns:
        str: The Airtable API token.
    """
    if not api_key:
        api_key = os.getenv("AIRTABLE_API_KEY")
        if not api_key:
            log.debug(
                "Airtable API key is not set in the environment variables."
            )

    return pyairtable.Api(api_key or os.getenv("AIRTABLE_API_KEY"))


def get_airtable_base(base_name: Optional[str] = None) -> pyairtable.Base:
    """Retrieve the Airtable base instance.

    Returns:
        pyairtable.Base: The Airtable base instance.
    """
    api = get_api_token()
    if base_name:
        base_name = os.getenv("AIRTABLE_BASE_ID", "")
        if not base_name:
            log.debug(
                "Airtable base ID is not set in the environment variables."
            )

    return api.base(base_name)


def get_airtable_table(table_name: Optional[str] = None) -> pyairtable.Table:
    """Retrieve the Airtable table instance.

    Returns:
        pyairtable.Table: The Airtable table instance.
    """
    base = get_airtable_base()
    if table_name:
        table_name = os.getenv("AIRTABLE_TABLE_NAME", "")
        if not table_name:
            log.debug(
                "Airtable table name is not set in the environment variables."
            )
    return base.table(table_name)
