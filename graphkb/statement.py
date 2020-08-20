from . import GraphKBConnection
from .vocab import get_terms_set
from .constants import RELEVANCE_BASE_TERMS
from .types import CategoryBaseTermMapping


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
    return ''
