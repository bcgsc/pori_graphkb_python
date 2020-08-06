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
