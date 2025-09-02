"""Airtable leecher service package.

Provides AirtableListener and service_main for leecher operations.
"""

from .listener import AirtableListener, service_main

__all__ = (
    "AirtableListener",
    "service_main",
)
