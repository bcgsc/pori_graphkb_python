"""
Methods for retrieving gene annotation lists from GraphKB
"""
from typing import Any, Dict, List, cast

from . import GraphKBConnection
from .types import Ontology, Statement, Variant

ONCOKB_SOURCE_NAME = 'oncokb'
ONCOGENE = 'oncogenic'
TUMOUR_SUPPRESSIVE = 'tumour suppressive'

FUSION_NAMES = ['structural variant', 'fusion']

GENE_RETURN_PROPERTIES = [
    'name',
    '@rid',
    '@class',
    'sourceId',
    'sourceIdVersion',
    'source.name',
    'source.@rid',
    'displayName',
    'biotype',
    'deprecated',
]


def _get_oncokb_gene_list(conn: GraphKBConnection, relevance: str) -> List[Ontology]:
    source = conn.get_source(ONCOKB_SOURCE_NAME)['@rid']

    statements = cast(
        List[Statement],
        conn.query(
            {
                'target': 'Statement',
                'filters': [
                    {'source': source},
                    {'relevance': {'target': 'Vocabulary', 'filters': {'name': relevance}}},
                ],
                'returnProperties': [f'subject.{prop}' for prop in GENE_RETURN_PROPERTIES],
            },
            ignore_cache=False,
        ),
    )
    genes: Dict[str, Ontology] = {}

    for statement in statements:
        if statement['subject'].get('biotype', '') == 'gene':
            record_id = statement['subject']['@rid']
            genes[record_id] = statement['subject']

    return [gene for gene in genes.values()]


def get_oncokb_oncogenes(conn: GraphKBConnection) -> List[Ontology]:
    """
    Gets the list of oncogenes stored in GraphKB derived from OncoKB

    Args:
        conn: the graphkb connection object

    Returns:
        gene (Feature) records
    """
    return _get_oncokb_gene_list(conn, ONCOGENE)


def get_oncokb_tumour_supressors(conn: GraphKBConnection) -> List[Ontology]:
    """
    Gets the list of tumour supressor genes stored in GraphKB derived from OncoKB

    Args:
        conn: the graphkb connection object

    Returns:
        gene (Feature) records
    """
    return _get_oncokb_gene_list(conn, TUMOUR_SUPPRESSIVE)


def get_genes_from_variant_types(
    conn: GraphKBConnection, types: List[str], source_record_ids: List[str] = []
) -> List[Ontology]:
    """
    Retrieve a list of Genes which are found in variants on the given types

    Args:
        conn: the graphkb connection object
        types: list of names of variant types
        source_record_ids: list of sources ids to filter genes by

    Returns:
        List.<dict>: gene (Feature) records
    """
    variants = cast(
        List[Variant],
        conn.query(
            {
                'target': 'Variant',
                'filters': [
                    {'type': {'target': 'Vocabulary', 'filters': {'name': types, 'operator': 'IN'}}}
                ],
                'returnProperties': ['reference1', 'reference2'],
            },
        ),
    )

    genes = set()

    for variant in variants:
        genes.add(variant['reference1'])

        if variant['reference2']:
            genes.add(variant['reference2'])

    filters: List[Dict[str, Any]] = [{'biotype': 'gene'}]

    if source_record_ids:
        filters.append({'source': source_record_ids, 'operator': 'IN'})

    if not genes:
        return []
    result = cast(
        List[Ontology],
        conn.query(
            {'target': list(genes), 'returnProperties': GENE_RETURN_PROPERTIES, 'filters': filters}
        ),
    )
    return result
