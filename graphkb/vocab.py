BASE_EXPRESSION = 'expression variant'
BASE_INCREASED_EXPRESSION = 'increased expression'
BASE_REDUCED_EXPRESSION = 'reduced expression'


def get_term_tree(conn, base_term_name, **kwargs):
    """
    Args:
        conn (GraphKBConnection): the graphkb connection object
        base_term_name (str): the term to use as the base of the subclass tree

    Returns:
        List.<dict>: Vocabulary records

    Note: this must be done in 2 calls to avoid going up and down the tree in a single query (exclude adjacent siblings)
    """
    # get all child terms of the subclass tree and disambiguate them
    child_terms = conn.query(
        {
            'target': {
                'target': 'Vocabulary',
                'queryType': 'ancestors',
                'filters': {'name': base_term_name},
            },
            'queryType': 'similarTo',
            'treeEdges': [],
            'returnProperties': ['sourceId', 'sourceIdVersion', 'deprecated', 'name', '@rid'],
        },
        ignore_cache=False,
        **kwargs,
    )
    # get all parent terms of the subclass tree and disambiguate them
    parent_terms = conn.query(
        {
            'target': {
                'target': 'Vocabulary',
                'queryType': 'descendants',
                'filters': {'name': base_term_name},
            },
            'queryType': 'similarTo',
            'treeEdges': [],
            'returnProperties': ['sourceId', 'sourceIdVersion', 'deprecated', 'name', '@rid'],
        },
        ignore_cache=False,
        **kwargs,
    )
    terms = {}
    # merge the two lists
    for term in child_terms + parent_terms:
        terms[term['@rid']] = term

    return list(terms.values())


def get_term_by_name(conn, name, **kwargs):
    """
    Args:
        conn (GraphKBConnection): the graphkb connection object
        name (str): the name of the Vocabulary term to retrieve

    Raises:
        AssertionError: more than one term or no terms with that name were found

    Returns:
        List.<dict>: Vocabulary records
    """
    result = conn.query(
        {
            'target': 'Vocabulary',
            'filters': {'name': name},
            'returnProperties': ['sourceId', 'sourceIdVersion', 'deprecated', 'name', '@rid'],
        },
        ignore_cache=False,
        **kwargs,
    )

    if len(result) != 1:
        raise AssertionError(f'unable to find term ({name}) by name')
    return result[0]
