
import sys
import time
import logging
import traceback

import ayon_api
from .handlers.sync_from_ayon import AyonAirtableHub


class AirtableTransmitter:
    log = logging.getLogger(__name__)

    def __init__(self):
        """ Ensure both AYON and Airtable connections are available.

        Set up common needed attributes and handle airtable connection
        closure via signal handlers.

        Args:
            func (Callable, None): In case we want to override the default
                function we cast to the processed events.
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

            if isinstance(airtable_secret, list):
                raise ValueError(
                    "Airtable API Key not found. Make sure to set it in the "
                    "Addon System settings. "
                    "`ayon+settings://airtable/service_settings/script_key`"
                )

            self.airtable_api_key = airtable_secret.get("value")
            if not self.airtable_api_key:
                raise ValueError(
                    "Airtable API Key not found. Make sure to set it in the "
                    "Addon System settings."
                )

        except Exception as e:
            self.log.error("Unable to get Addon settings from the server.")
            self.log.error(traceback.format_exc())
            raise e

    def start_processing(self):
        """ Main loop querying AYON for `entity.*` events.

        We enroll to events that `created`, `deleted` and `renamed`
        on AYON `entity` to replicate the event in Shotgrid.
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
                    # This should never happen since we only fetch events of
                    # projects we have shotgridPush enabled; but just in case
                    # The event happens when after we deleted a project in
                    # AYON.
                    self.log.info(
                        f"Project {project_name} does not exist in AYON "
                        "or does not have the `shotgridPush` attribute set, "
                        f"ignoring event {event}."
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

                self.log.info("Event has been processed... setting to finished!")
                ayon_api.update_event(
                    event["id"],
                    project_name=project_name,
                    status="finished"
                )
            except Exception:
                self.log.error(
                    "Error processing event", exc_info=True)

                ayon_api.update_event(
                    event["id"],
                    project_name=project_name,
                    status="failed",
                    payload={
                        "message": traceback.format_exc(),
                    },
                )

    def _get_sync_project_names(self):
        """Get project names that are enabled for Airtable sync."""
        ayon_projects = ayon_api.get_projects(fields=["name", "attrib"])

        project_names = [
            project["name"]
            for project in ayon_projects
            if project["attrib"].get("airtablePush")
        ]

        return project_names

def service_main():
    ayon_api.init_service()
    airtable_transmitter = AirtableTransmitter()
    sys.exit(airtable_transmitter.start_processing())
