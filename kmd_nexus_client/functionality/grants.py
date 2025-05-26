from datetime import datetime
from httpx import HTTPStatusError

from kmd_nexus_client.client import NexusClient

def update_grant_elements(current_elements, field_updates):
    for item in current_elements:
        item_type = item.get('type')

        # Check if the type exists in field_updates
        if item_type in field_updates:
            new_value = field_updates[item_type]

            # Apply the update based on the type
            if item_type == 'description' and 'text' in item:
                item['text'] = new_value
            elif item_type == 'plannedDate' and 'date' in item:
                item['date'] = new_value
            elif item_type == 'allocationDate' and 'date' in item:
                item['date'] = new_value
            elif item_type == 'orderedDate' and 'date' in item:
                item['date'] = new_value
            elif item_type == 'entryDate' and 'date' in item:
                item['date'] = new_value
            elif item_type == 'serviceDelivery' and 'date' in item:
                item['date'] = new_value
            elif item_type == 'billingStartDate' and 'date' in item:
                item['date'] = new_value
            elif item_type == 'billingEndDate' and 'date' in item:
                item['date'] = new_value
            elif item_type == 'followUpDate' and 'date' in item:
                item['date'] = new_value
            elif item_type == 'repetition' and 'next' in item:
                item['next'] = new_value
            elif item_type == 'value' and 'value' in item:
                item['value'] = new_value
            elif item_type == 'text' and 'text' in item:
                item['text'] = new_value
            elif item_type == 'number' and 'number' in item:
                item['number'] = new_value            
            
    return current_elements

class GrantsClient:
    def __init__(self, nexus_client: NexusClient):
            self.client = nexus_client

    def edit_grant(self, grant: dict, changes: dict, transition: str) -> dict:
        """
        Edit a grant.

        :param grant: The grant to edit.
        :param transition: The transition to apply to the grant.
        :return: The updated grant.
        """
        
        if "currentWorkflowTransitions" not in grant:
            raise ValueError("Grant does not have any transitions")
        
        transition = next((t for t in grant["currentWorkflowTransitions"] if t["name"] == transition), None)              

        if not transition:
            raise ValueError(f"Transition {transition} is not available for this grant")
      
        try:
            prototype = self.client.get(transition["_links"]["prepareEdit"]["href"]).json()
            prototype["elements"] = update_grant_elements(prototype["elements"], changes)

            response = self.client.post(
                prototype["_links"]["save"]["href"],
                json = prototype
            )

            return response.json()
        
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_grant_elements(self, grant: dict) -> dict:
        """
        Get a grant's elements.

        :param grant: The grant to retrieve elements for.
        :return: The grant's elements.
        """
        dest = {}

        if "currentElements" in grant:
            elements = grant["currentElements"]
        elif "futureElements" in grant:
            elements = grant["futureElements"]
        else:
            return dest

        if elements is None:
            return dest

        for child in elements:
            if "text" in child:
                dest[child["type"]] = child["text"]
                continue

            if "date" in child:
                date_value = child["date"]
                dest[child["type"]] = datetime.fromisoformat(date_value) if date_value else None
                continue

            if "number" in child:
                dest[child["type"]] = child["number"]
                continue

            if "decimal" in child:
                dest[child["type"]] = child["decimal"]
                continue

            if "boolean" in child:
                dest[child["type"]] = child["boolean"]
                continue

            dest[child["type"]] = child

        return dest

    