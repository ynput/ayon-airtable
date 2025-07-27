
"""AYON Airtable Transmitter Service.

This module provides the AirtableTransmitter class, which handles
synchronization of AYON entity events to Airtable. It manages connections,
event polling, and transfers relevant data from AYON to Airtable for
enabled projects.
"""

import logging
import sys
import time
import traceback

import ayon_api

from .handlers.sync_from_ayon import AyonAirtableHub


class AirtableTransmitter:
    """Handles synchronization of AYON entity events to Airtable.

    This class manages connections, event polling, and the transfer of relevant
    data from AYON to Airtable, ensuring that only enabled projects are
    processed.
    """

    log = logging.getLogger(__name__)

    def __init__(self):
        """Ensure both AYON and Airtable connections are available.

        Set up common needed attributes and handle airtable connection
        closure via signal handlers.

        Args:
            func (Callable, None): In case we want to override the default
                function we cast to the processed events.

        Raises:
            TypeError: If the Airtable API Key is not found or not a dict.
            ValueError: If the Airtable API Key is not found or invalid.
        """
        self.log.info("Initializing the Airtable Transmitter.")

        self._cached_hubs = {}
        try:
            self.settings = ayon_api.get_service_addon_settings()
            service_settings = self.settings["service_settings"]
            self.airtable_base_name = service_settings["base_name"]
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

    def start_processing(self) -> None:
        """Main loop querying AYON for `entity.*` events.

        We enroll to events that `created` and `status_changed`
        on AYON `entity` to replicate the event in Airtable.
        """
        events_we_care = [
            "entity.version.created",
            "entity.version.status_changed",
        ]

        while True:
            try:
                # enrolling only events which were not created by any
                # of service users so loopback is avoided
                event = ayon_api.enroll_event_job(
                    events_we_care,
                    "airtable.push",
                    ayon_api.get_service_name(),
                    ignore_sender_types=["airtable"],
                    description=(
                        "Handle AYON entity changes and "
                        "sync them to Airtable."
                    ),
                    max_retries=2
                )

                if not event:
                    time.sleep(self.poll_interval)
                    continue

                source_event = ayon_api.get_event(event["dependsOn"])

                project_name = source_event["project"]

                if project_name not in self._get_sync_project_names():
                    self.log.info(
                        "Project %s does not exist in AYON or does not have"
                        "the `airtablePush` attribute set, ignoring event %s.",
                        project_name,
                        event
                    )
                    ayon_api.update_event(
                        event["id"],
                        project_name=project_name,
                        status="finished"
                    )
                    continue

                kwargs = {
                    "topic": source_event["topic"],
                    "user": source_event["user"],
                    "api_key": self.airtable_api_key,
                    "base_name": self.airtable_base_name,
                    "project_name": project_name,
                    "summary": source_event["summary"],
                    "payload": source_event["payload"],
                    "attribs_map": self.attribs_map
                }
                hub = AyonAirtableHub(**kwargs)
                hub.sync_from_ayon_to_airtable()

                self.log.info(
                    "Event has been processed... setting to finished!"
                )
                ayon_api.update_event(
                    event["id"],
                    project_name=project_name,
                    status="finished"
                )
            except Exception:
                self.log.exception("Error processing event")

                ayon_api.update_event(
                    event["id"],
                    project_name=project_name,
                    status="failed",
                    payload={
                        "message": traceback.format_exc(),
                    },
                )

    @staticmethod
    def _get_sync_project_names() -> list:
        """Get project names that are enabled for Airtable sync.

        Returns:
            list: List of project names enabled for Airtable sync.
        """
        ayon_projects = ayon_api.get_projects(fields=["name", "attrib"])
        return [
            project["name"]
            for project in ayon_projects
            if project["attrib"].get("airtablePush")
        ]


def service_main() -> None:
    """Initialize AYON service and start the Airtable transmitter processing loop.

    This function sets up the AYON API service, creates an instance of
    AirtableTransmitter, and starts processing events until the process exits.
    """  # noqa: E501
    ayon_api.init_service()
    airtable_transmitter = AirtableTransmitter()
    sys.exit(airtable_transmitter.start_processing())
