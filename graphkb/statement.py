from typing import List, cast

from . import GraphKBConnection
from .constants import FAILED_REVIEW_STATUS, RELEVANCE_BASE_TERMS, STATEMENT_RETURN_PROPERTIES
from .types import CategoryBaseTermMapping, Statement, Variant
from .util import convert_to_rid_list
from .vocab import get_terms_set


def categorize_relevance(
    graphkb_conn: GraphKBConnection,
    relevance_rid: str,
    category_base_terms: CategoryBaseTermMapping = RELEVANCE_BASE_TERMS,
) -> str:
    """
    Given the record ID of some relevance term, return the higher level categorization
    """
    for category, base_terms in category_base_terms:
        term_set = get_terms_set(graphkb_conn, base_terms)
        if relevance_rid in term_set:
            return category
    return ""


def get_statements_from_variants(
    graphkb_conn: GraphKBConnection, variants: List[Variant], failed_review: bool = False
) -> List[Statement]:
    """Given a list of variant records from GraphKB, return related statements.

    Args:
        graphkb_conn (GraphKBConnection): the graphkb api connection object
        variants (list.<dict>): list of variant records. (Have @rid property.)
        failed_review (bool): Include statements that failed review

    Returns:
        list.<dict>: list of Statement records from graphkb
    """
    statements = graphkb_conn.query(
        {
            "target": "Statement",
            "filters": {"conditions": convert_to_rid_list(variants), "operator": "CONTAINSANY"},
            "returnProperties": STATEMENT_RETURN_PROPERTIES,
        }
    )
    if not failed_review:
        statements = [s for s in statements if s.get("reviewStatus") != FAILED_REVIEW_STATUS]
    return [cast(Statement, s) for s in statements]
