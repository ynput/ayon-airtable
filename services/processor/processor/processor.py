
"""Airtable Processor Service for AYON.

This module provides the AirtableProcessor class, which handles AYON events
related to Airtable integration, including event enrollment, synchronization
of projects from Airtable, API authentication, and polling intervals.
"""

import logging
import sys
import time
import traceback
from pprint import pformat
from typing import Dict, Optional

import ayon_api
import pyairtable

from .handlers.sync_from_airtable_handlers import sync_projects_from_airtable


class AirtableProcessor:
    """Processes AYON events related to Airtable integration.

    Handles event enrollment, synchronization of projects from Airtable,
    and manages API authentication and polling intervals.
    """
    log = logging.getLogger(__name__)

    def __init__(self):
        """A class to process AYON events of `airtable.event` topic.

        Raises:
            ValueError: If the Airtable API Key is not found in the Addon
                System settings.
            TypeError: If the Airtable API Key is not found or is not a dict.
        """
        self.log.info("Initializing the Airtable Processor.")

        try:
            self.settings = ayon_api.get_service_addon_settings()
            service_settings = self.settings["service_settings"]
            self.attribs_map = self.settings["attribute_maps"]
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

        except Exception:
            self.log.exception("Unable to get Addon settings from the server.")
            self.log.exception(traceback.format_exc())
            raise

    def handle_airtable_event(self, payload: Dict) -> None:
        """Handle the `airtable.event` event type."""
        self.log.info("Handling Airtable event.")
        if not payload:
            self.log.warning("No payload found in the event.")
            return
        required_fields = [
            self.attribs_map.get("project"),
            self.attribs_map.get("status"),
            self.attribs_map.get("version_id"),
        ]
        required_fields = [field for field in required_fields if field]
        if not required_fields:
            self.log.warning("No required fields found in the settings.")
            return
        api = self._get_api_token()
        sync_projects_from_airtable(
            api,
            payload,
            required_fields,
            self.attribs_map
        )

    def _get_api_token(
            self, airtable_api_key: Optional[str] = None) -> pyairtable.Api:
        """Get the Airtable API token.

        Args:
            airtable_api_key (Optional[str]): The Airtable API key to use.
            If None, uses the instance's API key.

        Returns:
            pyairtable.Api: An instance of the Airtable API client.
        """
        if airtable_api_key is None:
            airtable_api_key = self.airtable_api_key
        return pyairtable.Api(airtable_api_key)

    def start_processing(self) -> None:
        """Enroll AYON events of topic `airtable.leech` and.

        process them using handle_airtable_event.
        """
        while True:
            try:

                event = ayon_api.enroll_event_job(
                    "airtable.leech",
                    "airtable.proc",
                    sender=ayon_api.get_service_name(),
                    description="Event processing",
                    max_retries=2,
                    sequential=False,
                )
                if not event:
                    self.log.debug(
                        "No event found, sleeping for poll interval."
                    )
                    time.sleep(self.poll_interval)
                    continue

                source_event = ayon_api.get_event(event["dependsOn"])
                payload = source_event["payload"]
                table_event_id = payload["id"]
                failed = False

                if payload.get("action") == "airtable-leech":
                    try:
                        self.log.info(
                            "Running the Handler handle_airtable_event"
                        )
                        ayon_api.update_event(
                            event["id"],
                            description=(
                                "Processing event with Handler "
                                f"{payload['action']}..."
                            ),
                            status="in_progress",
                        )
                        self.log.debug(f"processing event {pformat(payload)}")  # noqa: G004
                        self.handle_airtable_event(payload)

                    except Exception:
                        failed = True
                        self.log.exception(
                            "Unable to process handler handle_airtable_event"
                        )
                        ayon_api.update_event(
                            event["id"],
                            status="failed",
                            description=(
                                "An error occurred while processing "
                                f"{table_event_id}"
                            ),
                            payload={
                                "message": traceback.format_exc(),
                            },
                        )

                if not failed:
                    self.log.info(
                        "Event has been processed... setting to finished!")
                    ayon_api.update_event(
                        event["id"],
                        description=(
                            f"Event processed successfully {table_event_id}"
                        ),
                        status="finished",
                    )

            except Exception:
                self.log.exception(traceback.format_exc())


def service_main() -> None:
    """Main entry point for the Airtable processor service.

    Initializes the AYON service, sets the sender type, and starts
    processing events.
    """
    ayon_api.init_service()
    ayon_api.set_sender_type("airtable")
    airtable_processor = AirtableProcessor()
    sys.exit(airtable_processor.start_processing())
