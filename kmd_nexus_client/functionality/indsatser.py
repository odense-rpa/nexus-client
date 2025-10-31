from datetime import datetime, timezone
from typing import Optional, List
from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.tree_helpers import find_nodes


class IndsatsClient:
    """
    Klient til indsats-operationer i KMD Nexus.

    VIGTIGT: Opret ikke denne klasse direkte!
    Brug NexusClientManager: nexus.indsatser.hent_indsats(...)
    """

    def __init__(self, nexus_client: NexusClient):
        self.client = nexus_client

    def rediger_indsats(self, indsats: dict, ændringer: dict, overgang: str) -> dict:
        """
        Rediger en indsats.

        :param indsats: Indsatsen der skal redigeres.
        :param ændringer: Dictionary med feltændringer der skal anvendes.
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
            raise ValueError(
                f"Overgang {overgang} er ikke tilgængelig for denne indsats"
            )

        prototype = self.client.get(
            overgang_obj["_links"]["prepareEdit"]["href"]
        ).json()

        self._fill_grant_elements(prototype["elements"], ændringer)

        response = self.client.post(prototype["_links"]["save"]["href"], json=prototype)

        return response.json()

    def hent_indsats_elementer(self, indsats: dict) -> dict:
        """
        Hent en indsats' elementer.

        :param indsats: Indsatsen at hente elementer for.
        :return: Indsatsens elementer.
        """
        dest = {}

        if indsats.get("currentElements", {}):
            elements = indsats["currentElements"]
        elif indsats.get("futureElements", {}):
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
        felter: dict = {},
        leverandør: str = "",
        oprettelsesform: str = "",
        indsatsnote: str = "",
    ) -> dict:
        """
        Opret en ny indsats.

        :param borger: Borgeren som indsatsen skal oprettes for
        :param grundforløb: Grundforløbets navn (f.eks. "Sundhedsfagligt grundforløb")
        :param forløb: Forløbets navn (f.eks. "FSIII")
        :param indsats: Navnet på indsatsen der skal oprettes
        :param felter: Valgfri dictionary med feltværdier
        :param leverandør: Valgfri leverandørs navn
        :param oprettelsesform: Oprettelsesform/overgangs navn (f.eks. "Ansøg, Bevilg, Bestil")
        :param indsatsnote: Valgfri note til indsatsen
        :return: tupple med 'indsats' (indsats objekt), 'succes' (boolean), 'error' (str, hvis fejl opstod)
        :raises ValueError: Hvis indsatsen ikke findes i kataloget eller der opstår fejl under oprettelse
        :raises httpx.HTTPStatusError: Hvis der opstår HTTP fejl under API kald
        """
        # Get the correct basket for this pathway combination
        basket = self._get_correct_basket(borger, grundforløb, forløb)

        # Find the grant in the catalog and get its ID
        grant_id, is_package = self._find_grant_in_catalog(basket, indsats)

        # Create the grant from prototype
        created_grant = self._create_grant_from_prototype(basket, grant_id, is_package)

        # Configure and save the grant
        final_grant = self._configure_and_save_grant(
            created_grant, oprettelsesform, leverandør, felter
        )

        # Add note if provided
        if indsatsnote:
            self._add_grant_note(final_grant, indsatsnote)

        return final_grant

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
                n.get("name") == grant_name
                and n.get("type") in ["catalogGrant", "catalogPackage"]
            ),
            children_key="subcatalogs",
            find_all=False,
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
            self._fill_grant_elements(template["elements"], fields)

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

    def _fill_grant_elements(self, elements: List[dict], fields: dict) -> None:
        """Fill grant elements with field values. Complex logic preserved from Blue Prism."""
        # elements = target_elements.get("elements", [])

        for field_name, field_value in fields.items():
            element = next((e for e in elements if e.get("type") == field_name), None)

            if not element:
                raise ValueError(f"Field '{field_name}' not found in template elements")

            if "text" in element:
                if not isinstance(field_value, str):
                    raise ValueError(f"Field '{field_name}' expects a string value")
                element["text"] = field_value
                continue

            if "date" in element:
                if not isinstance(field_value, datetime):
                    raise ValueError(f"Field '{field_name}' expects a date value")

                if field_value.tzinfo is None:
                    # Assume local time, make it timezone-aware, then convert to UTC
                    local_dt = field_value.replace(
                        tzinfo=datetime.now().astimezone().tzinfo
                    )
                    utc_dt = local_dt.astimezone(timezone.utc)
                else:
                    # Already timezone-aware, convert to UTC
                    utc_dt = field_value.astimezone(timezone.utc)

                element["date"] = utc_dt.isoformat().replace("+00:00", "Z")
                continue

            # Apparently value fields are bools if there are no possibleValues
            if "value" in element and "possibleValues" not in element:
                if not isinstance(field_value, bool):
                    raise ValueError(f"Field '{field_name}' expects a boolean value")

                element["value"] = field_value
                continue

            # Default handling of value fields
            if "value" in element and "possibleValues" in element:
                if not isinstance(field_value, str):
                    raise ValueError(f"Field '{field_name}' expects a string value")

                if field_value not in element.get("possibleValues", []):
                    raise ValueError(
                        f"Value '{field_value}' not in possible values for field '{field_name}'"
                    )

                element["value"] = field_value
                continue

            # Handle selectedValues field
            if "selectedValues" in element:
                if not isinstance(field_value, list):
                    raise ValueError(
                        f"Field '{field_name}' expects a list of selected values"
                    )

                # Validate each selected value against possible values
                for value in field_value:
                    if not isinstance(value, str):
                        raise ValueError(
                            f"Selected value '{value}' in field '{field_name}' must be a string"
                        )
                    if value not in element.get("possibleValues", []):
                        raise ValueError(
                            f"Selected value '{value}' not in possible values for field '{field_name}'"
                        )

                element["selectedValues"] = field_value
                continue

            # Handle decimal fields
            if "decimal" in element:
                if not isinstance(field_value, (int, float)):
                    raise ValueError(f"Field '{field_name}' expects a decimal value")

                # TODO: Actually verify decimal format used by Nexus
                element["decimal"] = field_value
                continue

            # Supplier
            if "supplier" in element:
                if not isinstance(field_value, str):
                    raise ValueError(f"Field '{field_name}' expects a supplier name")

                # Get available suppliers and find match
                suppliers = self.client.get(
                    element["_links"]["availableSuppliers"]["href"]
                ).json()

                matching_supplier = next(
                    (s for s in suppliers if s.get("name") == field_value), None
                )

                if not matching_supplier:
                    raise ValueError(f"Supplier '{field_value}' not found")

                element["supplier"] = matching_supplier
                continue

            raise ValueError(f"Unsupported field type for '{field_name}' in template")

    def _add_grant_note(self, grant: dict, note: str) -> None:
        """Add note to grant."""
        order_grant_id = grant.get("savedGrant", {}).get("currentOrderGrantId")
        if not order_grant_id:
            raise ValueError("Could not find currentOrderGrantId in saved grant")

        note_url = f"{self.client.base_url}/patientGrants/supplierComment?orderGrantIds={order_grant_id}"
        self.client.post(note_url, json={"comment": note})

    def filtrer_indsats_referencer(
        self,
        indsats_referencer: List[dict],
        kun_aktive: bool = True,
        leverandør_navn: str = "",
        inkluder_indsatspakker: bool = False,
    ) -> List[dict]:
        """
        Filtrer indsatsreferencer.

        :param indsatser_referencer: Liste af indsatser referencer at filtrere
        :param kun_aktive: Om kun aktive indsatser skal inkluderes
        :param leverandør_navn: Valgfri leverandør navn at filtrere efter
        :param inkluder_indsatspakker: Om indsatspakker skal inkluderes i resultatet
        :return: Filtreret liste af indsatser referencer
        """

        filtered_refs = find_nodes(
            indsats_referencer,
            lambda node: (
                (
                    node.get("type") == "basketGrantReference"
                    and (
                        not kun_aktive
                        or (
                            kun_aktive
                            and node.get("workflowState", {}).get("name")
                            not in [
                                "Afsluttet",
                                "Annulleret",
                                "Fjernet",
                                "Frafaldet",
                                "Afgjort",
                                "Afslået",
                            ]
                        )
                    )
                    and (
                        leverandør_navn == ""
                        or any(
                            [
                                leverandør
                                for leverandør in node.get("additionalInfo", [])
                                if leverandør.get("key") == "Leverandør"
                                and leverandør.get("value") == leverandør_navn
                            ]
                        )
                    )
                )
                or (
                    inkluder_indsatspakker
                    and node.get("type") == "basketGrantPackageReference"
                )
            ),
            children_key="children",
        )

        return filtered_refs

    def hent_indsats(self, indsats_reference: dict) -> dict:
        """
        Hent fulde indsats detaljer fra en indsats reference.

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

        return grant_response.json()
