import os

from graphkb import GraphKBConnection, constants, match  # , types, util, vocab
from graphkb.vocab import get_equivalent_terms, get_term_tree

# # Production
# GKB_API_URL: str = 'https://graphkb-api.bcgsc.ca/api'
# GKB_USER: str = os.environ['USER']
# GKB_PASSWORD: str = os.environ['JIRA_PASS']

# # Staging
# GKB_API_URL: str = 'https://graphkbstaging-api.bcgsc.ca/api'
# GKB_USER: str = 'graphkb_importer'
# GKB_PASSWORD: str = os.environ['GKB_PASS']

# Dev
GKB_API_URL: str = 'https://graphkbdev-api.bcgsc.ca/api'
GKB_USER: str = os.environ['USER']
GKB_PASSWORD: str = os.environ['JIRA_PASS']

# # Local
# GKB_API_URL: str = 'http://mlemieux01.phage.bcgsc.ca:8080/api/'
# GKB_USER: str = os.environ['USER']
# GKB_PASSWORD: str = os.environ['JIRA_PASS']

conn = GraphKBConnection(GKB_API_URL, use_global_cache=False)  # conn = GraphKBConnection()
conn.login(GKB_USER, GKB_PASSWORD)


#
matches = match.type_screening(conn, {"type": "duplication"}, updateTypes=True)
