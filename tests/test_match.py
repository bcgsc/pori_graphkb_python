import os
import re

import pytest

from graphkb import GraphKBConnection
from graphkb import match

INCREASE_PREFIXES = ['up', 'increase', 'over', 'gain', 'amp']
DECREASE_PREFIXES = ['down', 'decrease', 'reduce', 'under', 'loss', 'delet']


def has_prefix(word, prefixes):
    for prefix in prefixes:
        if re.search(r'\b' + prefix, word):
            return True
    return False


@pytest.fixture(scope='module')
def conn():
    conn = GraphKBConnection()
    conn.login(os.environ['GRAPHKB_USER'], os.environ['GRAPHKB_PASS'])
    return conn


class TestMatchCopyVariant:
    def test_bad_category(self, conn):
        with pytest.raises(ValueError):
            match.match_copy_variant(conn, 'kras', 'not a copy number')

    def test_bad_gene_name(self, conn):
        with pytest.raises(ValueError):
            match.match_copy_variant(conn, 'not a real gene name', match.INPUT_COPY_CATEGORIES.AMP)

    def test_known_loss(self, conn):
        matches = match.match_copy_variant(conn, 'CDKN2A', match.INPUT_COPY_CATEGORIES.LOSS)
        assert matches

        types_selected = {record['type']['name'] for record in matches}

        assert match.INPUT_COPY_CATEGORIES.LOSS in types_selected
        assert match.INPUT_COPY_CATEGORIES.AMP not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, INCREASE_PREFIXES)
            assert has_prefix(variant_type, DECREASE_PREFIXES)

    def test_known_gain(self, conn):
        matches = match.match_copy_variant(conn, 'KRAS', match.INPUT_COPY_CATEGORIES.GAIN)
        assert matches

        types_selected = {record['type']['name'] for record in matches}

        assert match.INPUT_COPY_CATEGORIES.AMP in types_selected
        assert match.INPUT_COPY_CATEGORIES.LOSS not in types_selected

        for variant_type in types_selected:
            assert has_prefix(variant_type, INCREASE_PREFIXES)
            assert not has_prefix(variant_type, DECREASE_PREFIXES)


class TestMatchExpressionVariant:
    def test_bad_category(self, conn):
        with pytest.raises(ValueError):
            match.match_expression_variant(conn, 'PTEN', 'not a expression category')

    def test_bad_gene_name(self, conn):
        with pytest.raises(ValueError):
            match.match_expression_variant(
                conn, 'not a real gene name', match.INPUT_EXPRESSION_CATEGORIES.UP
            )

    def test_known_reduced_expression(self, conn):
        matches = match.match_expression_variant(
            conn, 'PTEN', match.INPUT_EXPRESSION_CATEGORIES.DOWN
        )
        assert matches

        types_selected = {record['type']['name'] for record in matches}

        assert match.INPUT_EXPRESSION_CATEGORIES.UP not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, INCREASE_PREFIXES)
            assert has_prefix(variant_type, DECREASE_PREFIXES)

    def test_known_increased_expression(self, conn):
        matches = match.match_expression_variant(
            conn, 'CA9', match.INPUT_EXPRESSION_CATEGORIES.UP
        )
        assert matches

        types_selected = {record['type']['name'] for record in matches}

        assert match.INPUT_EXPRESSION_CATEGORIES.UP not in types_selected

        for variant_type in types_selected:
            assert has_prefix(variant_type, INCREASE_PREFIXES)
            assert not has_prefix(variant_type, DECREASE_PREFIXES)
