import os
from typing import Dict, Iterable, List, Set

from graphkb import GraphKBConnection, constants, match, types, util, vocab

# GKB_API_URL: str = 'https://graphkbdev-api.bcgsc.ca/api' # 'http://mlemieux01.phage.bcgsc.ca:8080/api/' #
GKB_USER: str = os.environ['USER']
GKB_PASSWORD: str = os.environ['JIRA_PASS']

# conn = GraphKBConnection(GKB_API_URL, use_global_cache=False)
conn = GraphKBConnection()
conn.login(GKB_USER, GKB_PASSWORD)

# gene_name: str = "TSC2" #"TP53"
# category: str = "small mutation" #"substitution"
# variant_string: str = "TSC2:c.3365G>C"
# variant_string: str = "TSC2:c.4700G>A"
variant_string: str = "KRAS:p.G12D"

# # match_positional_variant()
# positional_variant: List[types.Variant] = match.match_positional_variant(conn, variant_string)
# # positional_variant = list(set(positional_variant))
# # positional_variant = sorted(positional_variant, key=lambda d: d['displayName'])
# displayNames = [i['displayName'] for i in positional_variant]
# displayNames = sorted(list(set(displayNames)))
# print(f"\nmatches for positional variant {variant_string} ({len(displayNames)}):")
# for pv in displayNames:
#     print(pv)

query_filters = [
    {'reference1': ['#127:91609', '#128:64304', '#125:94839', '#127:3145', '#125:33712', '#127:64304', '#128:94838', '#126:3145', '#128:33711', '#126:64304', '#127:94838', '#125:3145', '#127:33711', '#125:64304', '#126:94838', '#128:3144', '#126:33711', '#127:11256', '#127:42139', '#127:103287', '#125:42140', '#126:103287', '#125:103287', '#126:11256', '#126:72410', '#128:11256', '#125:72410', '#128:72409', '#128:42139']},
    {'reference2': None},
    {'type': ['#145:43', '#145:66', '#145:31', '#145:23', '#145:53', '#148:18', '#145:67', '#148:37']},
    # {'break1Start.@class': 'ProteinPosition'}
]

res = conn.query(
    {'target': 'PositionalVariant', 'filters': query_filters}
),

for i in res[0]:
    print(i['displayName'])
print(len(res[0]))