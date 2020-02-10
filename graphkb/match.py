from .util import IterableNamespace
from .constants import GENERIC_RETURN_PROPERTIES
from .genes import GENE_RETURN_PROPERTIES
from .vocab import get_term_tree

INPUT_COPY_CATEGORIES = IterableNamespace(AMP='amplification', GAIN='copy gain', LOSS='copy loss')
INPUT_EXPRESSION_CATEGORIES = IterableNamespace(
    UP='increased expression', DOWN='reduced expression'
)


def get_equivalent_features(conn, gene_name):
    return conn.query(
        {'target': {'target': 'Feature', 'filters': {'name': gene_name}}, 'queryType': 'similarTo'},
        ignore_cache=False,
    )


def match_category_variant(conn, gene_name, category):
    """
    Returns a list of variants matching the input variant

    Args:
        conn (GraphKBConnection): the graphkb connection object
        gene_name (str): the name of the gene the variant is in reference to
        category (str): the variant category (ex. copy loss)

    Raises:
        ValueError: The gene could not be found in GraphKB

    Returns:
        Array.<dict>: List of variant records from GraphKB which match the input
    """
    # disambiguate the gene to find all equivalent representations
    features = [record['@rid'] for record in get_equivalent_features(conn, gene_name)]

    if not features:
        raise ValueError(f'unable to find the gene ({gene_name}) or any equivalent representations')

    # get the list of terms that we should match
    terms = get_term_tree(conn, category)

    if not terms:
        raise ValueError(f'unable to find the term/category ({category}) or any equivalent')

    return_properties = (
        [f'type.{p}' for p in GENERIC_RETURN_PROPERTIES]
        + [f'reference1.{p}' for p in GENE_RETURN_PROPERTIES]
        + ['reference2', 'zygosity', 'germline', 'displayName']
    )
    # find the variant list
    return conn.query(
        {
            'target': {
                'target': 'CategoryVariant',
                'filters': [
                    {'reference1': features, 'operator': 'IN'},
                    {'type': get_term_tree(conn, category), 'operator': 'IN'},
                ],
            },
            'queryType': 'similarTo',
            'returnProperties': return_properties,
        }
    )


def match_copy_variant(conn, gene_name, category):
    """
    Returns a list of variants matching the input variant

    Args:
        conn (GraphKBConnection): the graphkb connection object
        gene_name (str): the name of the gene the variant is in reference to
        category (str): the variant category (ex. copy loss)

    Raises:
        ValueError: The input copy category is not recognized

    Returns:
        Array.<dict>: List of variant records from GraphKB which match the input
    """
    if category not in INPUT_COPY_CATEGORIES.values():
        raise ValueError(f'not a valid copy variant input category ({category})')

    return match_category_variant(conn, gene_name, category)


def match_expression_variant(conn, gene_name, category):
    if category not in INPUT_EXPRESSION_CATEGORIES.values():
        raise ValueError(f'not a valid expression variant input category ({category})')

    return match_category_variant(conn, gene_name, category)


def match_hgvs_mutation(conn, hgvs_string):
    # parse the representation
    # disambiguate the gene name
    # disambiguate the variant type
    # match the existing mutations (positional)
    # match the existing category mutations
    raise NotImplementedError('TODO')


def match_structural_variant(conn, fusion_string):
    raise NotImplementedError('TODO')
