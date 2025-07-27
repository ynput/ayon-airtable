from typing import Dict
import logging
import pyairtable
from ayon_api.entity_hub import EntityHub


log = logging.getLogger(__name__)

AIRTABLE_ID_ATTRIB = "airtableId"
AIRTABLE_PATH_ATTRIB = "airtablePath"


def serialize_fields(target_fields: Dict) -> Dict:
    """
    Serialize the fields from Airtable record to avoid new lines and
    trailing backslashes in strings.

    Args:
        target_fields (Dict): The fields from the Airtable record to serialize.

    Returns:
        Dict: A serialized attributes map.
    """
    result = {}
    for key, value in target_fields.items():
        if isinstance(value, str):
            val = value.replace("\n", "")
            if val.endswith("\\"):
                val += "\\"
            result[key] = val
        else:
            result[key] = value

    return result


def parse_useful_payloads(payload: Dict) -> Dict:
    """Parse the payloads with useful information.

    This method is used to filter out the payloads that are not
    useful for processing and syncing airtable to AYON.

    Args:
        payload (Dict): The payload data from the event.

    Returns:
        Dict: A dictionary containing the base ID and changed tables IDs.

    """
    base_id = payload["base_id"]
    airtable_payload = payload.get("airtable_payloads", {})
    changed_record_by_tables_ids = {}
    if not airtable_payload:
        log.warning("No Airtable payloads found in the event.")
        return {
            "base_id": base_id,
            "changed_tables_ids": changed_record_by_tables_ids,
        }

    for payload_data in airtable_payload.values():
        changed_tables = payload_data.get("changed_tables_by_id", {})
        for table_id, changed_data in changed_tables.items():
            changed_record_by_tables_ids[table_id] = set()
            for record_by_id in changed_data.get("changed_records_by_id", {}).keys():
                changed_record_by_tables_ids[table_id].add(record_by_id)

    return {
        "base_id": base_id,
        "changed_tables_ids": changed_record_by_tables_ids,
    }

def sync_projects_from_airtable(api: pyairtable.Api, payload: Dict,
                                required_fields: list, attribs_map: Dict):
    """ Sync projects from Airtable to AYON.

    Args:
        api (pyairtable.Api): access to Airtable API
        payload (Dict): The payload data from the event.
        required_fields (list): required fields to check in the Airtable record.
        attribs_map (Dict): attributes mapping from AYON to Airtable.
    """
    parsed_payload = parse_useful_payloads(payload)
    base_id = parsed_payload["base_id"]
    base = api.base(base_id)
    base_meta_url = base.urls.meta
    if parsed_payload.get("changed_records_by_id", {}):
        for table_id, record_ids in parsed_payload["changed_tables_ids"].items():
            table = base.table(table_id)
            for record_id in record_ids:
                try:
                    record = table.get(record_id)
                    log.info(f"Processing record: {record}")
                    target_fields = record.get("fields", {})
                    if not all(field in target_fields for field in required_fields):
                        log.warning(
                            f"Record {record_id} does not have "
                            "'Project', 'Status', or 'VersionId' fields."
                        )
                        continue
                    sync_from_airtable_to_ayon(
                        base_id,
                        base_meta_url,
                        target_fields,
                        attribs_map
                    )
                except Exception as e:
                    log.error(
                        f"Error processing record {record_id}: {e}",
                        exc_info=True
                    )


def sync_from_airtable_to_ayon(base_id: str, base_url: str,
                               target_fields: Dict, attribs_map: Dict):
    """ Sync data from Airtable to AYON.

    Args:
        base_id (str): ID of the Airtable base.
        base_url (str): meta url of the Airtable base.
        target_fields (Dict): target fields from the Airtable record.
        attribs_map (Dict): attributes mapping from AYON to Airtable.

    """

    target_fields = serialize_fields(target_fields)
    airtable_project = attribs_map["project"]
    project = target_fields[airtable_project]
    version_id = attribs_map["version_id"]
    try:
        ayon_entity_hub = EntityHub(project)
        project_entity = ayon_entity_hub.project_entity
    except Exception as e:
        raise ValueError(f"Unable to get EntityHub for project '{project}': {e}")

    ayon_entity = ayon_entity_hub.get_or_query_entity_by_id(version_id, ["version"])
    # can we use much simpler function?
    # ayon_entity = ayon_entity_hub.get_version_by_id(version_id)
    if ayon_entity is None:
        raise ValueError("Unable to update a non existing entity.")

    # make sure the entity is not immutable
    if ayon_entity.immutable_for_hierarchy:
        raise ValueError("Entity is immutable, aborting...")

    airtable_status = attribs_map["status"]
    all_status_attribs_matched = set(
        status.name for status in project_entity.statuses
    )
    new_status = target_fields[airtable_status]
    if new_status in all_status_attribs_matched:
        ayon_entity.status = new_status
    else:
        log.warning(
            f"Status '{new_status}' not available"
            f" for {ayon_entity.entity_type}."
        )

    ayon_entity_airtable_id = str(
        ayon_entity.attribs.get_attribute(AIRTABLE_ID_ATTRIB).value)
    ayon_entity_airtable_path = str(
        ayon_entity.attribs.get_attribute(AIRTABLE_PATH_ATTRIB).value)

    # Ensure AYON Entity has the correct base ID and url.
    if ayon_entity_airtable_id != base_id:
        ayon_entity.attribs.set(
            AIRTABLE_ID_ATTRIB,
            base_id
        )
    if ayon_entity_airtable_path != base_url:
        ayon_entity.attribs.set(
            AIRTABLE_PATH_ATTRIB,
            base_url
        )

    ayon_entity_hub.commit_changes()

