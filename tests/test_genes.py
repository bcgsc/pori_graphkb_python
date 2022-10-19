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


@pytest.mark.parametrize('gene', CANONICAL_ONCOGENES)
def test_finds_oncogene(conn, gene):
    result = get_oncokb_oncogenes(conn)

    names = {row['name'] for row in result}
    assert gene in names


@pytest.mark.parametrize('gene', CANONICAL_TS)
def test_ts_not_oncogene(conn, gene):
    result = get_oncokb_oncogenes(conn)

    names = {row['name'] for row in result}
    assert gene not in names


@pytest.mark.parametrize('gene', CANONICAL_ONCOGENES)
def test_oncogene_not_ts(conn, gene):
    result = get_oncokb_tumour_supressors(conn)

    names = {row['name'] for row in result}
    assert gene not in names


@pytest.mark.parametrize('gene', CANONICAL_TS)
def test_finds_ts(conn, gene):
    result = get_oncokb_tumour_supressors(conn)

    names = {row['name'] for row in result}
    assert gene in names


@pytest.mark.parametrize('gene', CANONICAL_FUSION_GENES)
def test_find_fusion_genes(conn, gene):
    result = get_genes_from_variant_types(conn, FUSION_NAMES)
    names = {row['name'] for row in result}
    assert gene in names


@pytest.mark.parametrize('gene', CANNONICAL_THERAPY_GENES + CANONICAL_ONCOGENES + CANONICAL_TS)
def test_get_therapeutic_associated_genes(conn, gene):
    gene_list = get_therapeutic_associated_genes(graphkb_conn=conn)
    assert gene_list, 'No get_therapeutic_associated_genes found'
    assert (
        len(gene_list) > 500
    ), f'Expected over 500 get_therapeutic_associated_genes but found {len(gene_list)}'
    names = {row['name'] for row in gene_list}
    assert gene in names
