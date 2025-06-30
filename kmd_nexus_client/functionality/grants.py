from datetime import datetime, timezone
from httpx import HTTPStatusError
from typing import Optional, List
from kmd_nexus_client.client import NexusClient


def update_grant_elements(current_elements, field_updates):
    for item in current_elements:
        item_type = item.get("type")

        # Check if the type exists in field_updates
        if item_type in field_updates:
            new_value = field_updates[item_type]

            # Apply the update based on the type
            if item_type == "description" and "text" in item:
                item["text"] = new_value
            elif item_type == "plannedDate" and "date" in item:
                item["date"] = new_value
            elif item_type == "allocationDate" and "date" in item:
                item["date"] = new_value
            elif item_type == "orderedDate" and "date" in item:
                item["date"] = new_value
            elif item_type == "entryDate" and "date" in item:
                item["date"] = new_value
            elif item_type == "serviceDelivery" and "date" in item:
                item["date"] = new_value
            elif item_type == "billingStartDate" and "date" in item:
                item["date"] = new_value
            elif item_type == "billingEndDate" and "date" in item:
                item["date"] = new_value
            elif item_type == "followUpDate" and "date" in item:
                item["date"] = new_value
            elif item_type == "repetition" and "next" in item:
                item["next"] = new_value
            elif item_type == "value" and "value" in item:
                item["value"] = new_value
            elif item_type == "text" and "text" in item:
                item["text"] = new_value
            elif item_type == "number" and "number" in item:
                item["number"] = new_value

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

        transition = next(
            (t for t in grant["currentWorkflowTransitions"] if t["name"] == transition),
            None,
        )

        if not transition:
            raise ValueError(f"Transition {transition} is not available for this grant")

        try:
            prototype = self.client.get(
                transition["_links"]["prepareEdit"]["href"]
            ).json()
            prototype["elements"] = update_grant_elements(
                prototype["elements"], changes
            )

            response = self.client.post(
                prototype["_links"]["save"]["href"], json=prototype
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
                dest[child["type"]] = (
                    datetime.fromisoformat(date_value) if date_value else None
                )
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

    # These are AI generated conversions of the Blue Prism Code

    def create_grant(
        self,
        citizen: dict,
        grundforløb: str,
        forløb: str,
        indsats: str,
        leverandør: str = "",
        oprettelsesform: str = "",
        felter: Optional[dict] = None,
        indsatsnote: str = "",
    ) -> dict:
        """
        Create a new grant (Opret indsats).

        :param citizen: The citizen to create the grant for
        :param grundforløb: The pathway name (e.g., "Sundhedsfagligt grundforløb")
        :param forløb: The course name (e.g., "FSIII")
        :param indsats: The grant name to create
        :param leverandør: Optional supplier name
        :param oprettelsesform: The creation form/transition name (e.g., "Tildel, Bestil")
        :param felter: Optional dictionary of field values
        :param indsatsnote: Optional note to attach to the grant
        :return: Dict with 'indsats' (grant object) and 'succes' (boolean)
        """
        try:
            # Get the correct basket for this pathway combination
            basket = self._get_correct_basket(citizen, grundforløb, forløb)

            # Find the grant in the catalog and get its ID
            grant_id, is_package = self._find_grant_in_catalog(basket, indsats)

            # Create the grant from prototype
            created_grant = self._create_grant_from_prototype(
                basket, grant_id, is_package
            )

            # Configure and save the grant
            final_grant = self._configure_and_save_grant(
                created_grant, oprettelsesform, leverandør, felter
            )

            # Add note if provided
            if indsatsnote:
                self._add_grant_note(final_grant, indsatsnote)

            return {"indsats": final_grant, "succes": True}

        except Exception as e:
            return {"indsats": None, "succes": False, "error": str(e)}

    def _get_correct_basket(self, citizen: dict, grundforløb: str, forløb: str) -> dict:
        """Get the basket for the specified pathway combination."""
        # Get available baskets
        baskets = self.client.get(citizen["_links"]["availableBaskets"]["href"]).json()

        # Find matching basket
        expected_placement = f"{grundforløb} > {forløb}"
        matching_baskets = [
            basket
            for basket in baskets
            if basket.get("pathwayPlacementName") == expected_placement
        ]

        if len(matching_baskets) != 1:
            raise ValueError(
                f"Expected exactly 1 basket for '{expected_placement}', found {len(matching_baskets)}"
            )

        # Get complete basket details
        return self.client.get(matching_baskets[0]["_links"]["self"]["href"]).json()

    def _find_grant_in_catalog(self, basket: dict, grant_name: str) -> tuple[int, bool]:
        """Find grant ID and package status in the catalog."""
        # Get grant catalog
        catalog = self.client.get(basket["_links"]["grantCatalog"]["href"]).json()

        # Search catalog recursively
        for catalog_item in catalog:
            grant_id, is_package = self._search_catalog_tree(catalog_item, grant_name)
            if grant_id != 0:
                return grant_id, is_package

        raise ValueError(f"Grant '{grant_name}' not found in catalog")

    def _search_catalog_tree(self, node: dict, grant_name: str) -> tuple[int, bool]:
        """Recursively search catalog tree for grant."""
        # Check current node
        if node.get("name") == grant_name and node.get("type") in [
            "catalogGrant",
            "catalogPackage",
        ]:
            return int(node["id"]), node.get("type") == "catalogPackage"

        # Search subcatalogs
        for subcatalog in node.get("subcatalogs", []):
            grant_id, is_package = self._search_catalog_tree(subcatalog, grant_name)
            if grant_id != 0:
                return grant_id, is_package

        return 0, False

    def _create_grant_from_prototype(
        self, basket: dict, grant_id: int, is_package: bool
    ) -> dict:
        """Create grant from prototype."""
        # Get and fill prototype
        prototype = self.client.get(basket["_links"]["bulkPrototype"]["href"]).json()

        prototype["catalogGrantId"] = grant_id
        prototype["basketId"] = basket["id"]
        prototype["key"] = f"null:{grant_id}:{str(is_package).lower()}"
        if is_package:
            prototype["isPackage"] = True

        # Create grant
        response = self.client.post(
            basket["_links"]["bulkGet"]["href"], json=[prototype]
        )  # type: ignore
        created_grants = response.json()

        if not created_grants:
            raise ValueError("No grant created from prototype")

        return created_grants

    def _configure_and_save_grant(
        self,
        grant: dict,
        transition_name: str,
        supplier_name: str,
        fields: Optional[dict],
    ) -> dict:
        """Configure the grant with supplier and fields, then save."""
        # Find workflow transition
        transitions = [
            t
            for t in grant.get("currentWorkflowTransitions", [])
            if t.get("name") == transition_name
        ]

        if len(transitions) != 1:
            raise ValueError(
                f"Expected exactly 1 transition '{transition_name}', found {len(transitions)}"
            )

        # Get edit template
        template = self.client.get(
            transitions[0]["_links"]["prepareEdit"]["href"]
        ).json()

        # Handle supplier if provided
        if supplier_name:
            self._set_supplier(template, supplier_name)

        # Handle fields if provided
        if fields:
            self._fill_template_with_fields(template, fields)

        # Save grant
        return self.client.post(
            template["_links"]["save"]["href"], json=template
        ).json()

    def _set_supplier(self, template: dict, supplier_name: str) -> None:
        """Set supplier in template."""
        elements = template.get("elements", [])
        supplier_element = next(
            (e for e in elements if e.get("type") == "supplier"), None
        )

        if not supplier_element:
            return

        # Get available suppliers and find match
        suppliers = self.client.get(
            supplier_element["_links"]["availableSuppliers"]["href"]
        ).json()
        matching_supplier = next(
            (s for s in suppliers if s.get("name") == supplier_name), None
        )

        if not matching_supplier:
            raise ValueError(f"Supplier '{supplier_name}' not found")

        supplier_element["supplier"] = matching_supplier

    def _fill_template_with_fields(self, template: dict, fields: dict) -> None:
        """Fill template with field values. Complex logic preserved from Blue Prism."""
        elements = template.get("elements", [])

        for field_name, field_value in fields.items():
            element = next((e for e in elements if e.get("type") == field_name), None)

            if element:
                if isinstance(field_value, str):
                    if "text" in element:
                        element["text"] = field_value
                    if "value" in element:
                        element["value"] = field_value
                    if "pattern" in element:
                        element["pattern"] = field_value
                elif isinstance(field_value, (int, float)):
                    element["number"] = int(field_value)
                elif isinstance(field_value, datetime):
                    # Handle timezone-naive datetime (assume local time) and convert to UTC
                    if field_value.tzinfo is None:
                        # Assume local time, make it timezone-aware, then convert to UTC
                        local_dt = field_value.replace(
                            tzinfo=datetime.now().astimezone().tzinfo
                        )
                        utc_dt = local_dt.astimezone(timezone.utc)
                    else:
                        # Already timezone-aware, convert to UTC
                        utc_dt = field_value.astimezone(timezone.utc)

                    element["date"] = utc_dt.isoformat().replace(
                        "+00:00", "Z"
                    )  # TODO: Add more complex field type handling as needed

    def _add_grant_note(self, grant: dict, note: str) -> None:
        """Add note to grant."""
        order_grant_id = grant.get("savedGrant", {}).get("currentOrderGrantId")
        if not order_grant_id:
            raise ValueError("Could not find currentOrderGrantId in saved grant")

        note_url = f"{self.client.base_url}/patientGrants/supplierComment?orderGrantIds={order_grant_id}"
        self.client.post(note_url, json={"comment": note})

    # Other grant functions

    def get_grant_references(
        self, citizen: dict, pathway_name: str = "- Alt", include_grant_packages=False
    ) -> List[dict]:
        """
        Get grant references for a citizen (Hent indsatsereferencer).

        :param citizen: The citizen to retrieve grant references for
        :param pathway_name: The pathway name to use (default: "- Alt")
        :return: List of grant references
        """
        # Get citizen pathway
        pathway = self._get_citizen_pathway(citizen, pathway_name)

        # Get pathway references
        references_response = self.client.get(
            pathway["_links"]["pathwayReferences"]["href"]
        )
        references_json = references_response.json()

        # Use complex tree traversal to find grant references (matching Blue Prism logic)
        grant_references = []
        for pathway_root in references_json:
            matching_references = self._find_all_matching_nodes(
                pathway_root,
                lambda node: (
                    (
                        node.get("type") == "basketGrantReference"
                        and node.get("workflowState", {}).get("name") != "Afsluttet"
                    )
                    or (
                        include_grant_packages
                        and node.get("type") == "basketGrantPackageReference"
                    )
                ),
                "children",
            )
            grant_references.extend(matching_references)

        return grant_references

    def get_grant(self, grant_reference: dict) -> dict:
        """
        Get full grant details from a grant reference (Hent indsats).

        :param grant_reference: The grant reference to resolve
        :return: Dict with 'grant' (full grant object) and 'field_values' (extracted values)
        """
        # Check if this is a reference that needs resolving
        if "type" not in grant_reference:
            raise ValueError("Input is not a valid grant reference")

        # Handle different reference types (matching Blue Prism's choice logic)
        if grant_reference.get("type") == "basketGrantReference":
            # Direct grant reference
            grant_url = grant_reference["_links"]["referencedObject"]["href"]
        elif grant_reference.get("type") == "basketGrantPackageReference":
            # Package reference - get the package first
            package_response = self.client.get(
                grant_reference["_links"]["self"]["href"]
            )
            package = package_response.json()
            grant_url = package["_links"]["referencedObject"]["href"]
        else:
            raise ValueError(f"Unknown reference type: {grant_reference.get('type')}")

        # Get the full grant object
        grant_response = self.client.get(grant_url)
        grant = grant_response.json()

        return grant

    def filter_grant_references(
        self,
        grant_references: List[dict],
        active_only: bool = True,
        supplier_name: str = "",
    ) -> List[dict]:
        """
        Filter grant references (Filtrer indsatsreferencer).

        :param grant_references: List of grant references to filter
        :param active_only: Whether to include only active grants
        :param supplier_name: Optional supplier name to filter by
        :return: Filtered list of grant references
        """
        filtered_refs = []

        for ref in grant_references:
            # Filter by active status (matching Blue Prism's workflow state logic)
            if active_only:
                workflow_state = ref.get("workflowState", {}).get("name", "")
                active_states = [
                    "Bestilt",
                    "Bevilliget",
                    "Planlagt, ikke bestilt",
                    "Ændret",
                ]
                if workflow_state not in active_states:
                    continue

            # Filter by supplier if specified (matching Blue Prism's supplier filtering)
            if supplier_name:
                # Check if reference has additional info with sufficient columns
                additional_info = ref.get("additionalInfo", [])
                if len(additional_info) <= 2:
                    continue

                # Look for supplier info
                supplier_info = next(
                    (
                        info
                        for info in additional_info
                        if info.get("key") == "Leverandør"
                    ),
                    None,
                )

                if not supplier_info or supplier_info.get("value") != supplier_name:
                    continue

            filtered_refs.append(ref)

        return filtered_refs

    # Helper methods for get_grant_references, get_grant, and filter_grant_references
    def _get_citizen_pathway(self, citizen: dict, pathway_name: str = "- Alt") -> dict:
        """Get citizen pathway."""
        preferences_response = self.client.get(
            citizen["_links"]["patientPreferences"]["href"]
        )
        preferences = preferences_response.json()

        for item in preferences["CITIZEN_PATHWAY"]:
            if item["name"] == pathway_name:
                return self.client.get(item["_links"]["self"]["href"]).json()

        raise ValueError(f"Pathway '{pathway_name}' not found")

    def _find_all_matching_nodes(
        self, root: dict, condition, node_name: str = "children"
    ) -> List[dict]:
        """
        Find all nodes in a tree that match a condition (Blue Prism's 'All' method).

        :param root: The root node to start search from
        :param condition: Function that returns True for matching nodes
        :param node_name: The property name containing child nodes
        :return: List of all matching nodes
        """
        result = []

        def collect_matching(node: dict) -> None:
            if condition(node):
                result.append(node)

        self._traverse_tree(root, collect_matching, node_name)
        return result

    def _traverse_tree(self, root: dict, callback, node_name: str = "children") -> None:
        """
        Traverse a tree structure recursively (Blue Prism's 'Traverse' method).

        :param root: The root node to start traversal from
        :param callback: Function to call on each node
        :param node_name: The property name containing child nodes
        """
        callback(root)

        children = root.get(node_name)
        if children and isinstance(children, list):
            for child in children:
                self._traverse_tree(child, callback, node_name)

    def _extract_field_values(self, elements: List[dict]) -> dict:
        """
        Extract field values from grant elements (Blue Prism's element extraction logic).
        """
        field_values = {}

        for element in elements:
            element_type = element.get("type")
            if "text" in element:
                field_values[element_type] = element["text"]
            elif "date" in element and element["date"] is not None:
                field_values[element_type] = element["date"]
            elif "number" in element:
                field_values[element_type] = element["number"]
            elif "decimal" in element:
                field_values[element_type] = element["decimal"]
            elif "boolean" in element:
                field_values[element_type] = element["boolean"]
            else:
                # Store the whole element for complex types
                field_values[element_type] = element

        return field_values
