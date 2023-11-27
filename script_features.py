from graphkb.match import get_equivalent_features

from script_conn import connection


def main():
    # CONNECTION
    ##############################################################
    env = 'dev'  # 'local' | 'dev' | 'staging' | 'prod'
    conn = connection(env)

    # DATA
    ##############################################################
    source_name = 'entrez gene'
    gene_name = 'H3F3B'

    # PROCESSING
    ##############################################################
    features = get_equivalent_features(conn, gene_name)

    source_rid = conn.get_source(source_name)['@rid']
    features = [el for el in features if el['source'] == source_rid]

    if len(features) == 1:
        return features[0]

main()