import os

import pytest

from graphkb import GraphKBConnection, util


class OntologyTerm:
    def __init__(self, name, sourceId, displayName):
        self.name = name
        self.sourceId = sourceId
        self.displayName = displayName


@pytest.fixture(scope="module")
def conn() -> GraphKBConnection:
    conn = GraphKBConnection()
    conn.login(os.environ["GRAPHKB_USER"], os.environ["GRAPHKB_PASS"])
    return conn


class TestLooksLikeRid:
    @pytest.mark.parametrize("rid", ["#3:4", "#50:04", "#-3:4", "#-3:-4", "#3:-4"])
    def test_valid(self, rid):
        assert util.looks_like_rid(rid)

    @pytest.mark.parametrize("rid", ["-3:4", "KRAS"])
    def test_invalid(self, rid):
        assert not util.looks_like_rid(rid)


@pytest.mark.parametrize(
    "input,result",
    [
        ["GP5:p.Leu113His", "GP5:p.L113H"],
        ["GP5:p.Lys113His", "GP5:p.K113H"],
        ["CDK11A:p.Arg536Gln", "CDK11A:p.R536Q"],
        ["APC:p.Cys1405*", "APC:p.C1405*"],
        ["ApcTer:p.Cys1405*", "ApcTer:p.C1405*"],
        ["GP5:p.Leu113_His114insLys", "GP5:p.L113_H114insK"],
        ["NP_003997.1:p.Lys23_Val25del", "NP_003997.1:p.K23_V25del"],
        ["LRG_199p1:p.Val7del", "LRG_199p1:p.V7del"],
    ],
)
def test_convert_aa_3to1(input, result):
    assert util.convert_aa_3to1(input) == result


class TestOntologyTermRepr:
    @pytest.mark.parametrize(
        "termStr,termRepr", [["missense mutation", "missense mutation"], ["", ""]]
    )
    def test_ontologyTermRepr_str(self, termStr, termRepr):
        assert util.ontologyTermRepr(termStr) == termRepr

    @pytest.mark.parametrize(
        "termObjOpt,termRepr",
        [
            [{"displayName": "abc123", "name": "", "sourceId": ""}, "abc123"],
            [{"displayName": "", "name": "", "sourceId": "abc123"}, "abc123"],
            [{"displayName": "", "name": "abc123", "sourceId": ""}, "abc123"],
            [{"displayName": "", "name": "", "sourceId": ""}, ""],
        ],
    )
    def test_ontologyTermRepr_obj(self, termObjOpt, termRepr):
        termObj = OntologyTerm(**termObjOpt)
        assert util.ontologyTermRepr(termObj) == termRepr


class TestStripParentheses:
    @pytest.mark.parametrize(
        "breakRepr,StrippedBreakRepr",
        [
            ["p.(E2015_Q2114)", "p.E2015_Q2114"],
            ["p.(?572_?630)", "p.?572_?630"],
            ["g.178916854", "g.178916854"],
            ["e.10", "e.10"],
        ],
    )
    def test_stripParentheses(self, breakRepr, StrippedBreakRepr):
        assert util.stripParentheses(breakRepr) == StrippedBreakRepr


class TestStripRefSeq:
    @pytest.mark.parametrize(
        "breakRepr,StrippedBreakRepr",
        [
            ["p.L2209", "p.2209"],
            ["p.?891", "p.891"],
            # TODO: ['p.?572_?630', 'p.572_630'],
        ],
    )
    def test_stripRefSeq(self, breakRepr, StrippedBreakRepr):
        assert util.stripRefSeq(breakRepr) == StrippedBreakRepr


class TestStripDisplayName:
    @pytest.mark.parametrize(
        "opt,stripDisplayName",
        [
            [{"displayName": "ABL1:p.T315I", "withRef": True, "withRefSeq": True}, "ABL1:p.T315I"],
            [{"displayName": "ABL1:p.T315I", "withRef": False, "withRefSeq": True}, "p.T315I"],
            [{"displayName": "ABL1:p.T315I", "withRef": True, "withRefSeq": False}, "ABL1:p.315I"],
            [{"displayName": "ABL1:p.T315I", "withRef": False, "withRefSeq": False}, "p.315I"],
            [
                {"displayName": "chr3:g.41266125C>T", "withRef": False, "withRefSeq": False},
                "g.41266125>T",
            ],
            [
                {
                    "displayName": "chrX:g.99662504_99662505insG",
                    "withRef": False,
                    "withRefSeq": False,
                },
                "g.99662504_99662505insG",
            ],
            [
                {
                    "displayName": "chrX:g.99662504_99662505dup",
                    "withRef": False,
                    "withRefSeq": False,
                },
                "g.99662504_99662505dup",
            ],
            # TODO: [{'displayName': 'VHL:c.330_331delCAinsTT', 'withRef': False, 'withRefSeq': False}, 'c.330_331delinsTT'],
            # TODO: [{'displayName': 'VHL:c.464-2G>A', 'withRef': False, 'withRefSeq': False}, 'c.464-2>A'],
        ],
    )
    def test_stripDisplayName(self, opt, stripDisplayName):
        assert util.stripDisplayName(**opt) == stripDisplayName


class TestStringifyVariant:
    @pytest.mark.parametrize(
        "hgvs_string,opt,stringifiedVariant",
        [
            ["VHL:c.345C>G", {"withRef": True, "withRefSeq": True}, "VHL:c.345C>G"],
            ["VHL:c.345C>G", {"withRef": False, "withRefSeq": True}, "c.345C>G"],
            ["VHL:c.345C>G", {"withRef": True, "withRefSeq": False}, "VHL:c.345>G"],
            ["VHL:c.345C>G", {"withRef": False, "withRefSeq": False}, "c.345>G"],
            [
                "(LMNA,NTRK1):fusion(e.10,e.12)",
                {"withRef": False, "withRefSeq": False},
                "fusion(e.10,e.12)",
            ],
            ["ABCA12:p.N1671Ifs*4", {"withRef": False, "withRefSeq": False}, "p.1671Ifs*4"],
            ["x:y.p22.33copyloss", {"withRef": False, "withRefSeq": False}, "y.p22.33copyloss"],
            # TODO: ['MED12:p.(?34_?68)mut', {'withRef': False, 'withRefSeq': False}, 'p.(34_68)mut'],
            # TODO: ['FLT3:p.(?572_?630)_(?572_?630)ins', {'withRef': False, 'withRefSeq': False}, 'p.(572_630)_(572_630)ins'],
        ],
    )
    def test_stringifyVariant_parsed(self, conn, hgvs_string, opt, stringifiedVariant):
        opt["variant"] = conn.parse(hgvs_string)
        assert util.stringifyVariant(**opt) == stringifiedVariant

    # Based on the assumption that these variants are in the database.
    # createdAt date help avoiding errors if assumption tuns to be false
    @pytest.mark.parametrize(
        "rid,createdAt,stringifiedVariant",
        [
            ["#157:0", 1565627324397, "p.315I"],
            ["#157:79", 1565627683602, "p.776_777insVGC"],
            ["#158:35317", 1652734056311, "c.1>G"],
        ],
    )
    def test_stringifyVariant_positional(self, conn, rid, createdAt, stringifiedVariant):
        opt = {"withRef": False, "withRefSeq": False}
        variant = conn.get_record_by_id(rid)
        if variant and variant.get("createdAt", None) == createdAt:
            assert util.stringifyVariant(variant=variant, **opt) == stringifiedVariant
