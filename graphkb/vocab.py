from typing import List, cast, Iterable, Set

from . import GraphKBConnection
from .types import Ontology
from .util import convert_to_rid_list


def get_equivalent_terms(
    conn: GraphKBConnection,
    base_term_name: str,
    root_exclude_term: str = '',
    ontology_class: str = 'Vocabulary',
    ignore_cache: bool = False,
) -> List[Ontology]:
    """
    Get a list of terms equivalent to the current term up to the root term

    Args:
        base_term_name: the name to get superclasses of
        root_exclude_term: the parent term to exlcude along with all of its parent terms
    """
    base_term_parents = cast(
        List[Ontology],
        conn.query(
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
            ignore_cache=ignore_cache,
        ),
    )
    if root_exclude_term:
        exclude = set(
            convert_to_rid_list(
                conn.query(
                    {
                        'target': {
                            'target': ontology_class,
                            'queryType': 'descendants',
                            'filters': {'name': root_exclude_term},
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
                    ignore_cache=ignore_cache,
                )
            )
        )
        return [term for term in base_term_parents if term['@rid'] not in exclude]
    return base_term_parents


def get_term_tree(
    conn: GraphKBConnection,
    base_term_name: str,
    root_exclude_term: str = '',
    ontology_class: str = 'Vocabulary',
    include_superclasses: bool = True,
    ignore_cache: bool = False,
) -> List[Ontology]:
    """
    Get terms equivalent to the base term by traversing the subclassOf tree and expanding related
    alias and cross reference edges

    Args:
        conn: the graphkb connection object
        base_term_name: the term to use as the base of the subclass tree
        ontology_class: the default class to query. Defaults to 'Vocabulary'
        include_superclasses: when True the query will include superclasses of the current term

    Returns:
        GraphKB records

    Note: this must be done in 2 calls to avoid going up and down the tree in a single query (exclude adjacent siblings)
    """
    # get all child terms of the subclass tree and disambiguate them
    child_terms = cast(
        List[Ontology],
        conn.query(
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
            ignore_cache=ignore_cache,
        ),
    )
    # get all parent terms of the subclass tree and disambiguate them
    if include_superclasses:
        parent_terms = get_equivalent_terms(
            conn,
            base_term_name,
            root_exclude_term=root_exclude_term,
            ontology_class=ontology_class,
            ignore_cache=ignore_cache,
        )
    else:
        parent_terms = []

    terms = {}
    # merge the two lists
    for term in child_terms + parent_terms:
        terms[term['@rid']] = term

    return list(terms.values())


def get_term_by_name(
    conn: GraphKBConnection,
    name: str,
    ontology_class: str = 'Vocabulary',
    ignore_cache: bool = False,
    **kwargs,
) -> Ontology:
    """
    Retrieve a vocaulary term by name

    Args:
        conn: the graphkb connection object
        name: the name of the Vocabulary term to retrieve

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
            'returnProperties': [
                'sourceId',
                'sourceIdVersion',
                'deprecated',
                'name',
                '@rid',
                '@class',
            ],
        },
        ignore_cache=ignore_cache,
        **kwargs,
    )

    if len(result) != 1:
        raise AssertionError(f'unable to find term ({name}) by name')
    return cast(Ontology, result[0])


def get_terms_set(
    graphkb_conn: GraphKBConnection, base_terms: Iterable[str], ignore_cache: bool = False
) -> Set[str]:
    """
    Get a set of terms of vocabulary given some base/parent term names. Returns the record
    IDs for the resulting terms
    """
    cache_key = tuple(sorted(base_terms))
    if graphkb_conn.cache.get(cache_key, None) and not ignore_cache:
        return graphkb_conn.cache[cache_key]
    terms = set()
    for base_term in base_terms:
        terms.update(
            convert_to_rid_list(
                get_term_tree(
                    graphkb_conn, base_term, include_superclasses=False, ignore_cache=ignore_cache
                )
            )
        )
    if not ignore_cache:
        graphkb_conn.cache[cache_key] = terms
    return terms
