"""Handlers for syncing data from AYON to Airtable.

This module provides the AyonAirtableHub class for synchronizing
AYON entities with Airtable records.
"""

import logging
from typing import Dict

import ayon_api
import pyairtable
from ayon_api.entity_hub import EntityHub


class AyonAirtableHub:
    """A hub for synchronizing AYON entities with Airtable records.

    This class provides methods to parse AYON data, and create or update
    corresponding records in Airtable.
    """

    def __init__(self, **kwargs: object):
        """Initialize the Ayon Airtable Hub."""
        self.log = logging.getLogger(__name__)
        self.log.info("Initializing Ayon Airtable Hub.")
        self.topic = kwargs.get("topic")
        self.user = kwargs.get("user")
        self.api_key = kwargs.get("api_key")
        self.base_name = kwargs.get("base_name")
        self.project_name = kwargs.get("project_name")
        self.summary = kwargs.get("summary")
        self.payload = kwargs.get("payload")
        self.attrib_map = kwargs.get("attribs_map")
        self._cached_hub = self.get_entity_hub(self.project_name)

    @staticmethod
    def get_entity_hub(project_name: str) -> EntityHub:
        """Get the EntityHub for the given project.

        Args:
            project_name (str): Name of the project.

        Returns:
            EntityHub: The EntityHub instance for the given project name.
        """
        return EntityHub(project_name)

    def parse_data_to_be_synced(self) -> Dict:
        """Sync changes from AYON to Airtable.

        Returns:
            Dict: A dictionary mapping Airtable keys to their corresponding
            values from AYON.

        Raises:
            ValueError: If the version or product entity does not exist, or if
            the entity is immutable.
        """
        self.log.info("Starting sync from AYON to Airtable.")
        data_to_be_synced = {}
        entity_hub = self._cached_hub
        if entity_hub is None:
            entity_hub = self.get_entity_hub(self.project_name)

        data_to_be_synced["project"] = self.project_name
        data_to_be_synced["assignee"] = self.user
        data_to_be_synced["version_id"] = self.summary["entityId"]
        version_entity = entity_hub.get_version_by_id(self.summary["entityId"])
        if version_entity is None:
            msg = "Unable to update a non existing entity."
            raise ValueError(msg)

        # make sure the entity is not immutable
        if version_entity.immutable_for_hierarchy:
            msg = "Entity is immutable, aborting..."
            raise ValueError(msg)
        data_to_be_synced["status"] = version_entity.status
        data_to_be_synced["version"] = version_entity.name
        if version_entity.task_id:
            task = ayon_api.get_task_by_id(
                self.project_name,
                version_entity.task_id,
                fields=["name"]
            )
            task_name = [task["name"]] if task else []
        else:
            task_name = []

        data_to_be_synced["tags"] = task_name

        product_entity = entity_hub.get_product_by_id(self.summary["parentId"])
        if product_entity is None:
            msg = "Unable to update a non existing entity."
            raise ValueError(msg)

        data_to_be_synced["product_name"] = product_entity.name

        return {
            airtable_key: value
            for ayon_key, value in data_to_be_synced.items()
            if (airtable_key := self.attrib_map.get(ayon_key))
        }

    def sync_from_ayon_to_airtable(self) -> None:
        """Sync changes from AYON to Airtable based on the topic.

        This method parses the data to be synced and performs the appropriate
        action in Airtable (create or update) depending on the topic.
        """
        self.log.info("Starting sync from AYON to Airtable.")
        data = self.parse_data_to_be_synced()
        self.log.info("Syncing data: %s", data)
        if self.topic == "entity.version.created":
            self.log.info("Creating new version in Airtable.")
            # Here you would implement the logic to create a new version
            # in Airtable
            self.create_airtable_record(data)
        elif self.topic == "entity.version.status_changed":
            self.log.info("Updating version status in Airtable.")
            # Here you would implement the logic to update the version status
            # in Airtable
            self.update_airtable_record(data)
        else:
            self.log.warning("Unknown action: %s. Skipping.", self.topic)

        self.log.info("Sync from AYON to Airtable completed.")

    def create_airtable_record(self, data: Dict) -> None:
        """Create a record in Airtable.

        Args:
            data (Dict): The data to create the record with.
        """
        table = self.get_table()
        if table is None:
            self.log.error("No table found in Airtable base.")
            return

        self.log.info("Creating record in table %s.", table.name)
        table.create(data)

    def update_airtable_record(self, data: Dict) -> None:
        """Update a record in Airtable.

        Args:
            data (Dict): The data to update the record with.
        """
        table = self.get_table()
        if table is None:
            self.log.error("No table found in Airtable base.")
            return
        record_id = self.get_record_id(table, data)
        if record_id is None:
            self.log.info("No existing record found, creating a new one.")
            table.create(data)

        self.log.info("Updating record %s in table %s.", record_id, table.name)
        # Assuming data contains the fields to update
        table.update(record_id, data, replace=True)

    @staticmethod
    def get_record_id(table: pyairtable.Table, data: Dict) -> str:
        """Get the Airtable record ID for the given data.

        Args:
            table (pyairtable.Table): The Airtable table to search in.
            data (Dict): The data to match against existing records.

        Returns:
            record_id: str
        """
        for record in table.all():
            if not record.get("fields", {}):
                continue
            if (
                record["fields"].get("Project") == data["Project"]
                and record["fields"].get("V#") == data["V#"]
                and record["fields"].get("VersionId") == data["VersionId"]
            ):
                return record["id"]
        return None

    def get_table(self) -> pyairtable.Table:
        """Get the Airtable table for the current base.

        Returns:
            pyairtable.Table: The Airtable table object for the current base,
            or None if not found.
        """
        api = pyairtable.Api(self.api_key)
        base = api.base(self.base_name)
        return next((table for table in base.tables()), None)
