"""REST API routes."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ayon_core.lib import Logger

from ayon_airtable.backend import rest_routes

if TYPE_CHECKING:
    from aiohttp.web import UrlDispatcher


class AirtableModuleRestAPI:
    """REST API endpoint used for Airtable operations."""

    def __init__(self, server_manager: UrlDispatcher):
        """Initialize AirtableModuleRestAPI."""
        self._log = None
        self.server_manager = server_manager
        self.prefix = "/airtable"

    @property
    def log(self) -> Logger:
        """Get logger instance."""
        if self._log is None:
            self._log = Logger.get_logger(self.__class__.__name__)
        return self._log

    def register(self) -> None:
        """Register all REST API routes."""
        get_api = rest_routes.AirtableApiEndpoint()
        self.server_manager.add_route(
            "POST", f"{self.prefix}/api", get_api.dispatch
        )
        get_table = rest_routes.GetTableEndpoint()
        self.server_manager.add_route(
            "POST", f"{self.prefix}/get_table", get_table.dispatch
        )
        get_record_id = rest_routes.GetRecordIdEndpoint()
        self.server_manager.add_route(
            "POST", f"{self.prefix}/get_record_id", get_record_id.dispatch
        )
        update_record = rest_routes.UpdateRecordEndpoint()
        self.server_manager.add_route(
            "POST", f"{self.prefix}/update_record", update_record.dispatch
        )
        get_product_name_field = rest_routes.GetProductNameFieldEndpoint()
        self.server_manager.add_route(
            "POST", f"{self.prefix}/get_product_name_field",
            get_product_name_field.dispatch
        )
