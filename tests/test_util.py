import pytest

from graphkb import util


class TestLooksLikeRid:
    @pytest.mark.parametrize('rid', ['#3:4', '#50:04', '#-3:4', '#-3:-4', '#3:-4'])
    def test_valid(self, rid):
        assert util.looks_like_rid(rid)

    @pytest.mark.parametrize('rid', ['-3:4', 'KRAS'])
    def test_invalid(self, rid):
        assert not util.looks_like_rid(rid)


@pytest.mark.parametrize(
    'input,result',
    [
        ['GP5:p.Leu113His', 'GP5:p.L113H'],
        ['GP5:p.Lys113His', 'GP5:p.K113H'],
        ['CDK11A:p.Arg536Gln', 'CDK11A:p.R536Q'],
        ['APC:p.Cys1405*', 'APC:p.C1405*'],
        ['ApcTer:p.Cys1405*', 'ApcTer:p.C1405*'],
        ['GP5:p.Leu113_His114insLys', 'GP5:p.L113_H114insK'],
        ['NP_003997.1:p.Lys23_Val25del', 'NP_003997.1:p.K23_V25del'],
        ['LRG_199p1:p.Val7del', 'LRG_199p1:p.V7del'],
    ],
)
def test_convert_aa_3to1(input, result):
    assert util.convert_aa_3to1(input) == result
