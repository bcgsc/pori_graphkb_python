import os

from graphkb import GraphKBConnection, constants, match  # , types, util, vocab
from graphkb.vocab import get_equivalent_terms, get_term_tree

# # Production
# GKB_API_URL: str = 'https://graphkb-api.bcgsc.ca/api'
# GKB_USER: str = os.environ['USER']
# GKB_PASSWORD: str = os.environ['JIRA_PASS']

# # Staging
# GKB_API_URL: str = 'https://graphkbstaging-api.bcgsc.ca/api'
# GKB_USER: str = 'graphkb_importer'
# GKB_PASSWORD: str = os.environ['GKB_PASS']

# Dev
GKB_API_URL: str = 'https://graphkbdev-api.bcgsc.ca/api'
GKB_USER: str = os.environ['USER']
GKB_PASSWORD: str = os.environ['JIRA_PASS']

# # Local
# GKB_API_URL: str = 'http://mlemieux01.phage.bcgsc.ca:8080/api/'
# GKB_USER: str = os.environ['USER']
# GKB_PASSWORD: str = os.environ['JIRA_PASS']

conn = GraphKBConnection(GKB_API_URL, use_global_cache=False)  # conn = GraphKBConnection()
conn.login(GKB_USER, GKB_PASSWORD)

variants = [
    ########################
    ## KBDEV-1038
    ########################
    # "FGFR4:p.N535K",
    # "EGFR:p.D942N",
    ########################
    ## KBDEV-1052
    ########################
    # "EGFR:c.28246G>A",
    # "chr7:g.55198839G>A",
    # "EGFR:p.D942N",
    # '(PCM1,JAK2):fusion(r.6280,r.1821)',  # dummy test for Infers edges
    ########################
    ## KBDEV-1054
    ########################
    # "ERBB2:p.R814C",
    ########################
    ## KBDEV-1056
    ########################
    "ENST00000340107:c.1212dupC",
    "ENST00000340107:c.1212dupACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT",
    "ENST00000340107:c.1212_1213insC",
    "ENST00000340107:c.1212C>A",
    "chr1:g.33344590_33344592del",
    "FGFR3:g.5000_5001del",
    "FGFR3:g.5000_5100del",
    "ENST00000340107:c.9002_9050delinsTTT",
    "ENST00000340107:c.9002_9051delinsTTT",
    ########################
    ## GERO-299
    ########################
    # "chr17:g.7674252C>T",
    # "ENST00000269305:c.711G>A",
    # "TP53:p.M237I",
    ########################
    ## KBDEV-1024
    ########################
    # "TSC2:c.3365G>C",
    # "NM_000548.5:c.3365G>A",
    # "NM_000548.5:p.Arg1122His",
    # "TSC2: p.R112H",
    ########################
    ## KBDEV-1044
    ########################
    # "TSC2:c.4700G>A",
    ########################
    ## OTHER Ex.
    ########################
    # "ENST00000219476:c.4700_4701delinsAT",
    # "NM_000548.5:c.3365G>A",
    # "TSC2:p.R112H",
    # "TSC2:p.G1567D",
    # "KRAS:p.G12D",
]

for variant_string in variants:

    # parsed = conn.parse(variant_string)
    # screened_type = match.get_type_screening(parsed)
    # print(variant_string)
    # print('\t', screened_type)

    # match_positional_variant()


    matches = match.match_positional_variant(conn, variant_string)

    variant = [i['displayName'] for i in matches]
    variant = sorted(list(set(variant)))
    types = [i.get('type', {}).get('displayName', '') for i in matches]
    types = sorted(list(set(types)))

    print('=' * 50)
    print(variant_string)
    print(f"\nvariant matches ({len(variant)}):")
    for pv in variant:
        print(pv)
    print(f"\ntype matches ({len(types)}):")
    for t in types:
        if t != '':
            print(t)
