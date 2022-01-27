from unittest.mock import Mock

import pytest

from graphkb import statement


@pytest.fixture()
def graphkb_conn():
    def make_rid_list(*values):
        return [{'@rid': v} for v in values]

    def term_tree_calls(*final_values):
        # this function makes 2 calls to conn.query here
        sets = [['fake'], final_values]
        return [make_rid_list(*s) for s in sets]

    return_values = [
        *term_tree_calls('1'),  # therapeutic
        *term_tree_calls('2'),  # therapeutic (2nd base term)
        *term_tree_calls('3'),  # diagnostic
        *term_tree_calls('4'),  # prognostic
        *term_tree_calls('5'),  # pharmacogenomic ['metabolism']
        *term_tree_calls('6'),  # pharmacogenomic ['toxicity']
        *term_tree_calls('7'),  # pharmacogenomic ['dosage']
        *term_tree_calls('8'),  # cancer predisposition
        *term_tree_calls(),  # biological
        *term_tree_calls(),  # biological (2nd base term)
        *term_tree_calls(),  # biological (3rd base term)
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

    def test_second_category(self, graphkb_conn):
        category = statement.categorize_relevance(graphkb_conn, '3')
        assert category == 'diagnostic'

    def test_third_category(self, graphkb_conn):
        category = statement.categorize_relevance(graphkb_conn, '4')
        assert category == 'prognostic'

    def test_fourth_category(self, graphkb_conn):
        category = statement.categorize_relevance(graphkb_conn, '5')
        assert category == 'pharmacogenomic'

    def test_fifth_category(self, graphkb_conn):
        category = statement.categorize_relevance(graphkb_conn, '6')
        assert category == 'pharmacogenomic'

    def test_predisposition_category(self, graphkb_conn):
        category = statement.categorize_relevance(graphkb_conn, '8')
        assert category == 'cancer predisposition'

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
