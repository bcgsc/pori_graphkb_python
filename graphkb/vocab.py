BASE_EXPRESSION = 'expression variant'
BASE_INCREASED_EXPRESSION = 'increased expression'
BASE_REDUCED_EXPRESSION = 'reduced expression'


def get_term_tree(conn, base_term_name, **kwargs):
    return conn.query(
        {
            'target': 'Vocabulary',
            'queryType': 'ancestors',
            'filters': {'name': base_term_name},
            'returnProperties': ['sourceId', 'sourceIdVersion', 'deprecated', 'name', '@rid'],
        },
        ignore_cache=False,
        **kwargs,
    )


def get_term_by_name(conn, name, **kwargs):
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
