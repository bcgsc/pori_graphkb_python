import subprocess, json

from graphkb import match, statement

from script_data import variant_strings
from script_conn import connection


# CONNECTION
##############################################################
env = 'prod'  # 'local' | 'dev' | 'staging' | 'prod'
conn = connection(env)

# DATASET
##############################################################
variant_string_list = variant_strings.get('SDEV-3892', {})

# MATCHING VARIANTS
variants = []
##############################################################
for variant_string in variant_string_list:
    print(f"{'='*50}\n{variant_string}")

    # matching variants
    matches = match.match_positional_variant(conn, variant_string)
    variants += matches

    # displayName list
    variant = [f"{i['@rid']} {i['displayName']}" for i in matches]
    variant = sorted(list(set(variant)))
    
    print(f"\nvariant matches: {len(variant)}")
    for pv in variant:
        print(f'- {pv}')

    # type list
    types = [i.get('type', {}).get('displayName', '') for i in matches]
    types = set(types)
    types.discard('')
    types = sorted(list(types))

    print(f"\ntype matches: {len(types)}:")
    for t in types:
        print(f'- {t}')
    print()



# MATCHING STATEMENTS
##############################################################

# variant_records = conn.query({})

statements = statement.get_statements_from_variants(conn, variants)
print(f"statements: {len(statements)}")
for i in statements:
    print(i['@rid'])

x = conn.query({"target":"Statement", "filters": {"conditions": ['#162:149'], "operator": "CONTAINSANY"},})
print(f"matching #162:149: {len(x)}")
for i in x: print(i['@rid'])

# statement template display
print(x[0])
print('='*50)

s = json.dumps(x[0])
# s = str(x[0])
p = subprocess.Popen(f"""node displayStatement.js '{s}'""", stdout=subprocess.PIPE, shell=True)
print('%'*50)
print(p.communicate())