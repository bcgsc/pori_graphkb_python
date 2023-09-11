import os
import re
from typing import List
from unittest.mock import MagicMock

import pytest

import graphkb
from graphkb import GraphKBConnection, match
from graphkb.constants import DEFAULT_NON_STRUCTURAL_VARIANT_TYPE, STRUCTURAL_VARIANT_SIZE_THRESHOLD
from graphkb.util import FeatureNotFoundError

# Test datasets
from .data import structuralVariants

EXCLUDE_INTEGRATION_TESTS = os.environ.get("EXCLUDE_INTEGRATION_TESTS") == "1"

INCREASE_PREFIXES = ["up", "increase", "over", "gain", "amp"]
DECREASE_PREFIXES = ["down", "decrease", "reduce", "under", "loss", "delet"]
GENERAL_MUTATION = "mutation"


def has_prefix(word: str, prefixes: List[str]) -> bool:
    for prefix in prefixes:
        if re.search(r"\b" + prefix, word):
            return True
    return False


@pytest.fixture(scope="module")
def conn() -> GraphKBConnection:
    conn = GraphKBConnection()
    conn.login(os.environ["GRAPHKB_USER"], os.environ["GRAPHKB_PASS"])
    return conn


@pytest.fixture(scope="class")
def kras(conn):
    return [f["displayName"] for f in match.get_equivalent_features(conn, "kras")]


class TestGetEquivalentFeatures:
    def test_kras_has_self(self, kras):
        assert "KRAS" in kras

    def test_expands_aliases(self, kras):
        assert "KRAS2" in kras

    def test_expands_elements(self, kras):
        assert "NM_033360" in kras
        assert "ENST00000311936" in kras

    def test_expands_generalizations(self, kras):
        assert "NM_033360.4" in kras
        assert "ENSG00000133703.11" in kras

    def test_expands_generalizations_kras(self, kras):
        assert "NM_033360.4" in kras
        assert "NM_033360" in kras
        assert "ENSG00000133703.11" in kras
        assert "ENSG00000133703" in kras

    @pytest.mark.parametrize(
        "alt_rep", ("NM_033360.4", "NM_033360", "ENSG00000133703.11", "ENSG00000133703")
    )
    def test_expands_generalizations_refseq(self, alt_rep, conn):
        kras = [f["displayName"] for f in match.get_equivalent_features(conn, alt_rep)]
        assert "NM_033360.4" in kras
        assert "NM_033360" in kras
        assert "ENSG00000133703.11" in kras
        assert "ENSG00000133703" in kras

    def test_checks_by_source_id_kras(self, conn):
        kras = [
            f["displayName"]
            for f in match.get_equivalent_features(
                conn, "nm_033360", source="refseq", source_id_version="4", is_source_id=True
            )
        ]
        assert "KRAS" in kras


class TestMatchCopyVariant:
    def test_bad_category(self, conn):
        with pytest.raises(ValueError):
            match.match_copy_variant(conn, "kras", "not a copy number")

    def test_bad_gene_name(self, conn):
        with pytest.raises(FeatureNotFoundError):
            match.match_copy_variant(conn, "not a real gene name", match.INPUT_COPY_CATEGORIES.AMP)

    def test_known_loss(self, conn):
        matches = match.match_copy_variant(conn, "CDKN2A", match.INPUT_COPY_CATEGORIES.ANY_LOSS)
        assert matches

        types_selected = {record["type"]["name"] for record in matches}
        zygositys = {record["zygosity"] for record in matches}

        assert match.INPUT_COPY_CATEGORIES.ANY_LOSS in types_selected
        assert match.INPUT_COPY_CATEGORIES.AMP not in types_selected
        assert GENERAL_MUTATION not in types_selected

        assert "homozygous" in zygositys

        for variant_type in types_selected:
            assert not has_prefix(variant_type, INCREASE_PREFIXES)

    def test_known_loss_zygosity_filtered(self, conn):
        matches = match.match_copy_variant(
            conn, "CDKN2A", match.INPUT_COPY_CATEGORIES.ANY_LOSS, True
        )
        assert matches

        types_selected = {record["type"]["name"] for record in matches}
        zygositys = {record["zygosity"] for record in matches}

        assert "homozygous" not in zygositys

        assert GENERAL_MUTATION not in types_selected
        assert match.INPUT_COPY_CATEGORIES.ANY_LOSS in types_selected
        assert match.INPUT_COPY_CATEGORIES.AMP not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, INCREASE_PREFIXES)

    def test_known_gain(self, conn):
        matches = match.match_copy_variant(conn, "KRAS", "copy gain")
        assert matches

        types_selected = {record["type"]["name"] for record in matches}

        assert GENERAL_MUTATION not in types_selected
        assert match.INPUT_COPY_CATEGORIES.AMP in types_selected
        assert match.INPUT_COPY_CATEGORIES.ANY_LOSS not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, DECREASE_PREFIXES)

    @pytest.mark.skipif(
        EXCLUDE_INTEGRATION_TESTS, reason="excluding long running integration tests"
    )
    def test_low_gain_excludes_amplification(self, conn):
        matches = match.match_copy_variant(conn, "KRAS", match.INPUT_COPY_CATEGORIES.GAIN)

        types_selected = {record["type"]["name"] for record in matches}

        assert match.INPUT_COPY_CATEGORIES.AMP not in types_selected
        assert match.INPUT_COPY_CATEGORIES.LOSS not in types_selected
        assert GENERAL_MUTATION not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, DECREASE_PREFIXES)


@pytest.mark.parametrize("pos1,pos2_start,pos2_end", [[3, 2, 5], [2, None, 5], [3, 2, None]])
def test_range_overlap(pos1, pos2_start, pos2_end):
    assert match.positions_overlap({"pos": pos1}, {"pos": pos2_start}, {"pos": pos2_end})


@pytest.mark.parametrize(
    "pos1,pos2_start,pos2_end",
    [[2, 4, 5], [5, 2, 3], [10, None, 9], [10, 11, None], [1, 2, 2], [2, 1, 1]],
)
def test_range_not_overlap(pos1, pos2_start, pos2_end):
    assert not match.positions_overlap({"pos": pos1}, {"pos": pos2_start}, {"pos": pos2_end})


@pytest.mark.parametrize("pos1", [None, 1])
@pytest.mark.parametrize("pos2", [None, 1])
def test_position_match(pos1, pos2):
    assert match.positions_overlap({"pos": pos1}, {"pos": pos2})


class TestMatchExpressionVariant:
    def test_bad_category(self, conn):
        with pytest.raises(ValueError):
            match.match_expression_variant(conn, "PTEN", "not a expression category")

    def test_bad_gene_name(self, conn):
        with pytest.raises(FeatureNotFoundError):
            match.match_expression_variant(
                conn, "not a real gene name", match.INPUT_EXPRESSION_CATEGORIES.UP
            )

    @pytest.mark.skipif(
        EXCLUDE_INTEGRATION_TESTS, reason="excluding long running integration tests"
    )
    def test_known_reduced_expression(self, conn):
        matches = match.match_expression_variant(
            conn, "PTEN", match.INPUT_EXPRESSION_CATEGORIES.DOWN
        )
        assert matches

        types_selected = {record["type"]["name"] for record in matches}

        assert match.INPUT_EXPRESSION_CATEGORIES.UP not in types_selected
        assert GENERAL_MUTATION not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, INCREASE_PREFIXES)

    def test_known_reduced_expression_gene_id(self, conn):
        gene_id = conn.query({"target": "Feature", "filters": [{"name": "PTEN"}]})[0]["@rid"]
        matches = match.match_expression_variant(
            conn, gene_id, match.INPUT_EXPRESSION_CATEGORIES.DOWN
        )
        assert matches

        types_selected = {record["type"]["name"] for record in matches}

        assert match.INPUT_EXPRESSION_CATEGORIES.UP not in types_selected
        assert GENERAL_MUTATION not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, INCREASE_PREFIXES)

    @pytest.mark.skipif(
        EXCLUDE_INTEGRATION_TESTS, reason="excluding long running integration tests"
    )
    def test_known_increased_expression(self, conn):
        matches = match.match_expression_variant(conn, "CA9", match.INPUT_EXPRESSION_CATEGORIES.UP)
        assert matches

        types_selected = {record["type"]["name"] for record in matches}

        assert match.INPUT_EXPRESSION_CATEGORIES.UP not in types_selected
        assert GENERAL_MUTATION not in types_selected

        for variant_type in types_selected:
            assert not has_prefix(variant_type, DECREASE_PREFIXES)


class TestComparePositionalVariants:
    def test_nonspecific_altseq(self):
        assert match.compare_positional_variants(
            {"break1Start": {"pos": 1}}, {"break1Start": {"pos": 1}}
        )
        # null matches anything
        assert match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "untemplatedSeq": "T"}, {"break1Start": {"pos": 1}}
        )
        assert match.compare_positional_variants(
            {"break1Start": {"pos": 1}}, {"break1Start": {"pos": 1}, "untemplatedSeq": "T"}
        )

    @pytest.mark.parametrize("seq1", ["T", "X", "?"])
    @pytest.mark.parametrize("seq2", ["T", "X", "?"])
    def test_ambiguous_altseq(self, seq1, seq2):
        # ambiguous AA matches anything the same length
        assert match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "untemplatedSeq": seq1},
            {"break1Start": {"pos": 1}, "untemplatedSeq": seq2},
        )

    def test_altseq_length_mismatch(self):
        assert not match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "untemplatedSeq": "??"},
            {"break1Start": {"pos": 1}, "untemplatedSeq": "T"},
        )
        assert not match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "untemplatedSeq": "?"},
            {"break1Start": {"pos": 1}, "untemplatedSeq": "TT"},
        )

    def test_nonspecific_refseq(self):
        # null matches anything
        assert match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "refSeq": "T"}, {"break1Start": {"pos": 1}}
        )
        assert match.compare_positional_variants(
            {"break1Start": {"pos": 1}}, {"break1Start": {"pos": 1}, "refSeq": "T"}
        )

    @pytest.mark.parametrize("seq1", ["T", "X", "?"])
    @pytest.mark.parametrize("seq2", ["T", "X", "?"])
    def test_ambiguous_refseq(self, seq1, seq2):
        # ambiguous AA matches anything the same length
        assert match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "refSeq": seq1}, {"break1Start": {"pos": 1}, "refSeq": seq2}
        )

    def test_refseq_length_mismatch(self):
        assert not match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "refSeq": "??"}, {"break1Start": {"pos": 1}, "refSeq": "T"}
        )
        assert not match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "refSeq": "?"}, {"break1Start": {"pos": 1}, "refSeq": "TT"}
        )

    def test_diff_altseq(self):
        assert not match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "untemplatedSeq": "M"},
            {"break1Start": {"pos": 1}, "untemplatedSeq": "R"},
        )

    def test_same_altseq_matches(self):
        assert match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "untemplatedSeq": "R"},
            {"break1Start": {"pos": 1}, "untemplatedSeq": "R"},
        )

    def test_diff_refseq(self):
        assert not match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "refSeq": "M"}, {"break1Start": {"pos": 1}, "refSeq": "R"}
        )

    def test_same_refseq_matches(self):
        assert match.compare_positional_variants(
            {"break1Start": {"pos": 1}, "refSeq": "R"}, {"break1Start": {"pos": 1}, "refSeq": "R"}
        )

    def test_range_vs_sub(self):
        sub = {
            "break1Repr": "p.G776",
            "break1Start": {"@Class": "ProteinPosition", "pos": 776, "refAA": "G"},
            "break2Repr": "p.V777",
            "break2Start": {"@Class": "ProteinPosition", "pos": 777, "refAA": "V"},
            "reference1": "ERBB2",
            "type": "insertion",
            "untemplatedSeq": "YVMA",
            "untemplatedSeqSize": 4,
        }
        range_variant = {
            "break1Repr": "p.G776",
            "break1Start": {"@Class": "ProteinPosition", "pos": 776, "refAA": "G"},
            "break2Repr": "p.?776",
            "break2Start": None,
            "refSeq": "G",
            "untemplatedSeq": "VV",
        }
        assert not match.compare_positional_variants(sub, range_variant)
        assert not match.compare_positional_variants(range_variant, sub)


class TestMatchPositionalVariant:
    def test_error_on_duplicate_reference1(self, conn):
        with pytest.raises(ValueError):
            match.match_positional_variant(conn, "KRAS:p.G12D", "#123:34")

    def test_error_on_bad_reference2(self, conn):
        with pytest.raises(ValueError):
            match.match_positional_variant(conn, "KRAS:p.G12D", reference2="#123:34")

    def test_error_on_duplicate_reference2(self, conn):
        with pytest.raises(ValueError):
            match.match_positional_variant(
                conn, "(BCR,ABL1):fusion(e.13,e.3)", reference2="#123:34"
            )

    def test_uncertain_position_not_supported(self, conn):
        with pytest.raises(NotImplementedError):
            match.match_positional_variant(conn, "(BCR,ABL1):fusion(e.13_24,e.3)")

    def test_bad_gene_name(self, conn):
        with pytest.raises(FeatureNotFoundError):
            match.match_positional_variant(conn, "ME-AS-A-GENE:p.G12D")

    def test_bad_gene2_name(self, conn):
        with pytest.raises(FeatureNotFoundError):
            match.match_positional_variant(conn, "(BCR,ME-AS-A-GENE):fusion(e.13,e.3)")

    def test_match_explicit_reference1(self, conn):
        reference1 = conn.query({"target": "Feature", "filters": {"name": "KRAS"}})[0]["@rid"]
        matches = match.match_positional_variant(conn, "p.G12D", reference1=reference1)
        assert matches

    @pytest.mark.skipif(
        EXCLUDE_INTEGRATION_TESTS, reason="excluding long running integration tests"
    )
    def test_match_explicit_references(self, conn):
        reference1 = conn.query({"target": "Feature", "filters": {"name": "BCR"}})[0]["@rid"]
        reference2 = conn.query({"target": "Feature", "filters": {"name": "ABL1"}})[0]["@rid"]
        matches = match.match_positional_variant(
            conn, "fusion(e.13,e.3)", reference1=reference1, reference2=reference2
        )
        assert matches

    @pytest.mark.skipif(
        EXCLUDE_INTEGRATION_TESTS, reason="excluding long running integration tests"
    )
    @pytest.mark.parametrize(
        "known_variant,related_variants,unrelated_variants",
        [
            ["KRAS:p.G12D", ["KRAS:p.G12X", "chr12:g.25398284C>T"], ["KRAS:p.G12V"]],
            ["KRAS:p.G13D", ["KRAS:p.?13mut"], []],
            ["chr12:g.25398284C>T", ["KRAS:p.G12D"], ["KRAS:p.G12V"]],
            ["EGFR:p.E746_S752delinsI", ["EGFR mutation"], ["EGFR copy variant"]],
        ],
    )
    def test_known_variants(self, conn, known_variant, related_variants, unrelated_variants):
        matches = match.match_positional_variant(conn, known_variant)
        names = {m["displayName"] for m in matches}
        assert matches
        assert known_variant in names
        for variant in related_variants:
            assert variant in names
        for variant in unrelated_variants:
            assert variant not in names

    @pytest.mark.parametrize(
        "known_variant,related_variants",
        [
            ["(BCR,ABL1):fusion(e.13,e.3)", ["BCR and ABL1 fusion"]],
            ["(ATP1B1,NRG1):fusion(e.2,e.2)", ["NRG1 fusion", "ATP1B1 and NRG1 fusion"]],
        ],
    )
    def test_known_fusions(self, conn, known_variant, related_variants):
        matches = match.match_positional_variant(conn, known_variant)
        types_selected = [m["type"]["name"] for m in matches]
        assert GENERAL_MUTATION not in types_selected
        names = {m["displayName"] for m in matches}
        assert matches
        assert known_variant in names
        for variant in related_variants:
            assert variant in names

    def test_known_fusion_single_gene_no_match(self, conn):
        known = "(TERT,?):fusion(e.1,e.?)"
        matches = match.match_positional_variant(conn, known)
        assert not matches

    def test_novel_specific_matches_general(self, conn):
        novel_specific = "CDKN2A:p.T18888888888888888888M"
        matches = match.match_positional_variant(conn, novel_specific)
        names = {m["displayName"] for m in matches}
        assert matches
        assert novel_specific not in names
        assert "CDKN2A mutation" in names

    @pytest.mark.skipif(
        EXCLUDE_INTEGRATION_TESTS, reason="excluding long running integration tests"
    )
    def test_genomic_coordinates(self, conn):
        genomic = "X:g.100611165A>T"
        match.match_positional_variant(conn, genomic)
        # no assert b/c checking for no error rather than the result

    @pytest.mark.skipif(
        EXCLUDE_INTEGRATION_TESTS, reason="excluding long running integration tests"
    )
    def test_tert_promoter(self, conn):
        assert match.match_positional_variant(conn, "TERT:c.-124C>T")

    @pytest.mark.skipif(
        True, reason="GERO-303 - technically incorrect notation for GSC backwards compatibility."
    )
    def test_tert_promoter_leading_one_alt_notation(self, conn):
        # GERO-303 - technically this format is incorrect.
        assert match.match_positional_variant(conn, "TERT:c.1-124C>T")

    def test_missense_is_not_nonsense(self, conn):
        """GERO-299 - nonsense mutation creates a stop codon and is usually more severe."""
        # equivalent TP53 notations
        genomic = "chr17:g.7674252C>T"
        cds = "ENST00000269305:c.711G>A"
        protein = "TP53:p.M237I"
        for mut in (protein, genomic, cds):
            matches = match.match_positional_variant(conn, mut)
            nonsense = [m for m in matches if "nonsense" in m["displayName"]]
            assert (
                not nonsense
            ), f"Missense {mut} is not a nonsense variant: {((m['displayName'], m['@rid']) for m in nonsense)}"

    def test_structural_variants(self, conn):
        """KBDEV-1056"""
        for variant_string, expected in structuralVariants.items():
            print(variant_string)
            # Querying matches for variant_string
            m = match.match_positional_variant(conn, variant_string)
            MatchingDisplayNames = [el["displayName"] for el in m]
            MatchingTypes = [el["type"]["name"] for el in m]

            # Match
            for displayName in expected.get('matches', {}).get("displayName", []):
                assert displayName in MatchingDisplayNames
            for type in expected.get('matches', {}).get("type", []):
                assert type in MatchingTypes

            # Does not match
            for displayName in MatchingDisplayNames:
                assert displayName not in expected.get('does_not_matches', {}).get(
                    "displayName", []
                )
            for type in MatchingTypes:
                assert type not in expected.get('does_not_matches', {}).get("type", [])


class TestCacheMissingFeatures:
    def test_filling_cache(self):
        mock_conn = MagicMock(
            query=MagicMock(
                return_value=[
                    {"name": "bob", "sourceId": "alice"},
                    {"name": "KRAS", "sourceId": "1234"},
                ]
            )
        )
        match.cache_missing_features(mock_conn)
        assert "kras" in match.FEATURES_CACHE
        assert "alice" in match.FEATURES_CACHE


class TestTypeScreening:
    # Types as class variables
    default_type = DEFAULT_NON_STRUCTURAL_VARIANT_TYPE
    threshold = STRUCTURAL_VARIANT_SIZE_THRESHOLD
    unambiguous_structural = [
        "fusion",
        "translocation",
    ]
    ambiguous_structural = [
        "duplication",
        "deletion",
        "insertion",
        "indel",
    ]
    non_structural = [
        "substitution",
        "missense",
        "nonsense",
        "frameshift",
        "truncating",
    ]

    def test_type_screening_update(self, conn, monkeypatch):
        # Monkey-patching get_terms_set()
        def mock_get_terms_set(graphkb_conn, base_terms):
            nonlocal called
            called = True
            return set()

        monkeypatch.setattr("graphkb.match.get_terms_set", mock_get_terms_set)

        # Assert get_terms_set() has been called
        called = False
        graphkb.match.type_screening(conn, {"type": ""}, updateStructuralTypes=True)
        assert called

        # Assert get_terms_set() has not been called (default behavior)
        called = False
        graphkb.match.type_screening(conn, {"type": ""})
        assert not called

    def test_type_screening_non_structural(self, conn):
        for type in TestTypeScreening.non_structural:
            # type substitution and alike
            assert match.type_screening(conn, {"type": type}) == type

    def test_type_screening_structural(self, conn):
        for type in TestTypeScreening.unambiguous_structural:
            # type fusion and alike
            assert match.type_screening(conn, {"type": type}) == type
        for type in TestTypeScreening.ambiguous_structural:
            # w/ reference2
            assert match.type_screening(conn, {"type": type, "reference2": "#123:45"}) == type
            # w/ cytoband coordinates
            assert match.type_screening(conn, {"type": type, "prefix": "y"}) == type

    def test_type_screening_structural_ambiguous_size(self, conn):
        for type in TestTypeScreening.ambiguous_structural:
            # coordinate system with ambiguous size
            for prefix in ['e', 'i']:
                assert (
                    match.type_screening(
                        conn,
                        {
                            "type": type,
                            "break2Start": {"pos": TestTypeScreening.threshold},
                            "prefix": prefix,
                        },
                    )
                    == TestTypeScreening.default_type
                )

    def test_type_screening_structural_untemplatedSeqSize(self, conn):
        for type in TestTypeScreening.ambiguous_structural:
            # Variation length too small (< threshold)
            assert (
                match.type_screening(
                    conn,
                    {
                        "type": type,
                        "untemplatedSeqSize": TestTypeScreening.threshold - 1,
                    },
                )
                == TestTypeScreening.default_type
            )
            # Variation length big enough (>= threshold)
            assert (
                match.type_screening(
                    conn,
                    {
                        "type": type,
                        "untemplatedSeqSize": TestTypeScreening.threshold,
                    },
                )
                == type
            )

    def test_type_screening_structural_positions(self, conn):
        for type in TestTypeScreening.ambiguous_structural:
            # Variation length too small (< threshold)
            for opt in [
                {"break2Start": {"pos": TestTypeScreening.threshold - 1}},
                {"break2Start": {"pos": TestTypeScreening.threshold - 1}, "prefix": "c"},
                {"break2Start": {"pos": TestTypeScreening.threshold - 1}, "prefix": "g"},
                {"break2Start": {"pos": TestTypeScreening.threshold - 1}, "prefix": "n"},
                {"break2Start": {"pos": TestTypeScreening.threshold - 1}, "prefix": "r"},
                {"break2Start": {"pos": int(TestTypeScreening.threshold / 3) - 1}, "prefix": "p"},
                {
                    "break1Start": {"pos": 1 + 99},
                    "break2Start": {"pos": TestTypeScreening.threshold + 99 - 1},
                },
            ]:
                assert (
                    match.type_screening(conn, {"type": type, **opt})
                    == TestTypeScreening.default_type
                )
            # Variation length big enough (>= threshold)
            for opt in [
                {"break2Start": {"pos": TestTypeScreening.threshold}},
                {"break2Start": {"pos": TestTypeScreening.threshold}, "prefix": "c"},
                {"break2Start": {"pos": TestTypeScreening.threshold}, "prefix": "g"},
                {"break2Start": {"pos": TestTypeScreening.threshold}, "prefix": "n"},
                {"break2Start": {"pos": TestTypeScreening.threshold}, "prefix": "r"},
                {"break2Start": {"pos": int(TestTypeScreening.threshold / 3) + 1}, "prefix": "p"},
                {
                    "break1Start": {"pos": 1 + 99},
                    "break2Start": {"pos": TestTypeScreening.threshold + 99},
                },
            ]:
                assert match.type_screening(conn, {"type": type, **opt}) == type
