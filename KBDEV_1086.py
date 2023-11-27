from graphkb.vocab import (
    get_equivalent_terms,   # similar terms or parents
    get_term_by_name,       # return 1 vocab record
    get_term_tree,          # similar terms, parents or children
    get_terms_set,          # similar terms or children? Only RIDs
)
from script_conn import connection

# CONNECTION
##############################################################
env = 'dev'  # 'local' | 'dev' | 'staging' | 'prod'
conn = connection(env)

# INITIAL DATA
##############################################################
name = 'copy variant'

# QUERY
##############################################################
termTree = get_term_tree(conn, name)
equiTerms = get_equivalent_terms(conn, name)
termsSet = get_terms_set(conn, name)
terms = get_term_by_name(conn, name)

# LOGGING
##############################################################
for term in termTree:
    print(term)
print()
for term in equiTerms:
    print(term)
print()
for term in termsSet:
    print(term)
print()
print(terms)

