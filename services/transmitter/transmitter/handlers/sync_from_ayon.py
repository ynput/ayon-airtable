from typing import Dict, Union
import logging
from ayon_api.entity_hub import EntityHub
import ayon_api
import pyairtable


class AyonAirtableHub:
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

    def get_entity_hub(self, project_name: str) -> EntityHub:
        """Get the EntityHub for the given project.

        Args:
            project_name (str): Name of the project.

        Returns:
            EntityHub: The EntityHub instance for the given project name.
        """
        return EntityHub(project_name)

    def parse_data_to_be_synced(self):
        """Sync changes from AYON to Airtable."""
        self.log.info("Starting sync from AYON to Airtable.")
        data_to_be_synced = {}
        entity_hub = self._cached_hub
        if entity_hub is None:
            entity_hub = self.get_entity_hub(self.project_name)

        data_to_be_synced["project"] = self.project_name
        data_to_be_synced["assignne"] = self.user
        data_to_be_synced["version_id"] = self.summary["entityId"]
        version_entity = entity_hub.get_version_by_id(self.summary["entityId"])
        if version_entity is None:
            raise ValueError("Unable to update a non existing entity.")

        # make sure the entity is not immutable
        if version_entity.immutable_for_hierarchy:
            raise ValueError("Entity is immutable, aborting...")
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
            raise ValueError("Unable to update a non existing entity.")

        data_to_be_synced["product_name"] = product_entity.name

        return {
            self.attrib_map[airtable_key]: value
            for ayon_key, value in data_to_be_synced.items()
            if (airtable_key := self.attrib_map.get(ayon_key))
        }

    def sync_from_ayon_to_airtable(self):
        self.log.info("Starting sync from AYON to Airtable.")
        data_to_be_synced = self.parse_data_to_be_synced()
        for data in data_to_be_synced:
            self.log.info(f"Syncing data: {data}")
            if self.topic == "entity.version.created":
                self.log.info("Creating new version in Airtable.")
                # Here you would implement the logic to create a new version in Airtable
                self.create_airtable_record(data)
            elif self.topic == "entity.version.status_changed":
                self.log.info("Updating version status in Airtable.")
                # Here you would implement the logic to update the version status in Airtable
                self.update_airtable_record(data)
            else:
                self.log.warning(f"Unknown action: {data['action']}. Skipping.")
                continue

        self.log.info("Sync from AYON to Airtable completed.")

    def create_airtable_record(self, data: Dict):
        """Create a record in Airtable.

        Args:
            data (Dict): The data to create the record with.
        """
        api = pyairtable.Api(self.api_key)
        base = api.base(self.base_name)
        table = next((table for table in base.tables()), None)
        if table is None:
            self.log.error("No table found in Airtable base.")
            return

        self.log.info(f"Creating record in table {table.name}.")
        table.create(data)

    def update_airtable_record(self, data: Dict):
        """Update a record in Airtable.

        Args:
            data (Dict): The data to update the record with.
        """
        table, record_id = self.get_table_and_record_id(data)
        if record_id is None:
            self.log.info("No existing record found, creating a new one.")
            table.create(data)

        self.log.info(f"Updating record {record_id} in table {table.name}.")
        # Assuming data contains the fields to update
        table.update(record_id, data, replace=True)

    def get_table_and_record_id(self, data: Dict) -> Union[pyairtable.Table, str]:
        """Get Airtable table and record ID based on data.

        Returns:
            pyairtable.Table, record_id: Table, str
        """
        api = pyairtable.Api(self.api_key)
        base = api.base(self.base_name)
        for table in base.tables():
            for record in table.all():
                if record.get("fields", {}):
                    return table, None
                if (
                   record["fields"].get("Project") == data["Project"]
                   and record["fields"].get("V#") == data["V#"]
                   and record["fields"].get("VersionId") == data["VersionId"]
                ):
                    return table, record["id"]

        return None, None
