"""
Methods for retrieving gene annotation lists from GraphKB
"""

ONCOKB_SOURCE_NAME = 'oncokb'
ONCOGENE = 'oncogenic'
TUMOUR_SUPPRESSIVE = 'tumour suppressive'

FUSION_NAMES = ['structural variant', 'fusion']

GENE_RETURN_PROPERTIES = [
    'name',
    '@rid',
    '@class',
    'sourceId',
    'sourceIdVersion',
    'source.name',
    'displayName',
    'biotype',
]


def get_oncokb_gene_list(conn, relevance):
    source = conn.get_source(ONCOKB_SOURCE_NAME)['@rid']

    statements = conn.query(
        {
            'target': 'Statement',
            'filters': [
                {'source': source},
                {'relevance': {'target': 'Vocabulary', 'filters': {'name': relevance}}},
            ],
            'returnProperties': [f'subject.{prop}' for prop in GENE_RETURN_PROPERTIES],
        },
        ignore_cache=False,
    )
    genes = {}

    for statement in statements:
        if statement['subject']['biotype'] == 'gene':
            record_id = statement['subject']['@rid']
            genes[record_id] = statement['subject']

    return genes.values()


def get_oncokb_oncogenes(conn):
    """
    Gets the list of oncogenes stored in GraphKB derived from OncoKB
    """
    return get_oncokb_gene_list(conn, ONCOGENE)


def get_oncokb_tumour_supressors(conn):
    """
    Gets the list of tumour supressor genes stored in GraphKB derived from OncoKB
    """
    return get_oncokb_gene_list(conn, TUMOUR_SUPPRESSIVE)


def get_genes_in_fusions(conn):
    """
    Get a list of Genes involved in Fusion/Structural Variants
    """
    variants = conn.query(
        {
            'target': 'Variant',
            'filters': [
                {
                    'type': {
                        'target': 'Vocabulary',
                        'filters': {'name': FUSION_NAMES, 'operator': 'IN'},
                    }
                }
            ],
            'returnProperties': ['reference1', 'reference2'],
        },
    )

    genes = set()

    for variant in variants:
        genes.add(variant['reference1'])

        if variant['reference2']:
            genes.add(variant['reference2'])

    return conn.query(
        {
            'target': list(genes),
            'returnProperties': GENE_RETURN_PROPERTIES,
            'filters': {'biotype': 'gene'},
        }
    )
