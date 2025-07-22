"""
Tests for tree_helpers module.
"""

import pytest

from kmd_nexus_client.manager import NexusClientManager
from kmd_nexus_client.tree_helpers import (
    traverse_tree,
    find_nodes,
    find_first_node,
    find_node_by_id,
    filter_by_path,
    filter_by_predicate,
    map_tree,
    get_node_path,
    flatten_tree
)


@pytest.fixture
def sample_tree():
    """Sample tree structure for testing."""
    return {
        "id": "root",
        "name": "Root",
        "type": "root",
        "children": [
            {
                "id": "child1",
                "name": "Child 1",
                "type": "branch",
                "children": [
                    {
                        "id": "grandchild1",
                        "name": "Grandchild 1",
                        "type": "leaf",
                        "value": 10
                    },
                    {
                        "id": "grandchild2", 
                        "name": "Grandchild 2",
                        "type": "leaf",
                        "value": 20
                    }
                ]
            },
            {
                "id": "child2",
                "name": "Child 2",
                "type": "branch",
                "children": [
                    {
                        "id": "grandchild3",
                        "name": "Grandchild 3",
                        "type": "special",
                        "value": 30
                    }
                ]
            }
        ]
    }


@pytest.fixture
def pathway_tree():
    """Sample pathway tree structure similar to KMD Nexus data."""
    return {
        "id": "pathway1",
        "name": "Sundhedsfagligt grundforløb",
        "type": "patientPathwayReference",
        "pathwayStatus": "ACTIVE",
        "children": [
            {
                "id": "course1",
                "name": "FSIII",
                "type": "course",
                "children": [
                    {
                        "id": "intervention1",
                        "name": "Medicin administration",
                        "type": "basketGrantReference",
                        "workflowState": {"name": "Bestilt"},
                        "children": []
                    },
                    {
                        "id": "intervention2", 
                        "name": "Medicin dosering",
                        "type": "basketGrantReference",
                        "workflowState": {"name": "Afsluttet"},
                        "children": []
                    }
                ]
            }
        ]
    }


class TestTraverseTree:
    """Test tree traversal functionality."""
    
    def test_traverse_tree_visits_all_nodes(self, sample_tree):
        """Test that traverse_tree visits all nodes."""
        visited_nodes = []
        
        def visit_fn(node, path):
            visited_nodes.append(node["id"])
        
        traverse_tree(sample_tree, visit_fn)
        
        expected = ["root", "child1", "grandchild1", "grandchild2", "child2", "grandchild3"]
        assert visited_nodes == expected
    
    def test_traverse_tree_provides_correct_path(self, sample_tree):
        """Test that traverse_tree provides correct path information."""
        paths = []
        
        def visit_fn(node, path):
            path_ids = [n["id"] for n in path]
            paths.append((node["id"], path_ids))
        
        traverse_tree(sample_tree, visit_fn)
        
        # Check specific paths
        assert ("root", ["root"]) in paths
        assert ("grandchild1", ["root", "child1", "grandchild1"]) in paths
        assert ("grandchild3", ["root", "child2", "grandchild3"]) in paths
    
    def test_traverse_tree_custom_children_key(self):
        """Test traverse_tree with custom children key."""
        tree = {
            "name": "root",
            "subcatalogs": [
                {"name": "sub1", "subcatalogs": []},
                {"name": "sub2", "subcatalogs": []}
            ]
        }
        
        visited = []
        
        def visit_fn(node, path):
            visited.append(node["name"])
        
        traverse_tree(tree, visit_fn, children_key="subcatalogs")
        
        assert visited == ["root", "sub1", "sub2"]


class TestFindNodes:
    """Test node finding functionality."""
    
    def test_find_nodes_finds_all_matching(self, sample_tree):
        """Test finding all nodes matching a condition."""
        # Find all leaf nodes
        leaf_nodes = find_nodes(
            sample_tree,
            lambda node: node.get("type") == "leaf"
        )
        
        assert len(leaf_nodes) == 2
        assert all(node["type"] == "leaf" for node in leaf_nodes)
        leaf_ids = [node["id"] for node in leaf_nodes]
        assert "grandchild1" in leaf_ids
        assert "grandchild2" in leaf_ids
    
    def test_find_nodes_finds_first_only(self, sample_tree):
        """Test finding only first matching node."""
        # Find first leaf node
        leaf_nodes = find_nodes(
            sample_tree,
            lambda node: node.get("type") == "leaf",
            find_all=False
        )
        
        assert len(leaf_nodes) == 1
        assert leaf_nodes[0]["id"] == "grandchild1"  # First one encountered
    
    def test_find_nodes_with_list_input(self, sample_tree):
        """Test find_nodes with list of root nodes."""
        children = sample_tree["children"]
        
        leaf_nodes = find_nodes(
            children,
            lambda node: node.get("type") == "leaf"
        )
        
        assert len(leaf_nodes) == 2
    
    def test_find_first_node(self, sample_tree):
        """Test find_first_node helper."""
        first_leaf = find_first_node(
            sample_tree,
            lambda node: node.get("type") == "leaf"
        )
        
        assert first_leaf is not None
        assert first_leaf["id"] == "grandchild1"
    
    def test_find_first_node_no_match(self, sample_tree):
        """Test find_first_node when no match found."""
        result = find_first_node(
            sample_tree,
            lambda node: node.get("type") == "nonexistent"
        )
        
        assert result is None
    
    def test_find_node_by_id(self, sample_tree):
        """Test finding node by ID."""
        node = find_node_by_id(sample_tree, "grandchild2")
        
        assert node is not None
        assert node["id"] == "grandchild2"
        assert node["name"] == "Grandchild 2"
    
    def test_find_node_by_id_not_found(self, sample_tree):
        """Test finding non-existent node by ID."""
        node = find_node_by_id(sample_tree, "nonexistent")
        
        assert node is None
    
    def test_find_node_by_id_custom_key(self, sample_tree):
        """Test finding node by custom ID key."""
        node = find_node_by_id(sample_tree, "Child 1", id_key="name")
        
        assert node is not None
        assert node["name"] == "Child 1"


class TestFilterByPath:
    """Test path-based filtering."""

    def test_filter_by_path_nexus_data(self, test_borger: dict, nexus_manager: NexusClientManager):
        visning = nexus_manager.borgere.hent_visning(test_borger)
        assert visning is not None

        referencer = nexus_manager.borgere.hent_referencer(visning)
        assert referencer is not None

        grundforløb = filter_by_path(
            referencer,
            "/ÆHF - Forløbsindplacering (Grundforløb)",
            active_pathways_only=True
        )

        assert len(grundforløb) == 1

        indsatser = filter_by_path(
            referencer,
            "/Sundhedsfagligt grundforløb/FSIII/Indsatser/*",
            active_pathways_only=True
        )

        assert len(indsatser) > 0
    
    def test_filter_by_path_basic(self, pathway_tree):
        """Test basic path filtering."""
        results = filter_by_path(
            [pathway_tree],
            "/Sundhedsfagligt grundforløb/FSIII"
        )
        
        assert len(results) == 1
        assert results[0]["name"] == "FSIII"
    
    def test_filter_by_path_wildcard(self, pathway_tree):
        """Test path filtering with wildcard."""
        results = filter_by_path(
            [pathway_tree],
            "/Sundhedsfagligt grundforløb/*/Medicin%"
        )
        
        assert len(results) == 2
        intervention_names = [r["name"] for r in results]
        assert "Medicin administration" in intervention_names
        assert "Medicin dosering" in intervention_names
    
    def test_filter_by_path_active_pathways_only(self, pathway_tree):
        """Test filtering with active pathways only."""
        # Add inactive pathway
        pathway_tree["children"].append({
            "id": "inactive",
            "name": "Inactive Course",
            "type": "patientPathwayReference",
            "pathwayStatus": "INACTIVE",
            "children": []
        })
        
        results = filter_by_path(
            [pathway_tree],
            "/Sundhedsfagligt grundforløb",
            active_pathways_only=True
        )
        
        assert len(results) == 1
        assert results[0]["name"] == "Sundhedsfagligt grundforløb"
    
    def test_filter_by_path_empty_pattern(self):
        """Test that empty path raises error."""
        with pytest.raises(ValueError, match="Can't match empty path"):
            filter_by_path([], "")


class TestFilterByPredicate:
    """Test predicate-based filtering."""
    
    def test_filter_by_predicate_basic(self, sample_tree):
        """Test basic predicate filtering."""
        leaf_nodes = filter_by_predicate(
            [sample_tree],
            lambda node: node.get("type") == "leaf"
        )
        
        assert len(leaf_nodes) == 2
        assert all(node["type"] == "leaf" for node in leaf_nodes)
    
    def test_filter_by_predicate_complex(self, sample_tree):
        """Test complex predicate filtering."""
        high_value_nodes = filter_by_predicate(
            [sample_tree],
            lambda node: node.get("value", 0) > 15
        )
        
        assert len(high_value_nodes) == 2
        values = [node["value"] for node in high_value_nodes]
        assert 20 in values
        assert 30 in values
    
    def test_filter_by_predicate_custom_children_key(self):
        """Test predicate filtering with custom children key."""
        tree = {
            "name": "root",
            "type": "catalog",
            "subcatalogs": [
                {"name": "grant1", "type": "grant"},
                {"name": "package1", "type": "package"}
            ]
        }
        
        grants = filter_by_predicate(
            [tree],
            lambda node: node.get("type") == "grant",
            children_key="subcatalogs"
        )
        
        assert len(grants) == 1
        assert grants[0]["name"] == "grant1"


class TestMapTree:
    """Test tree transformation."""
    
    def test_map_tree_transforms_nodes(self, sample_tree):
        """Test tree transformation."""
        def add_processed_flag(node):
            new_node = node.copy()
            new_node["processed"] = True
            return new_node
        
        transformed = map_tree(sample_tree, add_processed_flag)
        
        # Original should be unchanged
        assert "processed" not in sample_tree
        
        # Transformed should have flag
        assert transformed["processed"] is True
        
        # Check children are also transformed
        def check_processed(node, path):
            assert node["processed"] is True
        
        traverse_tree(transformed, check_processed)
    
    def test_map_tree_preserves_structure(self, sample_tree):
        """Test that map_tree preserves tree structure."""
        def identity(node):
            return node.copy()
        
        transformed = map_tree(sample_tree, identity)
        
        # Should have same structure
        assert len(transformed["children"]) == len(sample_tree["children"])
        assert len(transformed["children"][0]["children"]) == len(sample_tree["children"][0]["children"])
        
        # But should be different objects
        assert transformed is not sample_tree


class TestGetNodePath:
    """Test path finding functionality."""
    
    def test_get_node_path_finds_correct_path(self, sample_tree):
        """Test finding path to a specific node."""
        target_node = sample_tree["children"][0]["children"][1]  # grandchild2
        
        path = get_node_path(sample_tree, target_node)
        
        assert path is not None
        assert len(path) == 3
        path_ids = [node["id"] for node in path]
        assert path_ids == ["root", "child1", "grandchild2"]
    
    def test_get_node_path_with_custom_compare(self, sample_tree):
        """Test path finding with custom comparison function."""
        def compare_by_id(a, b):
            return a.get("id") == b.get("id")
        
        target = {"id": "grandchild2"}
        
        path = get_node_path(sample_tree, target, compare_fn=compare_by_id)
        
        assert path is not None
        assert len(path) == 3
        path_ids = [node["id"] for node in path]
        assert path_ids == ["root", "child1", "grandchild2"]
    
    def test_get_node_path_not_found(self, sample_tree):
        """Test path finding when node not found."""
        nonexistent_node = {"id": "nonexistent"}
        
        path = get_node_path(sample_tree, nonexistent_node, 
                           compare_fn=lambda a, b: a.get("id") == b.get("id"))
        
        assert path is None


class TestFlattenTree:
    """Test tree flattening functionality."""
    
    def test_flatten_tree_basic(self, sample_tree):
        """Test basic tree flattening."""
        flattened = flatten_tree(sample_tree)
        
        assert len(flattened) == 6  # All nodes
        
        # Should have all nodes
        node_ids = [node["id"] for node in flattened]
        expected_ids = ["root", "child1", "grandchild1", "grandchild2", "child2", "grandchild3"]
        assert node_ids == expected_ids
        
        # Should not have children arrays
        for node in flattened:
            assert "children" not in node
    
    def test_flatten_tree_include_children(self, sample_tree):
        """Test flattening while preserving children arrays."""
        flattened = flatten_tree(sample_tree, include_children_key=True)
        
        assert len(flattened) == 6
        
        # Root and child nodes should have children arrays
        root_node = next(node for node in flattened if node["id"] == "root")
        assert "children" in root_node
        
        # Leaf nodes should have empty children arrays
        leaf_node = next(node for node in flattened if node["id"] == "grandchild1")
        assert "children" not in leaf_node or leaf_node["children"] == []
    
    def test_flatten_tree_custom_children_key(self):
        """Test flattening with custom children key."""
        tree = {
            "name": "root",
            "subcatalogs": [
                {"name": "sub1", "subcatalogs": []},
                {"name": "sub2", "subcatalogs": []}
            ]
        }
        
        flattened = flatten_tree(tree, children_key="subcatalogs")
        
        assert len(flattened) == 3
        names = [node["name"] for node in flattened]
        assert names == ["root", "sub1", "sub2"]


class TestBackwardCompatibility:
    """Test that tree_helpers work with existing patterns."""
    
    def test_works_with_citizens_filter_references_pattern(self, pathway_tree):
        """Test that tree_helpers work with existing filter_references pattern."""
        # This should work exactly like the old filter_references function
        results = filter_by_path(
            [pathway_tree],
            "/Sundhedsfagligt grundforløb/FSIII/Medicin%",
            active_pathways_only=True
        )
        
        assert len(results) == 2
        intervention_names = [r["name"] for r in results]
        assert "Medicin administration" in intervention_names
        assert "Medicin dosering" in intervention_names
    
    def test_works_with_grants_search_pattern(self):
        """Test that tree_helpers work with grants catalog search pattern."""
        catalog = {
            "id": "1",
            "name": "Root Catalog",
            "type": "catalog",
            "subcatalogs": [
                {
                    "id": "2",
                    "name": "Health Services",
                    "type": "catalogGrant",
                    "subcatalogs": []
                },
                {
                    "id": "3", 
                    "name": "Medical Package",
                    "type": "catalogPackage",
                    "subcatalogs": []
                }
            ]
        }
        
        # Find grant by name (like grants.py does)
        grant = find_first_node(
            catalog,
            lambda node: (
                node.get("name") == "Health Services" and 
                node.get("type") in ["catalogGrant", "catalogPackage"]
            ),
            children_key="subcatalogs"
        )
        
        assert grant is not None
        assert grant["name"] == "Health Services"
        assert grant["type"] == "catalogGrant"