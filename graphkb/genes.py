"""
Methods for retrieving gene annotation lists from GraphKB
"""
from typing import Any, Dict, List, cast

from . import GraphKBConnection
from .constants import (
    BASE_THERAPEUTIC_TERMS,
    GENE_RETURN_PROPERTIES,
    ONCOGENE,
    ONCOKB_SOURCE_NAME,
    TUMOUR_SUPPRESSIVE,
)
from .types import Ontology, Statement, Variant
from .vocab import get_terms_set


def _get_oncokb_gene_list(
    conn: GraphKBConnection, relevance: str, ignore_cache: bool = False
) -> List[Ontology]:
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
            ignore_cache=ignore_cache,
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


def get_therapeutic_associated_genes(graphkb_conn: GraphKBConnection) -> List[Ontology]:
    """Genes related to a cancer-associated statement in Graphkb."""
    therapeutic_relevance = get_terms_set(graphkb_conn, BASE_THERAPEUTIC_TERMS)
    statements = graphkb_conn.query(
        {
            'target': 'Statement',
            'filters': {'relevance': sorted(list(therapeutic_relevance))},
            'returnProperties': ['reviewStatus']
            + [f'conditions.{prop}' for prop in GENE_RETURN_PROPERTIES]
            + [
                f'conditions.reference{ref}.{prop}'
                for prop in GENE_RETURN_PROPERTIES
                for ref in ('1', '2')
            ],
        }
    )
    genes: List[Ontology] = []
    for statement in statements:
        if statement['reviewStatus'] == 'failed':
            continue
        for condition in statement['conditions']:
            if condition['@class'] == 'Feature':
                genes.append(condition)
            elif condition['@class'].endswith('Variant'):
                cond = cast(Variant, condition)
                if cond['reference1'] and cond['reference1']['@class'] == 'Feature':
                    genes.append(cond['reference1'])
                if cond['reference2'] and cond['reference2']['@class'] == 'Feature':
                    genes.append(cond['reference2'])
    unique_genes: List[Ontology] = []
    for gene in genes:
        if not gene.get('deprecated', False):
            if gene['@rid'] not in [g['@rid'] for g in unique_genes]:
                unique_genes.append(gene)
    return unique_genes


def get_genes_from_variant_types(
    conn: GraphKBConnection,
    types: List[str],
    source_record_ids: List[str] = [],
    ignore_cache: bool = False,
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
            ignore_cache=ignore_cache,
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
            {'target': list(genes), 'returnProperties': GENE_RETURN_PROPERTIES, 'filters': filters},
            ignore_cache=ignore_cache,
        ),
    )
    return result
