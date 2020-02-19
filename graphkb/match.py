"""
Functions which return Variants from GraphKB which match some input variant definition
"""
from .util import IterableNamespace, convert_to_rid_list
from .constants import GENERIC_RETURN_PROPERTIES
from .genes import GENE_RETURN_PROPERTIES
from .vocab import get_term_tree

INPUT_COPY_CATEGORIES = IterableNamespace(
    AMP='amplification',
    ANY_GAIN='copy gain',
    ANY_LOSS='copy loss',
    DEEP='deep deletion',
    GAIN='low level copy gain',
    LOSS='shallow deletion',
)
INPUT_EXPRESSION_CATEGORIES = IterableNamespace(
    UP='increased expression', DOWN='reduced expression'
)
AMBIGUOUS_AA = ['x', '?', 'X']


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
    features = convert_to_rid_list(get_equivalent_features(conn, gene_name))

    if not features:
        raise ValueError(f'unable to find the gene ({gene_name}) or any equivalent representations')

    # get the list of terms that we should match
    terms = convert_to_rid_list(get_term_tree(conn, category))

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
                    {'type': terms, 'operator': 'IN'},
                ],
            },
            'queryType': 'similarTo',
            'returnProperties': return_properties,
        }
    )


def match_copy_variant(conn, gene_name, category, drop_homozygous=False):
    """
    Returns a list of variants matching the input variant

    Args:
        conn (GraphKBConnection): the graphkb connection object
        gene_name (str): the name of the gene the variant is in reference to
        category (str): the variant category (ex. copy loss)
        drop_homozygous (bool): Drop homozygous matches from the result when true

    Raises:
        ValueError: The input copy category is not recognized

    Returns:
        Array.<dict>: List of variant records from GraphKB which match the input
    """
    if category not in INPUT_COPY_CATEGORIES.values():
        raise ValueError(f'not a valid copy variant input category ({category})')

    result = match_category_variant(conn, gene_name, category)

    if drop_homozygous:
        return [row for row in result if row['zygosity'] != 'homozygous']
    return result


def match_expression_variant(conn, gene_name, category):
    if category not in INPUT_EXPRESSION_CATEGORIES.values():
        raise ValueError(f'not a valid expression variant input category ({category})')

    return match_category_variant(conn, gene_name, category)


def positions_overlap(pos_record, range_start, range_end=None):
    """
    Check if 2 Position records from GraphKB indicate an overlap

    Note:
        null values indicate not-specified or any

    Args:
        pos_record (dict): the record to compare
        range_start (dict): the position record indicating the start of an uncertainty range
        range_end (dict, optional): the position record indicating the end of an uncertainty range

    Raises:
        NotImplementedError: if a cytoband type position is given

    Returns:
        bool: True if the positions overlap
    """
    if pos_record.get('@class', '') == 'CytobandPosition':
        raise NotImplementedError(
            'Position comparison for cytoband coordinates is not yet implemented'
        )
    pos = pos_record.get('pos', None)
    if pos is None:
        return True

    start = range_start.get('pos', None)

    if range_end:
        end = range_end.get('pos', None)

        if start is not None and pos < start:
            return False
        if end is not None and pos > end:
            return False
        return True
    return start is None or pos == start


def compare_positional_variants(variant, reference_variant):
    """
    Compare 2 variant records from GraphKB to determine if they are equivalent

    Args:
        variant (dict): the input variant
        reference_variant (dict): the reference (matched) variant record

    Returns:
        bool: True if the records are equivalent
    """
    if not positions_overlap(
        variant['break1Start'],
        reference_variant['break1Start'],
        reference_variant.get('break1End', None),
    ):
        return False

    if 'break2Start' in variant:
        if 'break2Start' not in reference_variant:
            return False
        if not positions_overlap(
            variant['break2Start'],
            reference_variant['break2Start'],
            reference_variant.get('break2End', None),
        ):
            return False

    if (
        variant.get('untemplatedSeq', None) is not None
        and reference_variant.get('untemplatedSeq', None) is not None
    ):
        if (
            variant.get('untemplatedSeqSize', None) is not None
            and reference_variant.get('untemplatedSeqSize', None) is not None
        ):
            if variant['untemplatedSeqSize'] != reference_variant['untemplatedSeqSize']:
                return False
        if (
            reference_variant['untemplatedSeq'] not in AMBIGUOUS_AA
            and variant['untemplatedSeq'] not in AMBIGUOUS_AA
        ):
            if reference_variant['untemplatedSeq'].lower() != variant['untemplatedSeq'].lower():
                return False
        elif len(variant['untemplatedSeq']) != len(reference_variant['untemplatedSeq']):
            return False

    if (
        variant.get('refSeq', None) is not None
        and reference_variant.get('refSeq', None) is not None
    ):
        if (
            reference_variant['refSeq'] not in AMBIGUOUS_AA
            and variant['refSeq'] not in AMBIGUOUS_AA
        ):
            if reference_variant['refSeq'].lower() != variant['refSeq'].lower():
                return False
        elif len(variant['refSeq']) != len(reference_variant['refSeq']):
            return False

    return True


def match_positional_variant(conn, variant_string):
    # parse the representation
    parsed = conn.parse(variant_string)

    if 'break1End' in parsed or 'break2End' in parsed:  # uncertain position
        raise NotImplementedError(
            f'Matching does not support uncertain positions ({variant_string}) as input'
        )
    # disambiguate the gene name
    gene1 = parsed['reference1']
    features = convert_to_rid_list(get_equivalent_features(conn, parsed['reference1']))

    if not features:
        raise ValueError(f'unable to find the gene ({gene1}) or any equivalent representations')

    secondary_features = None
    if 'reference2' in parsed:
        gene2 = parsed['reference2']
        secondary_features = convert_to_rid_list(get_equivalent_features(conn, gene2))

        if not secondary_features:
            raise ValueError(f'unable to find the gene ({gene2}) or any equivalent representations')
    # disambiguate the variant type
    types = convert_to_rid_list(get_term_tree(conn, parsed['type']))

    if not types:
        variant_type = parsed['type']
        raise ValueError(f'unable to find the term/category ({variant_type}) or any equivalent')

    # match the existing mutations (positional)
    query_filters = [
        {'reference1': features},
        {'reference2': secondary_features},
        {'type': types},
        {'break1Start.@class': parsed['break1Start']['@class']},
    ]

    filtered = []

    for row in conn.query(
        {'target': 'PositionalVariant', 'filters': query_filters}, ignore_cache=False
    ):
        if compare_positional_variants(parsed, row):
            filtered.append(row)

    # post filter matches
    matches = []
    if filtered:
        matches = conn.query(
            {
                'target': convert_to_rid_list(filtered),
                'queryType': 'similarTo',
                'edges': ['AliasOf', 'DeprecatedBy', 'CrossReferenceOf'],
                'treeEdges': ['Infers'],
            }
        )

    cat_matches = conn.query(
        {
            'target': {
                'target': 'CategoryVariant',
                'filters': [
                    {'reference1': features},
                    {'type': types},
                    {'reference2': secondary_features},
                ],
            },
            'queryType': 'similarTo',
            'edges': ['AliasOf', 'DeprecatedBy', 'CrossReferenceOf'],
            'treeEdges': [],
        },
        ignore_cache=False,
    )
    result = {}
    for row in matches + cat_matches:
        result[row['@rid']] = row

    return list(result.values())
