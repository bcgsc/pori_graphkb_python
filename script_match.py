from graphkb import match
from script_conn import connection
from script_data import variant_strings

# CONNECTION
##############################################################
env = "dev"  # 'local' | 'dev' | 'staging' | 'prod'
conn = connection(env)

# DATA
##############################################################
variant_string_list = variant_strings.get('KBDEV-1133', {})  # type filtering
# variant_string_list = variant_strings.get("KBDEV-1056", {})  # structural variant


for variant_string in variant_string_list:
    print(f"{'='*50}\n{variant_string}")

    # # PARSING ONLY
    # ##############################################################
    # parsed = conn.parse(variant_string)

    # MATCHING
    ##############################################################
    matches = match.match_positional_variant(
        conn,
        variant_string,
        # delinsSpecialHandling=False,
        # updateTypeList=True,
    )

    variants = matches
    # variants = [i["displayName"] for i in matches]
    # variants = sorted(list(set(variants)))

    print(f"\nvariants matches: {len(variants)}")
    for pv in variants:
        print(f"\n- {pv}")

    # types = [i["type"] for i in matches]
    # types = set()
