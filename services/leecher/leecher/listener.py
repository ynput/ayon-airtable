
"""Listener module for Airtable webhooks and AYON integration.

This module provides the AirtableListener class to handle webhook
management,payload retrieval, and event dispatching between
Airtable and AYON.
"""

import json
import logging
import os
import signal
import sys
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union

import ayon_api
import pyairtable
from pyairtable.models.webhook import CreateWebhookResponse


def to_dict(obj: object) -> Union[Dict[str, object], List[object], object]:
    """Recursively convert an object to a dictionary or list.

    Args:
        obj (object): The object to convert.

    Returns:
        Union[Dict[str, object], List[object], object]: The converted
        dictionary, list, or original object.
    """
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if hasattr(obj, "__dict__"):
        return {k: to_dict(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [to_dict(item) for item in obj]
    return obj


def serialize_datetime(obj: object) -> Optional[str]:
    """Serialize a datetime object to ISO format string.

    Parameters
    ----------
    obj : object
        The object to check and serialize if it is a datetime.

    Returns:
    -------
    Optional[str]
        ISO format string if obj is a datetime, otherwise None.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    return None


class AirtableListener:
    """Listener class for Airtable webhooks and events.

    Handles initialization, connection to Airtable and AYON,
    webhook management, payload retrieval, and event dispatching.

    """

    log = logging.getLogger(__name__)

    def __init__(self):
        """Ensure both AYON and Airtable connections are available.

        Set up common needed attributes and handle airtable connection
        closure via signal handlers.

        Raises:
            ValueError: If the Airtable API key or base name is not set.
        """  # noqa: DOC501
        self.log.info("Initializing the Airtable Listener.")
        self.stop_event = threading.Event()
        try:
            self.settings = ayon_api.get_service_addon_settings()
            service_settings = self.settings["service_settings"]
            self.airtable_base_name = service_settings["base_name"]
            self.poll_interval = service_settings["poll_interval"]
            airtable_secret = ayon_api.get_secret(
                service_settings["script_key"])
            if not isinstance(airtable_secret, dict):
                msg = (
                    "Airtable API Key not found. Make sure to set it in the "
                    "Addon System settings. "
                    "`ayon+settings://airtable/service_settings/script_key`"
                )
                raise TypeError(msg)  # noqa: TRY301

            self.airtable_api_key = airtable_secret.get("value")
            if not self.airtable_api_key:
                msg = (
                    "Airtable API Key not found. Make sure to set it in the "
                    "Addon System settings."
                )
                raise ValueError(msg)  # noqa: TRY301
            if not self.airtable_base_name:
                msg = (
                    "Invalid input for Airtable Base Name. "
                    "Please insert the correct one"
                )
                raise ValueError(msg)  # noqa: TRY301

        except Exception:
            self.log.exception(
                "Unable to get Addon settings from the server.")
            raise

        try:
            bases = self.get_bases_data_by_api_key()
            self.base_id, self.base = self.get_base_by_name(bases)
            self.webhook_handler = self.create_webhook()
        except Exception:
            self.log.exception(
                "Fails to connect Airtable Base Instance. "
                "Make sure set the correct API key"
                " in https://airtable.com/create/tokens/. "
                "Make sure the scope added "
                "with data.records.read and data.records.write"
            )
            raise

        signal.signal(signal.SIGINT, self._signal_teardown_handler)
        signal.signal(signal.SIGTERM, self._signal_teardown_handler)

    def _signal_teardown_handler(self, signalnum, frame) -> None:  # noqa: ANN001
        """Callback to terminating process.

        The webhook would be removed
        after the leecher has been stopped.

        """
        self.log.warning("Process stop requested. Terminating process.")
        self.stop_event.set()
        # Clean up Airtable connection
        if self.webhook_handler is not None:
            self.webhook_handler.delete()

        self.log.warning("Termination finished.")
        sys.exit(0)

    def _get_api_token(
            self, airtable_api_key: Optional[str] = None) -> pyairtable.Api:
        """Get Api access token to access Airtable.

        Returns:
            pyairtable.Api: Api access
        """
        if airtable_api_key is None:
            airtable_api_key = self.airtable_api_key
        return pyairtable.Api(self.airtable_api_key)

    def get_bases_data_by_api_key(self) -> Dict:
        """Get Airtable bases data by API key.

        Returns:
            Dict: The data of Airtable bases retrieved using the API key.
        """
        api = self._get_api_token()
        base_urls = api.urls.bases
        return api.get(base_urls)

    def get_base_by_name(
            self,
            bases: pyairtable.Api.bases,
            base_name: Optional[str] = None
        ) -> pyairtable.Base:
        """Get Airtable base by base name.

        Returns:
            pyairtable.Base: Base
        """
        api = self._get_api_token()
        if base_name is None:
            base_name = self.airtable_base_name
        for base_set in bases.values():
            for base in base_set:
                if base_name in base["name"]:
                    return base["id"], api.base(base["id"])
        return None, None

    def add_webhook(
            self, webserver_url: Optional[str] = None
            ) -> CreateWebhookResponse:
        """Adding Airtable webbook.

        Args:
            webserver_url (str, optional): Ayon Server URL. Defaults to None.

        Returns:
            CreateWebhookResponse: CreateWebhookResponse
        """
        if webserver_url is None:
            webserver_url = os.environ["AYON_SERVER_URL"]
        webhook_url = f"{webserver_url}/airtable/webhook"
        spec_data = {
            "options": {
                "filters": {
                    "dataTypes": ["tableData"],
                    "changeTypes": ["update"]
                }
            }
        }
        return self.base.add_webhook(webhook_url, spec_data)

    def create_webhook(self) -> pyairtable.models.Webhook:
        """Create Webhook for Aritable.

        Returns:
            pyairtable.models.Webhook: Webhook
        """
        if self.base.webhooks():
            for webhook in self.base.webhooks():
                return webhook
        webhook = self.add_webhook()
        webhook_id = webhook.id
        return self.base.webhook(webhook_id)

    def get_payloads(self) -> Dict:
        """Get all webhook payloads data from Airtable.

        Returns:
            Dict: payloads data
        """
        try:
            airtable_webhook_payloads = self.webhook_handler.payloads()
            airtable_payloads = {
                i: to_dict(payload) for i, payload in
                enumerate(airtable_webhook_payloads)
            }
        except Exception:  # noqa: BLE001
            airtable_payloads = {}
            self.log.info("No payload data found from Airtable's webhook.")

        seralize_payloads = json.dumps(
                airtable_payloads, default=serialize_datetime
            )
        seen = set()
        unique_payloads = {}

        for payload in json.loads(seralize_payloads).values():
            signature = json.dumps(payload, sort_keys=True)
            if signature not in seen:
                seen.add(signature)
                unique_payloads[str(len(seralize_payloads))] = payload
        return {
            "action": "airtable-leech",
            "webhook_id": self.webhook_handler.id,
            "base_id": self.base_id,
            "airtable_payloads": unique_payloads
        }

    def start_listening(self) -> None:
        """Main loop querying the Airtable database for new events."""
        self.log.info("Start listening for Airtable Events...")
        while not self.stop_event.is_set():
            try:
                payload_id = str(uuid.uuid4())
                # Get the payload and inject identifiers
                payload = self.get_payloads()
                payload["payload_id"] = payload_id
                description = f"Leeched {payload['action']}"
                ayon_api.dispatch_event(
                    "airtable.leech",
                    sender=ayon_api.ServiceContext.service_name,
                    event_hash=payload_id,
                    description=description,
                    payload=payload
                )

            except Exception as e:
                self.log.exception(f"Error in leecher: {e}")  # noqa: G004, TRY401

            time.sleep(self.poll_interval)


def service_main() -> None:
    """Initialize the AYON service and start the Airtable listener.

    This function sets up the AYON service, creates an AirtableListener
    instance, and starts listening for Airtable events until termination.

    """
    ayon_api.init_service()
    airtable_listener = AirtableListener()
    sys.exit(airtable_listener.start_listening())
