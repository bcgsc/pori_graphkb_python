from graphkb.preview import get_preview, natural_list_join


class TestNaturalListJoin:
    def test_single_item(self):
        assert natural_list_join(['1']) == '1'

    def test_empty_list(self):
        assert natural_list_join([]) == ''

    def test_multiple_items(self):
        assert natural_list_join(['1', '2', '3']) == '1, 2, and 3'


class TestPreview:
    def test_statement(self):
        statement = {
            'evidence': [
                {'displayName': 'pmid:22490330', '@rid': '#118:774', '@class': 'Publication'}
            ],
            'subject': {
                'sourceId': 'doid:9119',
                'displayName': 'acute myeloid leukemia [DOID:9119]',
                'name': 'acute myeloid leukemia',
                '@rid': '#135:9855',
                '@class': 'Disease',
            },
            'displayNameTemplate': '{conditions:variant} {relevance} of {subject} ({evidence})',
            'relevance': {
                'displayName': 'favours diagnosis',
                '@rid': '#148:2',
                '@class': 'Vocabulary',
            },
            'conditions': [
                {
                    'displayName': 'DNMT3A:p.R882',
                    '@rid': '#160:1133',
                    '@class': 'PositionalVariant',
                },
                {
                    'displayName': 'acute myeloid leukemia [DOID:9119]',
                    '@rid': '#135:9855',
                    '@class': 'Disease',
                },
            ],
            '@class': 'Statement',
        }
        get_preview(
            statement
        ) == 'DNMT3A:p.R882 favours diagnosis of acute myeloid leukemia [DOID:9119] (pmid:22490330)'
