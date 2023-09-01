import os
from typing import Dict, List

from graphkb import GraphKBConnection
from graphkb.types import Record

GKB_API_URL = {
    "local": f'http://{os.environ["HOSTNAME"]}:8080/api/',
    "dev": 'https://graphkbdev-api.bcgsc.ca/api',
    "prod": 'https://graphkb-api.bcgsc.ca/api',
}


# DB Connection
def connection(env: str) -> GraphKBConnection:
    return GraphKBConnection(
        url=GKB_API_URL[env],
        username=os.environ['USER'],
        password=os.environ['JIRA_PASS'],
        use_global_cache=False,
    )


# Using GraphKBConnection's post method
# Limited by the API to a maximunm of 1000 records per query but can be set to a lower limit
# Using the skip data's property for pagination
def get_statements_by_post(conn: GraphKBConnection, limit: int = 1000) -> List[Dict]:
    records: List[Dict] = []
    while True:
        response = conn.post(
            uri="query",
            data={
                "target": "Statement",
                "returnProperties": ["conditions.@rid", "conditions.@class"],
                "limit": limit,
                "skip": len(records),
                # "filters": {"@rid": "#153:2"},  # Optional filtering
            },
        )
        records += response['result']
        if response['metadata']['records'] < limit:
            return records


# Using GraphKBConnection's query method
# Will return all the records at once; pagination is handeled in the background
# Will also use a cahce if not deactivated
def get_statements_by_query(conn: GraphKBConnection) -> List[Record]:
    return conn.query(
        {
            "target": "Statement",
            "returnProperties": ["conditions.@rid", "conditions.@class"],
            # "filters": {"@rid": "#153:2"},  # Optional filtering
        },
        ignore_cache=True,
    )


results = get_statements_by_query(conn=connection('dev'))
positionalVariants = set()
for r in results:
    for condition in r['conditions']:
        if condition['@class'] == 'PositionalVariant':
            positionalVariants.add(condition['@rid'])

print(len(positionalVariants))
