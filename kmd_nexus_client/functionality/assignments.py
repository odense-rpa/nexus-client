from datetime import date
from httpx import HTTPStatusError
from kmd_nexus_client.client import NexusClient
from typing import List, Optional

class AssignmentsClient:
    def __init__(self, nexus_client: NexusClient):
        self.nexus_client = nexus_client

    def get_assignments(self, object: dict) -> List[dict]:
        """
        Get all by object assignments.

        :return: All assignments by object.
        """
        # Validate if object contains availableAssignmentTypes:
        if "availableAssignmentTypes" not in object["_links"]:
            raise ValueError("Object does not contain availableAssignmentTypes link.")
        
        response = self.nexus_client.get(object["_links"]["activeAssignments"]["href"])

        return response.json()
    
    def get_assignment_by_citizen(self, citizen: dict, assignment_id: int) -> Optional[dict]:
        # The way the API is called in this function is an exception, by directly using a hardcoded path, instead of using the HATEOAS design.
        # The alternative is to map assignment ids from the database to the citizen activity and reference json.
        """
        Get a specific assignment for a citizen by ID.

        :param citizen: The citizen to retrieve the assignment for.
        :param assignment_id: The ID of the assignment to retrieve.
        :return: The assignment details, or None if not found.
        """
        if not isinstance(citizen, dict):
            return None

        response = self.nexus_client.get(f"assignments/patient/{citizen["id"]}/assignments?ids={assignment_id}")
        
        if response.status_code == 404:
            return None
        
        return response.json()[0] if response.json() else None
    
    def create_assignment(self, object: dict, assignment_type: str, title: str, responsible_organization: str, start_date: date, due_date: date = None, description: str = None, responsible_worker: dict = None) -> dict:
        """
        Create a new assignment.

        :param object: The object to create the assignment for.
        :param assignment_type: The type of the assignment.
        :param title: The title of the assignment.
        :param responsible_organization: The organization responsible for the assignment.
        :param responsible_worker: The worker responsible for the assignment.
        :param description: The description of the assignment.
        :param start_date: The start date of the assignment.
        :param due_date: The due date of the assignment. Can be None if not specified.

        """

        # Validate if object contains availableAssignmentTypes:
        if "availableAssignmentTypes" not in object["_links"]:
            raise ValueError("Object does not contain availableAssignmentTypes link.")        
        
        available_assignment_types = self.nexus_client.get(object["_links"]["availableAssignmentTypes"]["href"]).json()
                
        # Find the correct assignment type
        assignment_type = next(
            (item 
            for item in available_assignment_types
            if item["name"] == assignment_type),None
        )

        if not assignment_type:
            raise ValueError(f"Assignment type {assignment_type} not found in available assignment types.")

        # Get prototype
        prototype = self.nexus_client.get(assignment_type["_links"]["assignmentPrototype"]["href"]).json()

        # Find correct organization
        possible_organizations = self.nexus_client.get(prototype["_links"]["availableOrganizationAssignees"]["href"]).json()
        probable_organization = next(
            (
                item 
                for item in possible_organizations
                if item["name"] == responsible_organization
            )
            , None
        )
        if not probable_organization:
            raise ValueError(f"Organization {responsible_organization} not found in available organizations.")

        # Skip responsible worker for now - need more help
       
        # Find the correct action type
        action_type = next(
            (action 
            for action in prototype["actions"]
            if action.get("name") == "Opret"), None
        )
        if not action_type:
            raise ValueError("Action type 'Opret' not found in prototype actions.")

        # Edit prototype with values
        prototype["object"] = object
        prototype["title"] = title
        #prototype["assignmentType"] = assignment_type
        prototype["organizationAssignee"] = {
                "organizationId": int(probable_organization["id"]),
                "displayName": str(probable_organization["name"]),
        }        
        prototype["startDate"] = start_date.strftime('%Y-%m-%d')
        if due_date:
            prototype["dueDate"] = due_date.strftime('%Y-%m-%d')
        if description:
            prototype["description"] = description
        if responsible_worker:
            # ask MIWN how to get responsible worker
            prototype["professionalAssignee"] = {
                "professionalId": int(responsible_worker["id"]),
                "displayName": str(responsible_worker["fullName"]),
                "displayNameWithUniqId": f"{responsible_worker['fullName']} ({responsible_worker['primaryIdentifier']})",
                "active": bool(responsible_worker["active"]),
            }

        # Create assignment
        response = self.nexus_client.post(
            action_type["_links"]["createAssignment"]["href"],
            json=prototype,
        )

        return response.json()

    def edit_assignment(self, updated_assignment: dict) -> dict:
        
        try:
            handling = next((a for a in updated_assignment["actions"] if a.get("name") == "Gem"), None)

            if not handling:
                raise ValueError("No 'Gem' action found in assignment actions.")
            
            response = self.nexus_client.put(
                handling["_links"]["updateAssignment"]["href"],
                json = updated_assignment
            )

            return response.json()
        
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        