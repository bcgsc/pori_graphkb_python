"""
Functions which return Variants from GraphKB which match some input variant definition
"""
from typing import List, Dict

from .util import IterableNamespace, convert_to_rid_list, FeatureNotFoundError
from .constants import GENERIC_RETURN_PROPERTIES, BASE_RETURN_PROPERTIES
from .genes import GENE_RETURN_PROPERTIES
from .vocab import get_term_tree
from . import GraphKBConnection

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


GENE_NAME_CACHE = set()


def get_equivalent_features(
    conn: GraphKBConnection, gene_name: str, ignore_cache: bool = False
) -> List[Dict]:
    """
    Args:
        gene_name: the gene name to search features by
        ignore_cache (bool, optional): bypass the cache to always force a new request

    Returns:
        equivalent feature records
    """
    if GENE_NAME_CACHE and gene_name.lower() not in GENE_NAME_CACHE and not ignore_cache:
        return []
    return conn.query(
        {'target': {'target': 'Feature', 'filters': {'name': gene_name}}, 'queryType': 'similarTo'},
        ignore_cache=False,
    )


def cache_gene_names(conn: GraphKBConnection) -> List[Dict]:
    genes = conn.query(
        {
            'target': 'Feature',
            'filters': {'biotype': 'gene'},
            'returnProperties': ['name'],
            'neighbors': 0,
        }
    )
    for gene in genes:
        if gene['name']:
            GENE_NAME_CACHE.add(gene['name'].lower())


def match_category_variant(
    conn: GraphKBConnection, gene_name: str, category: str, root_term: str = ''
) -> List[Dict]:
    """
    Returns a list of variants matching the input variant

    Args:
        conn (GraphKBConnection): the graphkb connection object
        gene_name (str): the name of the gene the variant is in reference to
        category (str): the variant category (ex. copy loss)

    Raises:
        FeatureNotFoundError: The gene could not be found in GraphKB

    Returns:
        Array.<dict>: List of variant records from GraphKB which match the input
    """
    # disambiguate the gene to find all equivalent representations
    features = convert_to_rid_list(get_equivalent_features(conn, gene_name))

    if not features:
        raise FeatureNotFoundError(
            f'unable to find the gene ({gene_name}) or any equivalent representations'
        )

    # get the list of terms that we should match
    terms = convert_to_rid_list(get_term_tree(conn, category, root_term))

    if not terms:
        raise ValueError(f'unable to find the term/category ({category}) or any equivalent')

    return_properties = (
        BASE_RETURN_PROPERTIES
        + [f'type.{p}' for p in GENERIC_RETURN_PROPERTIES]
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


def match_copy_variant(
    conn: GraphKBConnection, gene_name: str, category: str, drop_homozygous: bool = False
) -> List[Dict]:
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

    result = match_category_variant(conn, gene_name, category, root_term='copy variant')

    if drop_homozygous:
        return [row for row in result if row['zygosity'] != 'homozygous']
    return result


def match_expression_variant(conn: GraphKBConnection, gene_name: str, category: str) -> List[Dict]:
    if category not in INPUT_EXPRESSION_CATEGORIES.values():
        raise ValueError(f'not a valid expression variant input category ({category})')

    return match_category_variant(conn, gene_name, category, root_term='expression variant')


def positions_overlap(pos_record: Dict, range_start: Dict, range_end: Dict = None) -> bool:
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


def compare_positional_variants(variant: Dict, reference_variant: Dict) -> bool:
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


def match_positional_variant(conn: GraphKBConnection, variant_string: str) -> List[Dict]:
    """
    Given the HGVS+ representation of some positional variant, parse it and match it to
    annotations in GraphKB

    Args:
        variant_string: the HGVS+ annotation string

    Raises:
        NotImplementedError: thrown for uncertain position input (ranges)
        FeatureNotFoundError: One of the genes does not exist in GraphKB

    Returns:
        A list of matched statement records
    """
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
        raise FeatureNotFoundError(
            f'unable to find the gene ({gene1}) or any equivalent representations'
        )

    secondary_features = None
    if parsed.get('reference2', '?') != '?':
        gene2 = parsed['reference2']
        secondary_features = convert_to_rid_list(get_equivalent_features(conn, gene2))

        if not secondary_features:
            raise FeatureNotFoundError(
                f'unable to find the gene ({gene2}) or any equivalent representations'
            )
    # disambiguate the variant type
    types = convert_to_rid_list(
        get_term_tree(
            conn, parsed['type'], root_term='structural variant' if secondary_features else ''
        )
    )

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
