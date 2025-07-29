"""Airtable integration addon for AYON.

This package provides the AirtableAddon class and version information for
the AYON Airtable client.
"""

from .addon import (
    AirtableAddon,
)
from .version import __version__

__all__ = (
    "AirtableAddon",
    "__version__",
)
