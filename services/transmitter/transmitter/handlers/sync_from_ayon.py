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
        self.table_name = kwargs.get("table_name", "Shots")
        self.topic = kwargs.get("topic")
        self.user = kwargs.get("user")
        self.api_key = kwargs.get("api_key")
        self.base = kwargs.get("base")
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
        # data_to_be_synced["assignee"] = self.user
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
        airtable_version = f"{version_entity.get_version():03}"
        data_to_be_synced["version"] = airtable_version
        if version_entity.task_id:
            task = ayon_api.get_task_by_id(
                self.project_name,
                version_entity.task_id,
                fields=["type"]
            )
            task_name = [task["type"]] if task else []
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
        table = self.get_or_create_table()
        self.create_or_update_airtable_record(table, data, self.topic)
        self.log.info("Sync from AYON to Airtable completed.")

    def create_or_update_airtable_record(
            self, table: pyairtable.Table,
            data: Dict, topic: str) -> None:
        """Update a record in Airtable.

        Args:
            table (pyairtable.Table): The Airtable table to update
            the record in.
            data (Dict): The data to update the record with.
            topic (str): The topic of the event, used to determine how to
            update the record.
        """
        if table is None:
            self.log.error("No table found in Airtable base.")
            return
        record_id = self.get_record_id(table, data, topic)
        # data = self.convert_assignee_data(data)
        if record_id is None:
            self.log.info("No existing record found, creating a new one.")
            table.create(data)
        else:
            self.log.info("Updating record %s in table %s.",
                          record_id, table.name)
            # Assuming data contains the fields to update
            table.update(record_id, data, replace=True)

    def get_record_id(
            self, table: pyairtable.Table, data: Dict, topic: str) -> str:
        """Get the Airtable record ID for the given data.

        Args:
            table (pyairtable.Table): The Airtable table to search in.
            data (Dict): The data to match against existing records.
            topic (str): The topic of the event, used to determine how to

        Returns:
            record_id: str
        """
        for record in table.all():
            if not record.get("fields", {}):
                continue
            fields = record.get("fields", {})
            project = self.attrib_map.get("project")
            product_name = self.attrib_map.get("product_name")
            if topic == "entity.version.created" and (
                data.get(project) in fields.get(project) and
                data.get(product_name) in fields.get(product_name)
            ):
                return record["id"]

            version_id = self.attrib_map.get("version_id")
            if topic == "entity.version.status_changed" and (
                data.get(project) in fields.get(project) and
                data.get(product_name) in fields.get(product_name) and
                data.get(version_id) in fields.get(version_id)
            ):

                return record["id"]
        return None

    def get_or_create_table(self) -> pyairtable.Table:
        """Get the Airtable table for the current base.

        If it does not exist, create it with the schema based on the data.

        Args:
            data (Dict): The data to be synced, used to determine the table.

        Returns:
            pyairtable.Table: The Airtable table object for the current base,
            or None if not found.
        """
        try:
            table = self.base.table(self.table_name)
            table.all()

        except Exception:
            self.log.exception(
                "Error retrieving table %s", self.table_name
            )
            raise

        return table

    # def convert_assignee_data(self, data: Dict) -> Dict:
    #     """Convert assignee data to a format suitable for Airtable.

    #     Args:
    #         data (Dict): The data to convert.

    #     Returns:
    #         Dict: The converted data with the assignee field formatted.
    #     """
    #     api = pyairtable.Api(self.api_key)
    #     base = api.base(self.base_id)
    #     assignee = data.get("Assignee")
    #     if assignee:
    #         collaborators = base.collaborators()
    #         for collaborator in collaborators:
    #             if collaborator.name == assignee:
    #                 target_collaborator = collaborator
    #                 break
    #         data["Assignee"] = {
    #             "id": target_collaborator.id,
    #             "email": target_collaborator.email,
    #             "name": target_collaborator.name,
    #         }
    #     return data
