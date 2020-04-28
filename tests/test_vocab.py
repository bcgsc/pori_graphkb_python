"""
Tests here depend on specific data in GraphKB which can change. To avoid this, expected/stable values are chosen
"""
import os

import pytest

from graphkb import GraphKBConnection, genes, vocab

BASE_EXPRESSION = 'expression variant'
BASE_INCREASED_EXPRESSION = 'increased expression'
BASE_REDUCED_EXPRESSION = 'reduced expression'


@pytest.fixture(scope='module')
def conn():
    conn = GraphKBConnection()
    conn.login(os.environ['GRAPHKB_USER'], os.environ['GRAPHKB_PASS'])
    return conn


def test_expression_vocabulary(conn):
    result = vocab.get_term_tree(conn, BASE_EXPRESSION)

    names = [row['name'] for row in result]
    assert BASE_EXPRESSION in names
    assert 'increased rna expression' in names


def test_indel_vocabulary(conn):
    result = vocab.get_term_tree(conn, 'indel')

    names = {row['name'] for row in result}
    assert 'indel' in names
    assert 'copy variant' not in names
    assert 'copy number variant' not in names


def test_expression_up(conn):
    result = vocab.get_term_tree(conn, BASE_INCREASED_EXPRESSION)

    names = [row['name'] for row in result]
    assert BASE_EXPRESSION in names
    assert BASE_INCREASED_EXPRESSION in names
    assert 'increased rna expression' in names
    assert 'reduced rna expression' not in names
    assert BASE_REDUCED_EXPRESSION not in names


def test_expression_down(conn):
    result = vocab.get_term_tree(conn, BASE_REDUCED_EXPRESSION)

    names = [row['name'] for row in result]
    assert BASE_EXPRESSION in names
    assert BASE_REDUCED_EXPRESSION in names
    assert BASE_INCREASED_EXPRESSION not in names
    assert 'increased rna expression' not in names
    assert 'reduced rna expression' in names


class TestGetEquivalentTerms:
    def test_gain_excludes_amplification(self, conn):
        result = vocab.get_equivalent_terms(conn, 'copy gain')
        names = {row['name'] for row in result}
        assert 'copy gain' in names
        assert 'amplification' not in names

    def test_amplification_includes_gain(self, conn):
        result = vocab.get_equivalent_terms(conn, 'amplification')
        names = {row['name'] for row in result}
        assert 'copy gain' in names
        assert 'amplification' in names


def test_oncogenic(conn):
    result = vocab.get_term_by_name(conn, genes.ONCOGENE)
    assert result['name'] == genes.ONCOGENE
