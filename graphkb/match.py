"""
Functions which return Variants from GraphKB which match some input variant definition
"""
from typing import Dict, List, Optional, Set, Union, cast

from . import GraphKBConnection
from .constants import BASE_RETURN_PROPERTIES, GENERIC_RETURN_PROPERTIES
from .genes import GENE_RETURN_PROPERTIES
from .types import BasicPosition, Ontology, ParsedVariant, PositionalVariant, Record, Variant
from .util import FeatureNotFoundError, IterableNamespace, convert_to_rid_list, looks_like_rid
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

VARIANT_RETURN_PROPERTIES = (
    BASE_RETURN_PROPERTIES
    + [f'type.{p}' for p in GENERIC_RETURN_PROPERTIES]
    + [f'reference1.{p}' for p in GENE_RETURN_PROPERTIES]
    + [f'reference2.{p}' for p in GENE_RETURN_PROPERTIES]
    + ['zygosity', 'germline', 'displayName']
)

POS_VARIANT_RETURN_PROPERTIES = VARIANT_RETURN_PROPERTIES + [
    'break1Start',
    'break1End',
    'break2Start',
    'break2End',
    'break1Repr',
    'break2Repr',
    'refSeq',
    'untemplatedSeq',
    'untemplatedSeqSize',
    'truncation',
    'assembly',
]


FEATURES_CACHE: Set[str] = set()


def get_equivalent_features(
    conn: GraphKBConnection,
    gene_name: str,
    ignore_cache: bool = False,
    is_source_id: bool = False,
    source: str = '',
    source_id_version: str = '',
) -> List[Ontology]:
    """
    Args:
        gene_name: the gene name to search features by
        ignore_cache (bool, optional): bypass the cache to always force a new request
        is_source_id: treat the gene_name as the gene ID from the source database (ex. ENSG001)
        source_id_version: the version of the source_id
        source: the name of the source database the gene definition is from (ex. ensembl)
    Returns:
        equivalent feature records

    Example:
        get_equivalent_features(conn, 'KRAS')

    Example:
        get_equivalent_features(conn, 'ENSG001', source='ensembl', is_source_id=True)

    Example:
        get_equivalent_features(conn, 'ENSG001', source='ensembl', source_id_version='1')

    Example:
        get_equivalent_features(conn, '#3:44')
    """
    if looks_like_rid(gene_name):
        return cast(
            List[Ontology],
            conn.query({'target': [gene_name], 'queryType': 'similarTo'}, ignore_cache=False),
        )

    filters: List[Dict] = []
    if source:
        filters.append({'source': {'target': 'Source', 'filters': {'name': source}}})

    if is_source_id or source_id_version:
        filters.append({'sourceId': gene_name})

        if source_id_version:
            filters.append(
                {'OR': [{'sourceIdVersion': source_id_version}, {'sourceIdVersion': None}]}
            )

    elif FEATURES_CACHE and gene_name.lower() not in FEATURES_CACHE and not ignore_cache:
        return []
    else:
        filters.append({'OR': [{'sourceId': gene_name}, {'name': gene_name}]})

    return cast(
        List[Ontology],
        conn.query(
            {'target': {'target': 'Feature', 'filters': filters}, 'queryType': 'similarTo'},
            ignore_cache=False,
        ),
    )


def cache_missing_features(conn: GraphKBConnection) -> None:
    """
    Create a cache of features that exist to avoid repeatedly querying
    for missing features
    """
    genes = cast(
        List[Ontology],
        conn.query({'target': 'Feature', 'returnProperties': ['name', 'sourceId'], 'neighbors': 0}),
    )
    for gene in genes:
        if gene['name']:
            FEATURES_CACHE.add(gene['name'].lower())
        if gene['sourceId']:
            FEATURES_CACHE.add(gene['sourceId'].lower())


def match_category_variant(
    conn: GraphKBConnection,
    gene_name: str,
    category: str,
    root_exclude_term: str = '',
    gene_source: str = '',
    gene_is_source_id: bool = False,
) -> List[Variant]:
    """
    Returns a list of variants matching the input variant

    Args:
        conn (GraphKBConnection): the graphkb connection object
        gene_name (str): the name of the gene the variant is in reference to
        category (str): the variant category (ex. copy loss)
        gene_source: The source database the gene is defined by (ex. ensembl)
        gene_is_source_id: Indicates the gene name(s) input should be treated as sourceIds not names
    Raises:
        FeatureNotFoundError: The gene could not be found in GraphKB

    Returns:
        Array.<dict>: List of variant records from GraphKB which match the input
    """
    # disambiguate the gene to find all equivalent representations
    features = convert_to_rid_list(
        get_equivalent_features(conn, gene_name, source=gene_source, is_source_id=gene_is_source_id)
    )

    if not features:
        raise FeatureNotFoundError(
            f'unable to find the gene ({gene_name}) or any equivalent representations'
        )

    # get the list of terms that we should match
    terms = convert_to_rid_list(get_term_tree(conn, category, root_exclude_term))

    if not terms:
        raise ValueError(f'unable to find the term/category ({category}) or any equivalent')

    # find the variant list
    return cast(
        List[Variant],
        conn.query(
            {
                'target': {
                    'target': 'CategoryVariant',
                    'filters': [
                        {'reference1': features, 'operator': 'IN'},
                        {'type': terms, 'operator': 'IN'},
                    ],
                },
                'queryType': 'similarTo',
                'returnProperties': VARIANT_RETURN_PROPERTIES,
            }
        ),
    )


def match_copy_variant(
    conn: GraphKBConnection, gene_name: str, category: str, drop_homozygous: bool = False, **kwargs
) -> List[Variant]:
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
        List of variant records from GraphKB which match the input
    """
    if category not in INPUT_COPY_CATEGORIES.values():
        raise ValueError(f'not a valid copy variant input category ({category})')

    result = match_category_variant(
        conn, gene_name, category, root_exclude_term='structural variant', **kwargs
    )

    if drop_homozygous:
        return [row for row in result if row['zygosity'] != 'homozygous']
    return result


def match_expression_variant(
    conn: GraphKBConnection, gene_name: str, category: str, **kwargs
) -> List[Variant]:
    if category not in INPUT_EXPRESSION_CATEGORIES.values():
        raise ValueError(f'not a valid expression variant input category ({category})')

    return match_category_variant(
        conn, gene_name, category, root_exclude_term='biological', **kwargs
    )


def positions_overlap(
    pos_record: BasicPosition, range_start: BasicPosition, range_end: Optional[BasicPosition] = None
) -> bool:
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


def compare_positional_variants(
    variant: Union[PositionalVariant, ParsedVariant],
    reference_variant: Union[PositionalVariant, ParsedVariant],
) -> bool:
    """
    Compare 2 variant records from GraphKB to determine if they are equivalent

    Args:
        variant: the input variant
        reference_variant: the reference (matched) variant record

    Returns:
        bool: True if the records are equivalent
    """
    if not positions_overlap(
        cast(BasicPosition, variant['break1Start']),
        cast(BasicPosition, reference_variant['break1Start']),
        None
        if 'break1End' not in reference_variant
        else cast(BasicPosition, reference_variant['break1End']),
    ):
        return False

    if 'break2Start' in variant:
        if 'break2Start' not in reference_variant:
            return False
        if not positions_overlap(
            cast(BasicPosition, variant['break2Start']),
            cast(BasicPosition, reference_variant['break2Start']),
            None
            if 'break2End' not in reference_variant
            else cast(BasicPosition, reference_variant['break2End']),
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
            reference_variant['untemplatedSeq'] is not None
            and variant['untemplatedSeq'] is not None
        ):
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
            if reference_variant['refSeq'].lower() != variant['refSeq'].lower():  # type: ignore
                return False
        elif len(variant['refSeq']) != len(reference_variant['refSeq']):  # type: ignore
            return False

    return True


def match_positional_variant(
    conn: GraphKBConnection,
    variant_string: str,
    reference1: Optional[str] = None,
    reference2: Optional[str] = None,
    gene_is_source_id: bool = False,
    gene_source: str = '',
) -> List[Variant]:
    """
    Given the HGVS+ representation of some positional variant, parse it and match it to
    annotations in GraphKB

    Args:
        variant_string: the HGVS+ annotation string
        reference1: Explicitly specify the first reference link record (gene1)
        reference2: Explicitly specify the second reference link record (gene2)
        gene_source: The source database the gene is defined by (ex. ensembl)
        gene_is_source_id: Indicates the gene name(s) input should be treated as sourceIds not names

    Raises:
        NotImplementedError: thrown for uncertain position input (ranges)
        FeatureNotFoundError: One of the genes does not exist in GraphKB
        ValueError: the gene names were given both in the variant_string and explicitly

    Returns:
        A list of matched statement records

    Example:
        match_positional_variant(conn, '(EWSR1,FLI1):fusion(e.1,e.2)')

    Example:
        match_positional_variant(conn, 'fusion(e.1,e.2)', 'EWSR1', 'FLI1')

    Example:
        match_positional_variant(conn, 'fusion(e.1,e.2)', '#3:4', '#4:5')

    Example:
        match_positional_variant(conn, 'fusion(e.1,e.2)', '123', '456', gene_is_source_id=True, gene_source='entrez gene')

    Example:
        match_positional_variant(conn, 'KRAS:p.G12D')

    Example:
        match_positional_variant(conn, 'p.G12D', 'KRAS')
    """
    # parse the representation
    parsed = conn.parse(variant_string, not (reference1 or reference2))

    if 'break1End' in parsed or 'break2End' in parsed:  # uncertain position
        raise NotImplementedError(
            f'Matching does not support uncertain positions ({variant_string}) as input'
        )
    if reference2 and not reference1:
        raise ValueError('cannot specify reference2 without reference1')
    # disambiguate the gene name
    if reference1:
        gene1 = reference1
        if 'reference1' in parsed:
            raise ValueError(
                'Cannot specify reference1 explicitly as well as in the variant notation'
            )
    else:
        gene1 = parsed['reference1']
    features = convert_to_rid_list(
        get_equivalent_features(conn, gene1, source=gene_source, is_source_id=gene_is_source_id)
    )

    if not features:
        raise FeatureNotFoundError(
            f'unable to find the gene ({gene1}) or any equivalent representations'
        )

    secondary_features = None

    gene2: Optional[str] = None
    if reference2:
        gene2 = reference2
        if 'reference2' in parsed:
            raise ValueError(
                'Cannot specify reference2 explicitly as well as in the variant notation'
            )
        elif 'reference1' in parsed:
            raise ValueError(
                'variant notation cannot contain features when explicit features are given'
            )
    elif (
        'reference2' in parsed
        and parsed.get('reference2', '?') != '?'
        and parsed['reference2'] is not None
    ):
        gene2 = parsed['reference2']

    if gene2:
        secondary_features = convert_to_rid_list(
            get_equivalent_features(conn, gene2, source=gene_source, is_source_id=gene_is_source_id)
        )
        if not secondary_features:
            raise FeatureNotFoundError(
                f'unable to find the gene ({gene2}) or any equivalent representations'
            )
    # disambiguate the variant type
    types = convert_to_rid_list(
        get_term_tree(
            conn, parsed['type'], root_exclude_term='mutation' if secondary_features else '',
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

    filtered: List[Record] = []

    for row in cast(
        List[Record],
        conn.query({'target': 'PositionalVariant', 'filters': query_filters}, ignore_cache=False),
    ):
        if compare_positional_variants(parsed, cast(PositionalVariant, row)):
            filtered.append(row)

    # post filter matches
    matches: List[Record] = []
    if filtered:
        matches.extend(
            conn.query(
                {
                    'target': convert_to_rid_list(filtered),
                    'queryType': 'similarTo',
                    'edges': ['AliasOf', 'DeprecatedBy', 'CrossReferenceOf'],
                    'treeEdges': ['Infers'],
                    'returnProperties': POS_VARIANT_RETURN_PROPERTIES,
                }
            ),
        )
    matches.extend(
        conn.query(
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
                'treeEdges': ['Infers'],
                'returnProperties': POS_VARIANT_RETURN_PROPERTIES,
            }
        )
    )

    def cat_variant_query(
        cat_features: List[str],
        cat_types: List[str],
        cat_secondary_features: Optional[List[str]] = None,
    ) -> None:
        matches.extend(
            conn.query(
                {
                    'target': {
                        'target': 'CategoryVariant',
                        'filters': [
                            {'reference1': cat_features},
                            {'type': cat_types},
                            {'reference2': cat_secondary_features},
                        ],
                    },
                    'queryType': 'similarTo',
                    'edges': ['AliasOf', 'DeprecatedBy', 'CrossReferenceOf'],
                    'treeEdges': [],
                    'returnProperties': VARIANT_RETURN_PROPERTIES,
                },
                ignore_cache=False,
            )
        )

    cat_variant_query(features, types, secondary_features)

    if secondary_features:
        # match single gene fusions for either gene
        cat_variant_query(features, types, None)
        cat_variant_query(secondary_features, types, None)

    result: Dict[str, Variant] = {}
    for row in matches:
        result[row['@rid']] = cast(Variant, row)

    return list(result.values())
