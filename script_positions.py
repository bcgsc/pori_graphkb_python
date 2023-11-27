from graphkb import match
from script_conn import connection

# CONNECTION
##############################################################
env = 'dev'  # 'local' | 'dev' | 'staging' | 'prod'
conn = connection(env)

# DATA
##############################################################




for variant_string in variant_string_list:
    print(f"{'='*50}\n{variant_string}")

    # # PARSING ONLY
    # ##############################################################
    # parsed = conn.parse(variant_string)

    # MATCHING
    ##############################################################
    matches = match.match_positional_variant(conn, variant_string)

    # displayName list
    variant = [i['displayName'] for i in matches]
    variant = sorted(list(set(variant)))

    print(f"\nvariant matches: {len(variant)}")
    for pv in variant:
        print(f'- {pv}')

    # # type list
    # types = [i.get('type', {}).get('displayName', '') for i in matches]
    # types = set(types)
    # types.discard('')
    # types = sorted(list(types))

    # print(f"\ntype matches: {len(types)}:")
    # for t in types:
    #     print(f'- {t}')
    # print()
