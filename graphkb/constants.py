import argparse

from .types import CategoryBaseTermMapping

DEFAULT_LIMIT = 1000

GKB_BASE_URL = "https://graphkb-api.bcgsc.ca/api"
GKB_STAGING_URL = "https://graphkbstaging-api.bcgsc.ca/api"
GKB_DEV_URL = "https://graphkbdev-api.bcgsc.ca/api"
DEFAULT_URL = GKB_BASE_URL


BASE_RETURN_PROPERTIES = ['@rid', '@class']

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

VARIANT_RETURN_PROPERTIES = (
    BASE_RETURN_PROPERTIES
    + [f'type.{p}' for p in GENERIC_RETURN_PROPERTIES]
    + [f'reference1.{p}' for p in GENE_RETURN_PROPERTIES]
    + [f'reference2.{p}' for p in GENE_RETURN_PROPERTIES]
    + ['zygosity', 'germline', 'displayName']
)

POS_VARIANT_RETURN_PROPERTIES = VARIANT_RETURN_PROPERTIES + [
    'break1Start',
    'break1End',
    'break2Start',
    'break2End',
    'break1Repr',
    'break2Repr',
    'refSeq',
    'untemplatedSeq',
    'untemplatedSeqSize',
    'truncation',
    'assembly',
]

STATEMENT_RETURN_PROPERTIES = (
    BASE_RETURN_PROPERTIES
    + ['displayNameTemplate', 'sourceId', 'source.name', 'source.displayName']
    + [f'conditions.{p}' for p in GENERIC_RETURN_PROPERTIES]
    + [f'subject.{p}' for p in GENERIC_RETURN_PROPERTIES]
    + [f'evidence.{p}' for p in GENERIC_RETURN_PROPERTIES]
    + [f'relevance.{p}' for p in GENERIC_RETURN_PROPERTIES]
    + [f'evidenceLevel.{p}' for p in GENERIC_RETURN_PROPERTIES]
    + ['reviewStatus']
)


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

AMBIGUOUS_AA = ['x', '?', 'X']
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


class IterableNamespace(argparse.Namespace):
    def __init__(self, *pos, **kwargs):
        argparse.Namespace.__init__(self, *pos, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()

    def values(self):
        return self.__dict__.values()

    def __getitem__(self, key):
        return getattr(self, key)


INPUT_COPY_CATEGORIES = IterableNamespace(
    AMP='amplification',
    ANY_GAIN='copy gain',
    ANY_LOSS='copy loss',
    DEEP='deep deletion',
    GAIN='low level copy gain',
    LOSS='shallow deletion',
)
INPUT_EXPRESSION_CATEGORIES = IterableNamespace(
    UP='increased expression', DOWN='reduced expression'
)
