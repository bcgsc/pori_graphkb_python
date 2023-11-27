from graphkb.match import get_equivalent_features
from script_conn import connection

# CONNECTION
##############################################################
env = 'dev'  # 'local' | 'dev' | 'staging' | 'prod'
conn = connection(env)

# DATA
##############################################################
gene = 'BRCA2'
features = get_equivalent_features(conn, gene)

# LOGGING
##############################################################
for feature in features:
    print(
        f'- {feature["@rid"]} - {feature["biotype"]} - {feature["displayName"]} - source: {feature["source"]}'
    )

# # displayName list
# variant = [i['displayName'] for i in matches]
# variant = sorted(list(set(variant)))

# print(f"\nvariant matches: {len(variant)}")
# for pv in variant:
#     print(f'- {pv}')

# # type list
# types = [i.get('type', {}).get('displayName', '') for i in matches]
# types = set(types)
# types.discard('')
# types = sorted(list(types))

# print(f"\ntype matches: {len(types)}:")
# for t in types:
#     print(f'- {t}')
# print()
