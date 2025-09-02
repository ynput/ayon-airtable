"""Transmitter service package.

This package provides the AirtableTransmitter class and service_main function
for transmitting data.
"""

from .transmitter import (
    AirtableTransmitter,
    service_main,
)

__all__ = (
    "AirtableTransmitter",
    "service_main",
)
