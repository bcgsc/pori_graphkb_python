"""
Tests here depend on specific data in GraphKB which can change. To avoid this, expected/stable values are chosen
"""
import os

import pytest

from graphkb import GraphKBConnection, genes

CANONICAL_ONCOGENES = ['kras', 'nras', 'alk']
CANONICAL_TS = ['cdkn2a', 'tp53']
CANONICAL_FUSION_GENES = ['alk', 'ewsr1', 'fli1']


@pytest.fixture(scope='module')
def conn():
    conn = GraphKBConnection()
    conn.login(os.environ['GRAPHKB_USER'], os.environ['GRAPHKB_PASS'])
    return conn


@pytest.mark.parametrize('gene', CANONICAL_ONCOGENES)
def test_finds_oncogene(conn, gene):
    result = genes.get_oncokb_oncogenes(conn)

    names = {row['name'] for row in result}
    assert gene in names


@pytest.mark.parametrize('gene', CANONICAL_TS)
def test_ts_not_oncogene(conn, gene):
    result = genes.get_oncokb_oncogenes(conn)

    names = {row['name'] for row in result}
    assert gene not in names


@pytest.mark.parametrize('gene', CANONICAL_ONCOGENES)
def test_oncogene_not_ts(conn, gene):
    result = genes.get_oncokb_tumour_supressors(conn)

    names = {row['name'] for row in result}
    assert gene not in names


@pytest.mark.parametrize('gene', CANONICAL_TS)
def test_finds_ts(conn, gene):
    result = genes.get_oncokb_tumour_supressors(conn)

    names = {row['name'] for row in result}
    assert gene in names


@pytest.mark.parametrize('gene', CANONICAL_FUSION_GENES)
def test_find_fusion_genes(conn, gene):
    result = genes.get_genes_from_variant_types(conn, genes.FUSION_NAMES)
    names = {row['name'] for row in result}
    assert gene in names
