"""
Tests here depend on specific data in GraphKB which can change. To avoid this, expected/stable values are chosen
"""
import os

import pytest

from graphkb import GraphKBConnection
from graphkb.constants import FUSION_NAMES
from graphkb.genes import (
    get_cancer_predisposition_info,
    get_genes_from_variant_types,
    get_oncokb_oncogenes,
    get_oncokb_tumour_supressors,
    get_pharmacogenomic_info,
    get_preferred_gene_name,
)

CANONICAL_ONCOGENES = ['kras', 'nras', 'alk']
CANONICAL_TS = ['cdkn2a', 'tp53']
CANONICAL_FUSION_GENES = ['alk', 'ewsr1', 'fli1']
PHARMACOGENOMIC_INITIAL_GENES = [
    'ACYP2',
    'CEP72',
    # 'CYP26B1',  # defined as hgvsGenomic chr2:g.233760235_233760235nc_000002.12:g.233760235ta[7]>ta[8]
    'DPYD',
    'NUDT15',
    'RARG',
    'SLC28A3',
    'TPMT',
    'UGT1A6',
]
CANCER_PREDISP_INITIAL_GENES = [
    'AKT1',
    'APC',
    'ATM',
    'AXIN2',
    'BAP1',
    'BLM',
    'BMPR1A',
    'BRCA1',
    'BRCA2',
    'BRIP1',
    'CBL',
    'CDH1',
    'CDK4',
    'CDKN2A',
    'CHEK2',
    'DICER1',
    'EGFR',
    'EPCAM',
    'ETV6',
    'EZH2',
    'FH',
    'FLCN',
    'GATA2',
    'HRAS',
    'KIT',
    'MEN1',
    'MET',
    'MLH1',
    'MSH2',
    'MSH6',
    'MUTYH',
    'NBN',
    'NF1',
    'PALB2',
    'PDGFRA',
    'PMS2',
    'PTCH1',
    'PTEN',
    'PTPN11',
    'RAD51C',
    'RAD51D',
    'RB1',
    'RET',
    'RUNX1',
    'SDHA',
    'SDHB',
    'SDHC',
    'SDHD',
    'SMAD4',
    'SMARCA4',
    'STK11',
    'TP53',
    'TSC1',
    'TSC2',
    'VHL',
    'WT1',
]


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


def test_get_pharmacogenomic_info(conn):
    genes, matches = get_pharmacogenomic_info(conn)
    for gene in PHARMACOGENOMIC_INITIAL_GENES:
        assert gene in genes, f"{gene} not found in get_pharmacogenomic_info"
        for rid, variant_display in matches.items():
            if variant_display.startswith(gene):
                break
        else:  # no break called
            assert False, f"No rid found for a pharmacogenomic with {gene}"


def test_get_cancer_predisposition_info(conn):
    genes, matches = get_cancer_predisposition_info(conn)
    for gene in CANCER_PREDISP_INITIAL_GENES:
        assert gene in genes, f"{gene} not found in get_cancer_predisposition_info"


@pytest.mark.parametrize(
    'alt_rep', ('NM_033360.4', 'NM_033360', 'ENSG00000133703.11', 'ENSG00000133703')
)
def test_get_preferred_gene_name_kras(alt_rep, conn):
    gene_name = get_preferred_gene_name(conn, alt_rep)
    assert (
        'KRAS' == gene_name
    ), f"Expected KRAS as preferred gene name for {alt_rep}, not '{gene_name}'"


@pytest.mark.parametrize('gene', CANONICAL_FUSION_GENES)
def test_find_fusion_genes(conn, gene):
    result = get_genes_from_variant_types(conn, FUSION_NAMES)
    names = {row['name'] for row in result}
    assert gene in names
