"""
Tree traversal and manipulation utilities for hierarchical JSON structures.

This module provides unified utilities for working with tree-like JSON structures
that have children arrays, commonly found in KMD Nexus API responses.
"""

import re
from typing import List, Dict, Any, Callable, Optional, Union


def traverse_tree(
    node: Dict[str, Any],
    visit_fn: Callable[[Dict[str, Any], List[Dict[str, Any]]], None],
    children_key: str = "children",
    path: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Traverse a tree structure and call visit_fn for each node.

    Args:
        node: The current node to visit
        visit_fn: Function to call for each node, receives (node, path)
        children_key: Key name for children array (default: "children")
        path: Current path from root (used internally for recursion)
    """
    if path is None:
        path = []

    # Create a copy of path for this node
    current_path = path + [node]

    # Visit current node
    visit_fn(node, current_path)

    # Recursively visit children
    children = node.get(children_key, [])
    if children:
        for child in children:
            traverse_tree(child, visit_fn, children_key, current_path)


def find_nodes(
    roots: Union[Dict[str, Any], List[Dict[str, Any]]],
    predicate: Callable[[Dict[str, Any]], bool],
    children_key: str = "children",
    find_all: bool = True,
) -> List[Dict[str, Any]]:
    """
    Find nodes in tree structure(s) that match a predicate.

    Args:
        roots: Single node or list of root nodes to search
        predicate: Function that returns True for matching nodes
        children_key: Key name for children array (default: "children")
        find_all: If True, find all matches; if False, stop at first match

    Returns:
        List of matching nodes
    """
    results = []

    # Normalize input to list
    if isinstance(roots, dict):
        root_nodes = [roots]
    else:
        root_nodes = roots

    # Use exception to break out of deep recursion when find_all=False
    class FoundFirstMatch(Exception):
        pass

    def visit_node(node: Dict[str, Any], path: List[Dict[str, Any]]) -> None:
        if predicate(node):
            results.append(node)
            if not find_all:
                raise FoundFirstMatch()

    try:
        for root in root_nodes:
            traverse_tree(root, visit_node, children_key)
            if not find_all and results:
                break
    except FoundFirstMatch:
        pass

    return results


def find_first_node(
    roots: Union[Dict[str, Any], List[Dict[str, Any]]],
    predicate: Callable[[Dict[str, Any]], bool],
    children_key: str = "children",
) -> Optional[Dict[str, Any]]:
    """
    Find the first node that matches a predicate.

    Args:
        roots: Single node or list of root nodes to search
        predicate: Function that returns True for matching nodes
        children_key: Key name for children array (default: "children")

    Returns:
        First matching node or None if no match found
    """
    results = find_nodes(roots, predicate, children_key, find_all=False)
    return results[0] if results else None


def find_node_by_id(
    roots: Union[Dict[str, Any], List[Dict[str, Any]]],
    node_id: str,
    id_key: str = "id",
    children_key: str = "children",
) -> Optional[Dict[str, Any]]:
    """
    Find a node by its ID.

    Args:
        roots: Single node or list of root nodes to search
        node_id: The ID to search for
        id_key: Key name for the ID field (default: "id")
        children_key: Key name for children array (default: "children")

    Returns:
        Matching node or None if not found
    """
    return find_first_node(
        roots, lambda node: node.get(id_key) == node_id, children_key
    )


def filter_by_path(
    roots: List[Dict[str, Any]],
    path_pattern: str,
    active_pathways_only: bool = False,
    children_key: str = "children",
) -> List[Dict[str, Any]]:
    """
    Filter nodes by path pattern with wildcard support.

    This function replicates the behavior of the original filter_references
    function from citizens.py.

    Args:
        roots: List of root nodes to search
        path_pattern: Path pattern like "/parent/child/*" or "/parent/child/name%"
        active_pathways_only: If True, skip inactive pathways
        children_key: Key name for children array (default: "children")

    Returns:
        List of nodes matching the path pattern
    """
    # Parse path pattern
    path_segments = re.findall(r"/([^/]+)", path_pattern)

    if not path_segments:
        raise ValueError("Can't match empty path")

    results = []

    for root in roots:
        results.extend(
            _filter_tree_by_path(
                root, [], path_segments, active_pathways_only, children_key
            )
        )

    return results


def _filter_tree_by_path(
    node: Dict[str, Any],
    current_path: List[Dict[str, Any]],
    target_path: List[str],
    active_pathways_only: bool,
    children_key: str,
) -> List[Dict[str, Any]]:
    """
    Internal recursive function for path-based filtering.
    """
    result = []

    # Check for inactive pathways if filtering is enabled
    if (
        active_pathways_only
        and node.get("type") == "patientPathwayReference"
        and node.get("pathwayStatus") != "ACTIVE"
    ):
        return result

    # Add current node to path
    current_path = current_path + [node]

    # Check if current path matches target path
    if _path_matches(current_path, target_path):
        result.append(node)
    else:
        # Continue searching in children if we haven't exceeded target depth
        children = node.get(children_key, [])
        if children and len(target_path) > len(current_path):
            for child in children:
                result.extend(
                    _filter_tree_by_path(
                        child,
                        current_path,
                        target_path,
                        active_pathways_only,
                        children_key,
                    )
                )

    return result


def _path_matches(current_path: List[Dict[str, Any]], target_path: List[str]) -> bool:
    """
    Check if current path matches target path pattern.

    Supports wildcards:
    - "*" matches any single segment
    - "%" as suffix matches any string starting with prefix
    """
    if len(current_path) != len(target_path):
        return False

    for i, (node, pattern) in enumerate(zip(current_path, target_path)):
        # Wildcard matches anything
        if pattern == "*":
            continue

        # Get node name or type for matching
        node_name = node.get("name", "")
        node_type = node.get("type", "")

        # Check for prefix match (pattern ends with %)
        if pattern.endswith("%"):
            prefix = pattern[:-1]
            name_match = node_name.startswith(prefix)
            type_match = node_type.startswith(prefix)
        else:
            # Exact match with regex support - escape special chars then handle % wildcards
            escaped_pattern = re.escape(pattern).replace(r"\%", ".*")
            name_match = re.fullmatch(escaped_pattern, node_name) is not None
            type_match = re.fullmatch(escaped_pattern, node_type) is not None

        if not (name_match or type_match):
            return False

    return True


def filter_by_predicate(
    roots: List[Dict[str, Any]],
    predicate: Callable[[Dict[str, Any]], bool],
    children_key: str = "children",
) -> List[Dict[str, Any]]:
    """
    Filter nodes recursively using a predicate function.

    This function replicates the behavior of filter_pathway_references
    from citizens.py.

    Args:
        roots: List of root nodes to search
        predicate: Function that returns True for nodes to include
        children_key: Key name for children array (default: "children")

    Returns:
        List of nodes that match the predicate
    """
    result = []

    for node in roots:
        # Check current node
        if predicate(node):
            result.append(node)

        # Recursively check children
        children = node.get(children_key, [])
        if children:
            result.extend(filter_by_predicate(children, predicate, children_key))

    return result


def map_tree(
    node: Dict[str, Any],
    transform_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    children_key: str = "children",
) -> Dict[str, Any]:
    """
    Transform a tree by applying a function to each node.

    Args:
        node: Root node to transform
        transform_fn: Function to transform each node
        children_key: Key name for children array (default: "children")

    Returns:
        New tree with transformed nodes
    """
    # Transform current node
    transformed = transform_fn(node.copy())

    # Recursively transform children
    children = node.get(children_key, [])
    if children:
        transformed[children_key] = [
            map_tree(child, transform_fn, children_key) for child in children
        ]

    return transformed


def get_node_path(
    roots: Union[Dict[str, Any], List[Dict[str, Any]]],
    target_node: Dict[str, Any],
    children_key: str = "children",
    compare_fn: Optional[Callable[[Dict[str, Any], Dict[str, Any]], bool]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    Get the path from root to a target node.

    Args:
        roots: Single node or list of root nodes to search
        target_node: Node to find path to
        children_key: Key name for children array (default: "children")
        compare_fn: Custom comparison function (default: object identity)

    Returns:
        List representing path from root to target, or None if not found
    """
    if compare_fn is None:

        def default_compare_fn(a, b):
            return a is b

        compare_fn = default_compare_fn

    found_path = None

    def visit_node(node: Dict[str, Any], path: List[Dict[str, Any]]) -> None:
        nonlocal found_path
        if found_path is None and compare_fn(node, target_node):
            found_path = path.copy()

    # Normalize input to list
    if isinstance(roots, dict):
        root_nodes = [roots]
    else:
        root_nodes = roots

    for root in root_nodes:
        traverse_tree(root, visit_node, children_key)
        if found_path:
            break

    return found_path


def flatten_tree(
    node: Dict[str, Any],
    children_key: str = "children",
    include_children_key: bool = False,
) -> List[Dict[str, Any]]:
    """
    Flatten a tree structure into a list of all nodes.

    Args:
        node: Root node to flatten
        children_key: Key name for children array (default: "children")
        include_children_key: Whether to preserve children arrays in result

    Returns:
        Flat list of all nodes in the tree
    """
    nodes = []

    def visit_node(current_node: Dict[str, Any], path: List[Dict[str, Any]]) -> None:
        if include_children_key:
            nodes.append(current_node)
        else:
            # Create copy without children key
            node_copy = {k: v for k, v in current_node.items() if k != children_key}
            nodes.append(node_copy)

    traverse_tree(node, visit_node, children_key)
    return nodes
