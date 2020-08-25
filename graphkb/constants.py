from .types import CategoryBaseTermMapping

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

BASE_THERAPEUTIC_TERMS = ['therapeutic efficacy', 'eligibility']
# the order here is the order these are applied, the first category matched is returned
RELEVANCE_BASE_TERMS: CategoryBaseTermMapping = [
    ('therapeutic', BASE_THERAPEUTIC_TERMS),
    # ('pharmacogenomic', ['metabolism', 'toxicity', 'dosage']) TODO: add when new pharmacogenomic section ready,
    ('diagnostic', ['diagnostic indicator']),
    ('prognostic', ['prognostic indicator']),
    ('biological', ['functional effect', 'tumourigenesis', 'predisposing']),
]
