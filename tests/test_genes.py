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


def test_oncokb_oncogenes(conn):
    result = genes.get_oncokb_oncogenes(conn)

    names = {row['name'] for row in result}

    for name in CANONICAL_ONCOGENES:
        assert name in names

    for name in CANONICAL_TS:
        assert name not in names


def test_oncokb_tumour_suppressors(conn):
    result = genes.get_oncokb_tumour_supressors(conn)

    names = {row['name'] for row in result}

    for name in CANONICAL_ONCOGENES:
        assert name not in names

    for name in CANONICAL_TS:
        assert name in names


def test_get_genes_from_variant_types(conn):
    result = genes.get_genes_from_variant_types(conn, genes.FUSION_NAMES)
    names = {row['name'] for row in result}

    for fusion_gene in CANONICAL_FUSION_GENES:
        assert fusion_gene in names
