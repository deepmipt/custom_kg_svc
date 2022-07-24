from typing import Optional
import logging
from treelib import Tree
from treelib.exceptions import NodeIDAbsentError, DuplicatedNodeIdError

from deeppavlov_kg.utils import loader


class Entity(object):
    """A class to represent an entity. It's used as argument for treelib node data"""
    def __init__(self, properties: set):
        """
        Args:
          properties: the state properties an entity has or could have in future
        """
        self.properties = properties


def create_kind(
    kind: str,
    parent: str = "Kind",
    start_tree: Optional[Tree] = None,
    kind_properties: Optional[set] = None,
) -> Tree:
    """Adds a given kind to the ontology_graph tree.

    Args:
      kind: kind to be added
      parent: parent of kind
      start_tree: treelib.Tree object, to which the new kind should be added
      kind_properties: A set of properties for the created kind

    Returns:
      tree object representing the ontology graph after the kind creation

    """
    if kind_properties is None:
        kind_properties = set()
    kind = kind.capitalize()
    parent = parent.capitalize()

    if start_tree is None:
        start_tree = loader.load_ontology_graph()
        if start_tree is None:
            start_tree = Tree()
            start_tree.create_node(
                tag="Kind",
                identifier="Kind",
                data=Entity(set()),
            )
    tree = start_tree

    parent_node = tree.get_node(parent)
    if parent_node is None:
        tree = create_kind(parent, "Kind", tree)
        parent_node = tree.get_node(parent)
        logging.warning("Not-in-database kind '%s'. Has been added as a child of 'Kind'", parent)

    kind_properties.update(parent_node.data.properties) # type: ignore

    try:
        tree.create_node(
            tag=kind,
            identifier=kind,
            parent=parent,
            data=Entity(kind_properties),
        )
        loader.save_ontology_graph(tree)
    except DuplicatedNodeIdError:
        logging.info(
            "The '%s' kind exists in database. No new kind has been created", kind
        )

    return tree


def get_kind_node(tree: Tree, kind: str):
    """Searches tree for kind and returns the kind node

    Returns:
      kind node in case of success, None otherwise
    """
    if tree is None:
        logging.error("Ontology graph is empty")
        return None

    kind_node = tree.get_node(kind)
    if kind_node is None:
        logging.error("Kind '%s' is not in ontology graph", kind)
        return None
    return kind_node


def remove_kind(kind: str):
    """Removes kind from database/ontology_graph"""
    tree = loader.load_ontology_graph()
    if get_kind_node(tree, kind) is None:
        return None

    tree.remove_node(kind)

    loader.save_ontology_graph(tree)
    logging.info("Kind '%s' has been removed successfully from ontology graph", kind)


def update_properties_of_kind(kind: str, old_properties: list, new_properties: list):
    """Updates a list of properties of a given kind

    Returns:
      kind node in case of success, None otherwise
    """
    tree = loader.load_ontology_graph()
    kind_node = get_kind_node(tree, kind)
    if kind_node is None:
        return None

    for idx, prop in enumerate(old_properties):
        if prop in kind_node.data.properties:
            kind_node.data.properties.remove(prop)
            kind_node.data.properties.add(new_properties[idx])
        else:
            logging.error("Property '%s' is not in '%s' properties", prop, kind)
            return None

    loader.save_ontology_graph(tree)
    logging.info("Properties has been updated successfully")


def get_descendant_kinds(kind: str) -> list:
    """Returns the children kinds of a given kind."""
    tree = loader.load_ontology_graph()
    descendants = []
    if tree:
        try:
            descendants = [descendant.tag for descendant in tree.children(kind)]
        except NodeIDAbsentError:
            logging.error("Kind '%s' is not in ontology graph", kind)
            return None
    return descendants


def get_kind_properties(kind: str) -> Optional[set]:
    """Returns the kind properties, stored in ontology graph"""
    tree = loader.load_ontology_graph()
    kind_node = get_kind_node(tree, kind)
    if kind_node is not None:
        return kind_node.data.properties
    return None


def are_properties_in_kind(list_of_property_kinds, kind):
    """Checks if all the properties in the list are in fact properties of 'kind' in 
    the ontology graph.
    """
    kind_properties = get_kind_properties(kind)
    for prop in list_of_property_kinds:
        if prop not in kind_properties:
            logging.error("""The property '%s' isn't in '%s' properties in ontology graph.
                Use create_or_update_properties_of_kind() function to add it""", prop, kind)
            return False
    return True
