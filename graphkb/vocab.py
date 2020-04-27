from typing import List, Dict

from . import GraphKBConnection
from .util import convert_to_rid_list


def get_equivalent_terms(
    conn: GraphKBConnection, base_term_name: str, root_term: str, ontology_class: str = 'Vocabulary'
) -> List[Dict]:
    """
    Get a list of terms equivalent to the current term up to the root term

    Args:
        base_term_name: the name to get superclasses of
        root_term: the parent term to stop at
    """
    base_term_parents = conn.query(
        {
            'target': {
                'target': ontology_class,
                'queryType': 'descendants',
                'filters': {'name': base_term_name},
            },
            'queryType': 'similarTo',
            'treeEdges': [],
            'returnProperties': ['sourceId', 'sourceIdVersion', 'deprecated', 'name', '@rid'],
        },
        ignore_cache=False,
    )
    if root_term:
        exclude = set(
            convert_to_rid_list(
                conn.query(
                    {
                        'target': {
                            'target': ontology_class,
                            'queryType': 'descendants',
                            'filters': {'name': root_term},
                        },
                        'queryType': 'similarTo',
                        'treeEdges': [],
                        'returnProperties': [
                            'sourceId',
                            'sourceIdVersion',
                            'deprecated',
                            'name',
                            '@rid',
                        ],
                    },
                    ignore_cache=False,
                )
            )
        )
        return [
            term
            for term in base_term_parents
            if term['@rid'] not in exclude or term['name'] == root_term
        ]
    return base_term_parents


def get_term_tree(
    conn: GraphKBConnection,
    base_term_name: str,
    root_term: str,
    ontology_class: str = 'Vocabulary',
    include_superclasses: bool = True,
) -> List[Dict]:
    """
    Get terms equivalent to the base term by traversing the subclassOf tree and expanding related
    alias and cross reference edges

    Args:
        conn (GraphKBConnection): the graphkb connection object
        base_term_name (str): the term to use as the base of the subclass tree
        ontology_class (str): the default class to query. Defaults to 'Vocabulary'
        include_superclasses (bool): when True the query will include superclasses of the current term

    Returns:
        List.<dict>: GraphKB records

    Note: this must be done in 2 calls to avoid going up and down the tree in a single query (exclude adjacent siblings)
    """
    # get all child terms of the subclass tree and disambiguate them
    child_terms = conn.query(
        {
            'target': {
                'target': ontology_class,
                'queryType': 'ancestors',
                'filters': {'name': base_term_name},
            },
            'queryType': 'similarTo',
            'treeEdges': [],
            'returnProperties': ['sourceId', 'sourceIdVersion', 'deprecated', 'name', '@rid'],
        },
        ignore_cache=False,
    )
    # get all parent terms of the subclass tree and disambiguate them
    if include_superclasses:
        parent_terms = get_equivalent_terms(
            conn, base_term_name, root_term=root_term, ontology_class=ontology_class
        )
    else:
        parent_terms = []

    terms = {}
    # merge the two lists
    for term in child_terms + parent_terms:
        terms[term['@rid']] = term

    return list(terms.values())


def get_term_by_name(
    conn: GraphKBConnection, name: str, ontology_class: str = 'Vocabulary', **kwargs
) -> Dict:
    """
    Retrieve a vocaulary term by name

    Args:
        conn (GraphKBConnection): the graphkb connection object
        name (str): the name of the Vocabulary term to retrieve

    Raises:
        AssertionError: more than one term or no terms with that name were found

    Returns:
        Dict: Vocabulary record

    Raises:
        AssertionError: if the term was not found or more than 1 match was found (expected to be unique)
    """
    result = conn.query(
        {
            'target': ontology_class,
            'filters': {'name': name},
            'returnProperties': ['sourceId', 'sourceIdVersion', 'deprecated', 'name', '@rid'],
        },
        ignore_cache=False,
        **kwargs,
    )

    if len(result) != 1:
        raise AssertionError(f'unable to find term ({name}) by name')
    return result[0]
