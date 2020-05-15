"""
Type annotations used for static type checking in this module
"""

from typing import List, Optional, TypedDict, Union

Record = TypedDict('Record', {'@rid': str, '@class': str})
EmbeddedRecord = TypedDict('EmbeddedRecord', {'@class': str})

RecordLink = Union[str, Record]


class Ontology(Record):
    sourceId: str
    name: str
    source: RecordLink


OntologyLink = Union[str, Ontology]


class Position(EmbeddedRecord):
    pos: int


class CytobandPosition(EmbeddedRecord):
    arm: str
    majorBand: str
    minorBand: str


class VariantRecord(Record):
    reference1: OntologyLink
    reference2: Optional[OntologyLink]
    type: OntologyLink


class PostionalVariant(VariantRecord):
    break1Start: Union[Position, CytobandPosition]
    break1End: Optional[Union[Position, CytobandPosition]]
    break2Start: Optional[Union[Position, CytobandPosition]]
    break2End: Optional[Union[Position, CytobandPosition]]
    refSeq: Optional[str]
    untemplatedSeq: Optional[str]
    untemplatedSeqSize: Optional[int]


class Statement(Record):
    relevance: OntologyLink
    subject: OntologyLink
    conditions: List[OntologyLink]
    evidence: List[OntologyLink]
    evidenceLevel: List[OntologyLink]
    source: RecordLink
    sourceId: str
