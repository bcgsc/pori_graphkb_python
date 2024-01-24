from graphkb import match
from script_conn import connection
from script_data import variant_strings

# CONNECTION
##############################################################
env = "dev"  # 'local' | 'dev' | 'staging' | 'prod'
conn = connection(env)


# DATA
##############################################################
# variant_string_list = variant_strings.get("KBDEV-1052", {})
variant_string_list = variant_strings.get("KBDEV-1133", {})  # type filtering
# variant_string_list = variant_strings.get("KBDEV-1056", {})  # structural variant
# variant_string_list = variant_strings.get("MatchingUpdate", {})
##############################################################

# variant_string_list = []
# for k in variant_strings.keys():
#     variant_string_list.extend(variant_strings[k])

for variant_string in variant_string_list:
    print(f"{'='*50}\n{variant_string}")
    matches = match.match_positional_variant(conn, variant_string)

    variants = [i["displayName"] for i in matches]
    variants = sorted(list(set(variants)))

    print(f"\nvariants matches : {len(variants)}")
    for pv in variants:
        print(f"- {pv}")
