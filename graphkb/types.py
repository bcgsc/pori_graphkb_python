"""
Type annotations used for static type checking in this module
"""

from typing import List, Optional, Union

try:
    from typing import TypedDict  # type: ignore
except ImportError:
    from typing_extensions import TypedDict

Record: TypedDict = TypedDict('Record', {'@rid': str, '@class': str})
EmbeddedRecord: TypedDict = TypedDict('EmbeddedRecord', {'@class': str})

RecordLink = Union[str, Record]


class Ontology(Record):
    sourceId: str
    name: str
    source: RecordLink


OntologyLink = Union[str, Ontology]


class BasicPosition(EmbeddedRecord):
    pos: int


class CytobandPosition(EmbeddedRecord):
    arm: str
    majorBand: str
    minorBand: str


Position = Union[BasicPosition, CytobandPosition]


class Variant(Record):
    reference1: OntologyLink
    reference2: Optional[OntologyLink]
    type: OntologyLink
    zygosity: str
    germline: bool


class PositionalVariant(Variant):
    break1Start: Union[Position, CytobandPosition]
    break1End: Optional[Union[Position, CytobandPosition]]
    break2Start: Optional[Union[Position, CytobandPosition]]
    break2End: Optional[Union[Position, CytobandPosition]]
    refSeq: Optional[str]
    untemplatedSeq: Optional[str]
    untemplatedSeqSize: Optional[int]


class ParsedVariant(TypedDict):
    reference1: str
    reference2: Optional[str]
    type: str
    zygosity: str
    germline: bool
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
