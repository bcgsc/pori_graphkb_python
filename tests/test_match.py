import os
import re
from typing import List
from unittest.mock import MagicMock

import pytest

from graphkb import GraphKBConnection, match
from graphkb.util import FeatureNotFoundError

INCREASE_PREFIXES = ['up', 'increase', 'over', 'gain', 'amp']
DECREASE_PREFIXES = ['down', 'decrease', 'reduce', 'under', 'loss', 'delet']
GENERAL_MUTATION = 'mutation'


def has_prefix(word: str, prefixes: List[str]) -> bool:
    for prefix in prefixes:
        if re.search(r'\b' + prefix, word):
            return True
    return False


@pytest.fixture(scope='module')
def conn() -> GraphKBConnection:
    conn = GraphKBConnection()
    conn.login(os.environ['GRAPHKB_USER'], os.environ['GRAPHKB_PASS'])
    return conn


class TestMatchCopyVariant:
    def test_bad_category(self, conn):
        with pytest.raises(ValueError):
            match.match_copy_variant(conn, 'kras', 'not a copy number')

    def test_bad_gene_name(self, conn):
        with pytest.raises(FeatureNotFoundError):
            match.match_copy_variant(conn, 'not a real gene name', match.INPUT_COPY_CATEGORIES.AMP)

    def test_known_loss(self, conn):
        matches = match.match_copy_variant(conn, 'CDKN2A', match.INPUT_COPY_CATEGORIES.ANY_LOSS)
        assert matches

        types_selected = {record['type']['name'] for record in matches}
        zygositys = {record['zygosity'] for record in matches}

        assert match.INPUT_COPY_CATEGORIES.ANY_LOSS in types_selected
        assert match.INPUT_COPY_CATEGORIES.AMP not in types_selected
        assert GENERAL_MUTATION not in types_selected

        assert 'homozygous' in zygositys

        for variant_type in types_selected:
            assert not has_prefix(variant_type, INCREASE_PREFIXES)

    def test_known_loss_zygosity_filtered(self, conn):
        matches = match.match_copy_variant(
            conn, 'CDKN2A', match.INPUT_COPY_CATEGORIES.ANY_LOSS, True
        )
        assert matches

        types_selected = {record['type']['name'] for record in matches}
        zygositys = {record['zygosity'] for record in matches}

        assert 'homozygous' not in zygositys

        assert GENERAL_MUTATION not in types_selected
        assert match.INPUT_COPY_CATEGORIES.ANY_LOSS in types_selected
        assert match.INPUT_COPY_CATEGORIES.AMP not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, INCREASE_PREFIXES)

    def test_known_gain(self, conn):
        matches = match.match_copy_variant(conn, 'KRAS', 'copy gain')
        assert matches

        types_selected = {record['type']['name'] for record in matches}

        assert GENERAL_MUTATION not in types_selected
        assert match.INPUT_COPY_CATEGORIES.AMP in types_selected
        assert match.INPUT_COPY_CATEGORIES.ANY_LOSS not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, DECREASE_PREFIXES)

    def test_low_gain_excludes_amplification(self, conn):
        matches = match.match_copy_variant(conn, 'KRAS', match.INPUT_COPY_CATEGORIES.GAIN)

        types_selected = {record['type']['name'] for record in matches}

        assert match.INPUT_COPY_CATEGORIES.AMP not in types_selected
        assert match.INPUT_COPY_CATEGORIES.LOSS not in types_selected
        assert GENERAL_MUTATION not in types_selected

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
        with pytest.raises(FeatureNotFoundError):
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
        assert GENERAL_MUTATION not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, INCREASE_PREFIXES)

    def test_known_reduced_expression_gene_id(self, conn):
        gene_id = conn.query({'target': 'Feature', 'filters': [{'name': 'PTEN'}]})[0]['@rid']
        matches = match.match_expression_variant(
            conn, gene_id, match.INPUT_EXPRESSION_CATEGORIES.DOWN
        )
        assert matches

        types_selected = {record['type']['name'] for record in matches}

        assert match.INPUT_EXPRESSION_CATEGORIES.UP not in types_selected
        assert GENERAL_MUTATION not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, INCREASE_PREFIXES)

    def test_known_increased_expression(self, conn):
        matches = match.match_expression_variant(conn, 'CA9', match.INPUT_EXPRESSION_CATEGORIES.UP)
        assert matches

        types_selected = {record['type']['name'] for record in matches}

        assert match.INPUT_EXPRESSION_CATEGORIES.UP not in types_selected
        assert GENERAL_MUTATION not in types_selected

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
    def test_error_on_duplicate_reference1(self, conn):
        with pytest.raises(ValueError):
            match.match_positional_variant(conn, 'KRAS:p.G12D', '#123:34')

    def test_error_on_bad_reference2(self, conn):
        with pytest.raises(ValueError):
            match.match_positional_variant(conn, 'KRAS:p.G12D', reference2='#123:34')

    def test_error_on_duplicate_reference2(self, conn):
        with pytest.raises(ValueError):
            match.match_positional_variant(
                conn, '(BCR,ABL1):fusion(e.13,e.3)', reference2='#123:34'
            )

    def test_uncertain_position_not_supported(self, conn):
        with pytest.raises(NotImplementedError):
            match.match_positional_variant(
                conn, '(BCR,ABL1):fusion(e.13_24,e.3)',
            )

    def test_bad_gene_name(self, conn):
        with pytest.raises(FeatureNotFoundError):
            match.match_positional_variant(
                conn, 'ME-AS-A-GENE:p.G12D',
            )

    def test_bad_gene2_name(self, conn):
        with pytest.raises(FeatureNotFoundError):
            match.match_positional_variant(
                conn, '(BCR,ME-AS-A-GENE):fusion(e.13,e.3)',
            )

    def test_match_explicit_reference1(self, conn):
        reference1 = conn.query({'target': 'Feature', 'filters': {'name': 'KRAS'}})[0]['@rid']
        matches = match.match_positional_variant(conn, 'p.G12D', reference1=reference1)
        assert matches

    def test_match_explicit_references(self, conn):
        reference1 = conn.query({'target': 'Feature', 'filters': {'name': 'BCR'}})[0]['@rid']
        reference2 = conn.query({'target': 'Feature', 'filters': {'name': 'ABL1'}})[0]['@rid']
        matches = match.match_positional_variant(
            conn, 'fusion(e.13,e.3)', reference1=reference1, reference2=reference2
        )
        assert matches

    def test_known_substitution(self, conn):
        known = 'KRAS:p.G12D'
        matches = match.match_positional_variant(conn, known)
        names = {m['displayName'] for m in matches}
        assert matches
        assert known in names
        assert 'KRAS:p.G12V' not in names
        assert 'KRAS:p.G12X' in names
        assert 'chr12:g.25398284C>T' in names

        known = 'KRAS:p.G13D'
        matches = match.match_positional_variant(conn, known)
        names = {m['displayName'] for m in matches}
        assert matches
        assert known in names
        assert 'KRAS:p.?13mut' in names

    def test_known_fusion(self, conn):
        known = '(BCR,ABL1):fusion(e.13,e.3)'
        matches = match.match_positional_variant(conn, known)
        types_selected = [m['type']['name'] for m in matches]
        assert GENERAL_MUTATION not in types_selected
        names = {m['displayName'] for m in matches}
        assert matches
        assert known in names
        assert 'BCR and ABL1 fusion' in names

    def test_known_fusion_cat_match(self, conn):
        known = '(ATP1B1,NRG1):fusion(e.2,e.2)'
        matches = match.match_positional_variant(conn, known)
        types_selected = [m['type']['name'] for m in matches]
        assert GENERAL_MUTATION not in types_selected
        names = {m['displayName'] for m in matches}
        assert matches
        assert known in names
        assert 'NRG1 fusion' in names
        assert 'ATP1B1 and NRG1 fusion' in names

    def test_known_fusion_single_gene_no_match(self, conn):
        known = '(BCR,?):fusion(e.13,e.?)'
        matches = match.match_positional_variant(conn, known)
        assert not matches

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

    def test_genomic_coordinates(self, conn):
        genomic = 'X:g.100611165A>T'
        match.match_positional_variant(conn, genomic)
        # no assert b/c checking for no error rather than the result


class TestCacheMissingFeatures:
    def test_filling_cache(self):
        mock_conn = MagicMock(
            query=MagicMock(
                return_value=[
                    {'name': 'bob', 'sourceId': 'alice'},
                    {'name': 'KRAS', 'sourceId': '1234'},
                ]
            )
        )
        match.cache_missing_features(mock_conn)
        assert 'kras' in match.FEATURES_CACHE
        assert 'alice' in match.FEATURES_CACHE
