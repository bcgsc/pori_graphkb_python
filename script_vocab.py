from graphkb.vocab import get_equivalent_terms, get_term_tree, get_terms_set
from script_conn import connection

# CONNECTION
##############################################################
env = "dev"  # 'local' | 'dev' | 'staging' | 'prod'
conn = connection(env)

# term = "frameshift mutation"
term = "deletion"
print("term:", term)

# # get_term_tree
# terms = get_term_tree(conn, term)
# print("\nget_terms_tree", "\n#############################################")
# print(f"\nterms: {len(terms)}", "\n**************************")
# for t in terms:
#     print(t["@rid"], t["name"])

# get_equivalent_terms
terms2 = get_equivalent_terms(conn, term)
print("\nget_equivalent_terms", "\n#############################################")
print(f"\nterms: {len(terms2)}", "\n**************************")
for t in terms2:
    print(t["@rid"], t["name"])

# # get_terms_set
# terms3 = get_terms_set(conn, [term])
# print("\nget_terms_set", "\n#############################################")
# print(f"\nterms: {len(terms3)}", "\n**************************")
# for t in terms3:
#     print(t)

# # get_term_tree wo/ supercvlasses
# terms4 = get_term_tree(conn, [term], include_superclasses=False)
# print("\nget_term_tree wo superclasses", "\n#############################################")
# print(f"\nterms: {len(terms4)}", "\n**************************")
# for t in terms4:
#     print(t["@rid"], t["name"])
