from graphkb import util


class TestLooksLikeRid:
    def test_valid(self):
        assert util.looks_like_rid('#3:4')
        assert util.looks_like_rid('#50:04')

    def test_valid_with_negative(self):
        assert util.looks_like_rid('#-3:4')
        assert util.looks_like_rid('#-3:-4')
        assert util.looks_like_rid('#3:-4')

    def test_invalid_without_hash(self):
        assert not util.looks_like_rid('-3:4')

    def test_invalid_random_gene(self):
        assert not util.looks_like_rid('KRAS')


class TestConvertAA3to1:
    def test_substitution(self):
        assert util.convert_aa_3to1('GP5:p.Leu113His') == 'GP5:p.L113H'

    def test_non_matching_short_form(self):
        assert util.convert_aa_3to1('GP5:p.Lys113His') == 'GP5:p.K113H'
        assert util.convert_aa_3to1('CDK11A:p.Arg536Gln') == 'CDK11A:p.R536Q'

    def test_truncation(self):
        assert util.convert_aa_3to1('APC:p.Cys1405*') == 'APC:p.C1405*'

    def test_gene_with_aa_like_pattern(self):
        assert util.convert_aa_3to1('ApcTer:p.Cys1405*') == 'ApcTer:p.C1405*'

    def test_insertion(self):
        assert util.convert_aa_3to1('GP5:p.Leu113_His114insLys') == 'GP5:p.L113_H114insK'

    def test_deletion(self):
        assert util.convert_aa_3to1('NP_003997.1:p.Lys23_Val25del') == 'NP_003997.1:p.K23_V25del'
        assert util.convert_aa_3to1('LRG_199p1:p.Val7del') == 'LRG_199p1:p.V7del'
