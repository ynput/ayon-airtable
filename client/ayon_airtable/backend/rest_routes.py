"""Rest routes for Airtable backend."""
from __future__ import annotations

import datetime
import json
from typing import Any, Union

from aiohttp.web import Request, Response
from ayon_core.lib import Logger
from ayon_core.tools.tray.webserver.base_routes import RestApiEndpoint

from ayon_airtable.backend import api

log = Logger.get_logger("P4routes")


class AirtableRestApiEndpoint(RestApiEndpoint):
    """Base class for Airtable Rest API endpoints."""
    def __init__(self):
        """Init."""
        super().__init__()
        self._wrapper = api.AirtablePythonWrapper()

    @staticmethod
    def json_dump_handler(value: Any) -> Union[list, str]:  # noqa: ANN401
        """Custom JSON dump handler.

        Returns:
            str: JSON dump of the value.

        Raises:
            TypeError: If value is not supported.

        """
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        if isinstance(value, set):
            return list(value)
        raise TypeError(value)

    @classmethod
    def encode(cls, data: Any) -> bytes:  # noqa: ANN401
        """Encode data to JSON.

        Returns:
            bytes: Encoded JSON data.

        """
        return json.dumps(
            data,
            indent=4,
            default=cls.json_dump_handler
        ).encode("utf-8")


class AirtableApiEndpoint(AirtableRestApiEndpoint):
    """Return API for Airtable."""

    async def post(self, request: Request) -> Response:
        """Get API from Airtable Endpoint.

        Returns:
            Response: Response object.

        """
        content = await request.json()
        api_key = content.get("api_key", "")
        if not api_key:
            return Response(
                status=400,
                body=b"API key is required.",
                content_type="text/plain"
            )

        result = self._wrapper.api(api_key)
        return Response(
            status=200,
            body=self.encode(result),
            content_type="application/json"
        )


class GetTableEndpoint(AirtableRestApiEndpoint):
    """Return specific table from Airtable."""

    async def post(self, request: Request) -> Response:
        """Get Table from Airtable Endpoint.

        Returns:
            Response: Response object.

        """
        content = await request.json()

        result = self._wrapper.get_table(
            content["api_key"],
            content["base_name"],
            content["table_name"]
        )
        return Response(
            status=200,
            body=self.encode(result),
            content_type="application/json"
        )


class GetRecordIdEndpoint(AirtableRestApiEndpoint):
    """Return specific record ID from Airtable."""

    async def post(self, request: Request) -> Response:
        """Get Record ID from Airtable Endpoint.

        Returns:
            Response: Response object.

        """
        content = await request.json()
        kwargs = {
            "api_key": content["api_key"],
            "base_name": content["base_name"],
            "table_name": content["table_name"],
            "project_name": content["project_name"],
            "product_name": content["product_name"],
            "project_name_field": content["project_name_field"],
            "product_name_field": content["product_name_field"]
        }
        result = self._wrapper.get_record_id(**kwargs)

        return Response(
            status=200,
            body=self.encode(result),
            content_type="application/json"
        )


class UpdateRecordEndpoint(AirtableRestApiEndpoint):
    """Return update record from Airtable."""

    async def post(self, request: Request) -> Response:
        """Update Record from Airtable Endpoint.

        Returns:
            Response: Response object.

        """
        content = await request.json()

        result = self._wrapper.update_record(
            api_key=content["api_key"],
            base_name=content["base_name"],
            table_name=content["table_name"],
            record_id=content["record_id"],
            fields=content["fields"]
        )
        return Response(
            status=200,
            body=self.encode(result),
            content_type="application/json"
        )


class GetProductNameFieldEndpoint(AirtableRestApiEndpoint):
    """Return product name field from Airtable."""

    async def post(self, request: Request) -> Response:
        """Get Product Name Field from Airtable Endpoint.

        Returns:
            Response: Response object.

        """
        content = await request.json()
        result = self._wrapper.get_product_name_field(
            api_key=content["api_key"],
            base_name=content["base_name"],
            table_name=content["table_name"],
            project_name=content["project_name"],
            product_name_field=content["product_name_field"],
            project_name_field=content["project_name_field"]
        )
        return Response(
            status=200,
            body=self.encode(result),
            content_type="application/json"
        )
