import pytest
from unittest.mock import Mock

from graphkb import statement


@pytest.fixture()
def graphkb_conn():
    def make_rid_list(*values):
        return [{'@rid': v} for v in values]

    return_values = [
        make_rid_list('1'),  # cat1: therapeutic
        make_rid_list('2'),
        make_rid_list('3'),  # cat2: diagnositic
        make_rid_list('2'),
        [],  # cat3: prognostic
        [],
        [],  # cat4: biological
        [],
    ]
    query_mock = Mock()
    query_mock.side_effect = return_values
    conn = Mock(query=query_mock, cache={})

    return conn


class TestCategorizeRelevance:
    def test_default_categories(self, graphkb_conn):
        category = statement.categorize_relevance(graphkb_conn, '1')
        assert category == 'therapeutic'

    def test_first_match_returns(self, graphkb_conn):
        category = statement.categorize_relevance(graphkb_conn, '2')
        assert category == 'therapeutic'

    def test_second_categoary(self, graphkb_conn):
        category = statement.categorize_relevance(graphkb_conn, '3')
        assert category == 'diagnostic'

    def test_no_match(self, graphkb_conn):
        category = statement.categorize_relevance(graphkb_conn, 'x')
        assert category == ''

    def test_custom_categories(self, graphkb_conn):
        category = statement.categorize_relevance(
            graphkb_conn, 'x', [('blargh', ['some', 'blargh'])]
        )
        assert category == ''

        category = statement.categorize_relevance(
            graphkb_conn, '1', [('blargh', ['some', 'blargh'])]
        )
        assert category == 'blargh'
