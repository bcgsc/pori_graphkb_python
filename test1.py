import json
import os

from graphkb import GraphKBConnection

GKB_API_URL = 'https://graphkb-api.bcgsc.ca/api/'
GKB_USER = os.environ['USER']
GKB_PASSWORD = os.environ['JIRA_PASS']

graphkb_conn = GraphKBConnection(GKB_API_URL, use_global_cache=False)

graphkb_conn.login(GKB_USER, GKB_PASSWORD)

response = graphkb_conn.query(
    {'target': 'Source', 'filters': {'@rid': '#38:1'}},
    paginate=False,
    limit=3,
)


# test
for i in response:
    print('-' * 50)
    for k, v in i.items():
        print(k, ':\n\t', v)
