"""Processor package for Airtable integration.

This package provides the AirtableProcessor class and service_main entry point.
"""

from .processor import (
    AirtableProcessor,
    service_main,
)

__all__ = (
    "AirtableProcessor",
    "service_main",
)
