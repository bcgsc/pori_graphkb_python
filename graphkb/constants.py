from .types import CategoryBaseTermMapping

DEFAULT_LIMIT = 1000
DEFAULT_URL = 'https://graphkb-api.bcgsc.ca/api'

BASE_RETURN_PROPERTIES = [
    '@rid',
    '@class',
]

GENERIC_RETURN_PROPERTIES = [
    'name',
    'sourceId',
    'sourceIdVersion',
    'source.name',
    'source.@rid',
    'displayName',
    'deprecated',
] + BASE_RETURN_PROPERTIES

GENE_RETURN_PROPERTIES = ['biotype'] + GENERIC_RETURN_PROPERTIES


ONCOKB_SOURCE_NAME = 'oncokb'
ONCOGENE = 'oncogenic'
TUMOUR_SUPPRESSIVE = 'tumour suppressive'

FUSION_NAMES = ['structural variant', 'fusion']
BASE_THERAPEUTIC_TERMS = ['therapeutic efficacy', 'eligibility']
# the order here is the order these are applied, the first category matched is returned
RELEVANCE_BASE_TERMS: CategoryBaseTermMapping = [
    ('therapeutic', BASE_THERAPEUTIC_TERMS),
    ('diagnostic', ['diagnostic indicator']),
    ('prognostic', ['prognostic indicator']),
    ('pharmacogenomic', ['metabolism', 'toxicity', 'dosage']),
    ('cancer predisposition', ['pathogenic']),
    ('biological', ['functional effect', 'tumourigenesis', 'predisposing']),
]

AA_3to1_MAPPING = {
    'Ala': 'A',
    'Arg': 'R',
    'Asn': 'N',
    'Asp': 'D',
    'Asx': 'B',
    'Cys': 'C',
    'Glu': 'E',
    'Gln': 'Q',
    'Glx': 'Z',
    'Gly': 'G',
    'His': 'H',
    'Ile': 'I',
    'Leu': 'L',
    'Lys': 'K',
    'Met': 'M',
    'Phe': 'F',
    'Pro': 'P',
    'Ser': 'S',
    'Thr': 'T',
    'Trp': 'W',
    'Tyr': 'Y',
    'Val': 'V',
    'Ter': '*',
}
