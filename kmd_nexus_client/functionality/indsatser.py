from datetime import datetime, timezone
from httpx import HTTPStatusError
from typing import Optional, List
from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.tree_helpers import find_node_by_id, find_nodes


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


class IndsatsClient:
    def __init__(self, nexus_client: NexusClient):
        self.client = nexus_client

    def rediger_indsats(self, indsats: dict, ændringer: dict, overgang: str) -> dict:
        """
        Rediger en indsats.

        :param indsats: Indsatsen der skal redigeres.
        :param overgang: Overgangen der skal anvendes på indsatsen.
        :return: Den opdaterede indsats.
        """

        if "currentWorkflowTransitions" not in indsats:
            raise ValueError("Indsats har ingen overgange")

        overgang_obj = next(
            (t for t in indsats["currentWorkflowTransitions"] if t["name"] == overgang),
            None,
        )

        if not overgang_obj:
            raise ValueError(f"Overgang {overgang} er ikke tilgængelig for denne indsats")

        try:
            prototype = self.client.get(
                overgang_obj["_links"]["prepareEdit"]["href"]
            ).json()
            prototype["elements"] = update_grant_elements(
                prototype["elements"], ændringer
            )

            response = self.client.post(
                prototype["_links"]["save"]["href"], json=prototype
            )

            return response.json()

        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def hent_indsats_elementer(self, indsats: dict) -> dict:
        """
        Hent en indsats' elementer.

        :param indsats: Indsatsen at hente elementer for.
        :return: Indsatsens elementer.
        """
        dest = {}

        if "currentElements" in indsats:
            elements = indsats["currentElements"]
        elif "futureElements" in indsats:
            elements = indsats["futureElements"]
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

    def opret_indsats(
        self,
        borger: dict,
        grundforløb: str,
        forløb: str,
        indsats: str,
        leverandør: str = "",
        oprettelsesform: str = "",
        felter: Optional[dict] = None,
        indsatsnote: str = "",
    ) -> dict:
        """
        Opret en ny indsats.

        :param borger: Borgeren som indsatsen skal oprettes for
        :param grundforløb: Grundforløbets navn (f.eks. "Sundhedsfagligt grundforløb")
        :param forløb: Forløbets navn (f.eks. "FSIII")
        :param indsats: Navnet på indsatsen der skal oprettes
        :param leverandør: Valgfri leverandørs navn
        :param oprettelsesform: Oprettelsesform/overgangs navn (f.eks. "Tildel, Bestil")
        :param felter: Valgfri dictionary med feltværdier
        :param indsatsnote: Valgfri note til indsatsen
        :return: Dict med 'indsats' (indsats objekt) og 'succes' (boolean)
        """
        try:
            # Get the correct basket for this pathway combination
            basket = self._get_correct_basket(borger, grundforløb, forløb)

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
        """Search catalog tree for grant using unified tree helpers."""
        # Use tree_helpers to find the grant
        matching_node = find_nodes(
            node,
            lambda n: (
                n.get("name") == grant_name and 
                n.get("type") in ["catalogGrant", "catalogPackage"]
            ),
            children_key="subcatalogs",
            find_all=False
        )
        
        if matching_node:
            found_node = matching_node[0]
            return int(found_node["id"]), found_node.get("type") == "catalogPackage"
        
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

    def hent_indsatser_referencer(
        self, borger: dict, forløbsnavn: str = "- Alt", inkluder_indsats_pakker=False
    ) -> List[dict]:
        """
        Hent indsatser referencer for en borger.

        :param borger: Borgeren at hente indsatser referencer for
        :param forløbsnavn: Forløbsnavnet at bruge (standard: "- Alt")
        :return: Liste af indsatser referencer
        """
        # Get citizen pathway
        pathway = self._get_citizen_pathway(borger, forløbsnavn)

        # Get pathway references
        references_response = self.client.get(
            pathway["_links"]["pathwayReferences"]["href"]
        )
        references_json = references_response.json()

        # Use tree_helpers to find grant references
        grant_references = find_nodes(
            references_json,
            lambda node: (
                (
                    node.get("type") == "basketGrantReference"
                    and node.get("workflowState", {}).get("name") != "Afsluttet"
                )
                or (
                    inkluder_indsats_pakker
                    and node.get("type") == "basketGrantPackageReference"
                )
            ),
            children_key="children"
        )

        return grant_references

    def hent_indsats(self, indsats_reference: dict) -> dict:
        """
        Hent fuld indsats detaljer fra en indsats reference.

        :param indsats_reference: Indsats referencen der skal opløses
        :return: Fuld indsats objekt
        """
        # Check if this is a reference that needs resolving
        if "type" not in indsats_reference:
            raise ValueError("Input er ikke en gyldig indsats reference")

        # Handle different reference types (matching Blue Prism's choice logic)
        if indsats_reference.get("type") == "basketGrantReference":
            # Direct grant reference
            grant_url = indsats_reference["_links"]["referencedObject"]["href"]
        elif indsats_reference.get("type") == "basketGrantPackageReference":
            # Package reference - get the package first
            package_response = self.client.get(
                indsats_reference["_links"]["self"]["href"]
            )
            package = package_response.json()
            grant_url = package["_links"]["referencedObject"]["href"]
        else:
            raise ValueError(f"Ukendt reference type: {indsats_reference.get('type')}")

        # Get the full grant object
        grant_response = self.client.get(grant_url)
        grant = grant_response.json()

        return grant

    def filtrer_indsatser_referencer(
        self,
        indsatser_referencer: List[dict],
        kun_aktive: bool = True,
        leverandør_navn: str = "",
    ) -> List[dict]:
        """
        Filtrer indsatser referencer.

        :param indsatser_referencer: Liste af indsatser referencer at filtrere
        :param kun_aktive: Om kun aktive indsatser skal inkluderes
        :param leverandør_navn: Valgfri leverandør navn at filtrere efter
        :return: Filtreret liste af indsatser referencer
        """
        filtered_refs = []

        for ref in indsatser_referencer:
            # Filter by active status (matching Blue Prism's workflow state logic)
            if kun_aktive:
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
            if leverandør_navn:
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

                if not supplier_info or supplier_info.get("value") != leverandør_navn:
                    continue

            filtered_refs.append(ref)

        return filtered_refs

    # Helper methods for hent_indsatser_referencer, hent_indsats, and filtrer_indsatser_referencer
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

    # Backward compatibility aliases
    edit_grant = rediger_indsats
    get_grant_elements = hent_indsats_elementer
    create_grant = opret_indsats
    get_grant_references = hent_indsatser_referencer
    get_grant = hent_indsats
    filter_grant_references = filtrer_indsatser_referencer


# Backward compatibility class alias
GrantsClient = IndsatsClient
