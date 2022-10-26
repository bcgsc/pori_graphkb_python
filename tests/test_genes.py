"""
Tests here depend on specific data in GraphKB which can change. To avoid this, expected/stable values are chosen
"""
import os

import pytest

from graphkb import GraphKBConnection
from graphkb.constants import FUSION_NAMES
from graphkb.genes import (
    get_genes_from_variant_types,
    get_oncokb_oncogenes,
    get_oncokb_tumour_supressors,
    get_therapeutic_associated_genes,
)

CANONICAL_ONCOGENES = ['kras', 'nras', 'alk']
CANONICAL_TS = ['cdkn2a', 'tp53']
CANONICAL_FUSION_GENES = ['alk', 'ewsr1', 'fli1']
CANNONICAL_THERAPY_GENES = ['erbb2', 'brca2', 'egfr']


@pytest.fixture(scope='module')
def conn():
    conn = GraphKBConnection()
    conn.login(os.environ['GRAPHKB_USER'], os.environ['GRAPHKB_PASS'])
    return conn


def test_oncogene(conn):
    result = get_oncokb_oncogenes(conn)
    names = {row['name'] for row in result}
    for gene in CANONICAL_ONCOGENES:
        assert gene in names
    for gene in CANONICAL_TS:
        assert gene not in names


def test_tumour_supressors(conn):
    result = get_oncokb_tumour_supressors(conn)
    names = {row['name'] for row in result}
    for gene in CANONICAL_TS:
        assert gene in names
    for gene in CANONICAL_ONCOGENES:
        assert gene not in names


def test_find_fusion_genes(conn):
    result = get_genes_from_variant_types(conn, FUSION_NAMES)
    names = {row['name'] for row in result}
    for gene in CANONICAL_FUSION_GENES:
        assert gene in names, f"{gene} was not identified as a fusion gene."


def test_get_therapeutic_associated_genes(conn):
    gene_list = get_therapeutic_associated_genes(graphkb_conn=conn)
    assert gene_list, 'No get_therapeutic_associated_genes found'
    assert (
        len(gene_list) > 500
    ), f'Expected over 500 get_therapeutic_associated_genes but found {len(gene_list)}'
    names = {row['name'] for row in gene_list}
    for gene in CANNONICAL_THERAPY_GENES + CANONICAL_ONCOGENES + CANONICAL_TS:
        assert gene in names, f"{gene} not found by get_therapeutic_associated_genes"
