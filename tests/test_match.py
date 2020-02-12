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

    def test_known_gain(self, conn):
        matches = match.match_copy_variant(conn, 'KRAS', match.INPUT_COPY_CATEGORIES.GAIN)
        assert matches

        types_selected = {record['type']['name'] for record in matches}

        assert match.INPUT_COPY_CATEGORIES.AMP in types_selected
        assert match.INPUT_COPY_CATEGORIES.LOSS not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, DECREASE_PREFIXES)


class TestPositionsOverlap:
    def test_range_overlaps(self):
        assert match.positions_overlap({'pos': 3}, {'pos': 2}, {'pos': 5})
        assert not match.positions_overlap({'pos': 2}, {'pos': 4}, {'pos': 5})

    def test_nonspecific_range_overlaps(self):
        assert match.positions_overlap({'pos': 2}, {'pos': None}, {'pos': 5})
        assert match.positions_overlap({'pos': 3}, {'pos': 2}, {'pos': None})

    def test_nonspecific_overlaps(self):
        assert match.positions_overlap({'pos': None}, {'pos': 1})
        assert match.positions_overlap({'pos': None}, {'pos': None})
        assert match.positions_overlap({'pos': 1}, {'pos': None})

    def test_exact_overlaps(self):
        assert match.positions_overlap({'pos': 1}, {'pos': 1})
        assert not match.positions_overlap({'pos': 1}, {'pos': 2})


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

    def test_known_increased_expression(self, conn):
        matches = match.match_expression_variant(conn, 'CA9', match.INPUT_EXPRESSION_CATEGORIES.UP)
        assert matches

        types_selected = {record['type']['name'] for record in matches}

        assert match.INPUT_EXPRESSION_CATEGORIES.UP not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, DECREASE_PREFIXES)


class TestComparePositionalVariants:
    def test_nonspecific_altseq(self):
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}}, {'break1Start': {'pos': 1}}
        )
        # null matches anything
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'T'}, {'break1Start': {'pos': 1}}
        )
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}}, {'break1Start': {'pos': 1}, 'untemplatedSeq': 'T'}
        )

    def test_ambiguous_altseq(self):
        # ambiguous AA matches anything the same length
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'T'},
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'X'},
        )
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'T'},
            {'break1Start': {'pos': 1}, 'untemplatedSeq': '?'},
        )
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'X'},
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'T'},
        )
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'untemplatedSeq': '?'},
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'T'},
        )

    def test_altseq_length_mismatch(self):
        assert not match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'untemplatedSeq': '??'},
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'T'},
        )
        assert not match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'untemplatedSeq': '?'},
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'TT'},
        )

    def test_nonspecific_refseq(self):
        # null matches anything
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'refSeq': 'T'}, {'break1Start': {'pos': 1}}
        )
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}}, {'break1Start': {'pos': 1}, 'refSeq': 'T'}
        )

    def test_ambiguous_refseq(self):
        # ambiguous AA matches anything the same length
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'refSeq': 'T'}, {'break1Start': {'pos': 1}, 'refSeq': 'X'},
        )
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'refSeq': 'T'}, {'break1Start': {'pos': 1}, 'refSeq': '?'},
        )
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'refSeq': 'X'}, {'break1Start': {'pos': 1}, 'refSeq': 'T'},
        )
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'refSeq': '?'}, {'break1Start': {'pos': 1}, 'refSeq': 'T'},
        )

    def test_refseq_length_mismatch(self):
        assert not match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'refSeq': '??'}, {'break1Start': {'pos': 1}, 'refSeq': 'T'},
        )
        assert not match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'refSeq': '?'}, {'break1Start': {'pos': 1}, 'refSeq': 'TT'},
        )

    def test_diff_altseq(self):
        assert not match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'M'},
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'R'},
        )

    def test_same_altseq_matches(self):
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'R'},
            {'break1Start': {'pos': 1}, 'untemplatedSeq': 'R'},
        )

    def test_diff_refseq(self):
        assert not match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'refSeq': 'M'}, {'break1Start': {'pos': 1}, 'refSeq': 'R'},
        )

    def test_same_refseq_matches(self):
        assert match.compare_positional_variants(
            {'break1Start': {'pos': 1}, 'refSeq': 'R'}, {'break1Start': {'pos': 1}, 'refSeq': 'R'},
        )


class TestMatchPositionalVariant:
    def test_known_substitution(self, conn):
        known = 'KRAS:p.G12D'
        matches = match.match_positional_variant(conn, known)
        names = {m['displayName'] for m in matches}
        assert matches
        assert known in names
        assert 'KRAS:p.G12V' not in names
        assert 'KRAS:p.G12X' in names
        assert 'chr12:g.25398284C>T' in names

    def test_known_fusion(self, conn):
        known = '(BCR,ABL1):fusion(e.13,e.3)'
        matches = match.match_positional_variant(conn, known)
        names = {m['displayName'] for m in matches}
        assert matches
        assert known in names
        assert 'BCR and ABL1 fusion' in names

    def test_known_indel(self, conn):
        known = 'EGFR:p.E746_S752delinsI'
        matches = match.match_positional_variant(conn, known)
        names = {m['displayName'] for m in matches}
        assert matches
        assert known in names
        assert 'EGFR mutation' in names
        assert 'EGFR copy variant' not in names

    def test_movel_specific_matches_general(self, conn):
        novel_specific = 'CDKN2A:p.T18888888888888888888M'
        matches = match.match_positional_variant(conn, novel_specific)
        names = {m['displayName'] for m in matches}
        assert matches
        assert novel_specific not in names
        assert 'CDKN2A mutation' in names
