import os
from unittest import mock

import pytest

from graphkb import GraphKBConnection


def test_login_ok():
    conn = GraphKBConnection()
    conn.login(os.environ['GRAPHKB_USER'], os.environ['GRAPHKB_PASS'])
    assert conn.token is not None


@pytest.fixture(scope='module')
def conn():
    conn = GraphKBConnection()
    conn.login(os.environ['GRAPHKB_USER'], os.environ['GRAPHKB_PASS'])
    return conn


class TestPaginate:
    @mock.patch('graphkb.GraphKBConnection.request')
    def test_does_not_paginate_when_false(self, graphkb_request, conn):
        graphkb_request.side_effect = [{'result': [1, 2, 3]}, {'result': [4, 5]}]
        result = conn.query({}, paginate=False, limit=3)
        assert result == [1, 2, 3]

    @mock.patch('graphkb.GraphKBConnection.request')
    def test_paginates_by_default(self, graphkb_request, conn):
        graphkb_request.side_effect = [{'result': [1, 2, 3]}, {'result': [4, 5]}]
        result = conn.query({}, paginate=True, limit=3)
        assert result == [1, 2, 3, 4, 5]
