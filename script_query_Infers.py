import os
from graphkb import GraphKBConnection

# GKB_API_URL: str = 'https://graphkbdev-api.bcgsc.ca/api'
GKB_USER: str = os.environ['USER']
GKB_PASSWORD: str = os.environ['JIRA_PASS']

conn = GraphKBConnection()
conn.login(GKB_USER, GKB_PASSWORD)

query_filters = [
    {'in': '#160:0'},
    {'out': '#159:903'}
]

res = conn.query(
    {'target': 'Infers', 'filters': query_filters}
),

for i in res[0]:
    print(i)
