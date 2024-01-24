from graphkb.match import get_equivalent_features

from script_conn import connection


def main():
    # CONNECTION
    ##############################################################
    env = 'dev'  # 'local' | 'dev' | 'staging' | 'prod'
    conn = connection(env)

    # DATA
    ##############################################################
    gene_is_source_id = False
    # gene_source = 'entrez gene'
    # gene_is_source_id = True
    # gene1 = 'EGFR'
    # gene1 = 'NP_001333828'
    # gene1 = 'NP_001333828.1'
    # gene1 = 'NM_001346899'
    # gene1 = 'NP_001333826.1'
    # gene1 = 'NM_001346897.2'
    # gene1 = '1956'; gene_is_source_id = True
    # gene1 = 'TERT';

    # SDEV-4080
    # gene1 = 'CHEK2';
    # gene1 = 'ENST00000404276';
    # gene1 = 'ENST00000404276.6';
    gene1 = 'NM_007194';

    # PROCESSING
    ##############################################################
    features = get_equivalent_features(
        conn,
        gene1,
        # source=gene_source,
        is_source_id=gene_is_source_id,
    )

    displayNames = [f['displayName'] for f in features]
    displayNames.sort()

    print(f'Equivalent features for {gene1} ({len(displayNames)}):')
    for displayName in displayNames:
        print('-', displayName)

    print(displayNames)

main()