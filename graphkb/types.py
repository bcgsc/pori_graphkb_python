"""
Type annotations used for static type checking in this module
"""

from typing import Optional, Sequence, Union

try:
    from typing import TypedDict  # type: ignore
except ImportError:
    from typing_extensions import TypedDict

Record: TypedDict = TypedDict('Record', {'@rid': str, '@class': str})
EmbeddedRecord: TypedDict = TypedDict('EmbeddedRecord', {'@class': str})


class DataRecord(Record):
    displayName: str


class Ontology(DataRecord):
    sourceId: str
    name: str
    source: Record


class BasicPosition(EmbeddedRecord):
    pos: int


class CytobandPosition(EmbeddedRecord):
    arm: str
    majorBand: str
    minorBand: str


Position = Union[BasicPosition, CytobandPosition]


class Variant(DataRecord):
    reference1: Ontology
    reference2: Optional[Ontology]
    type: Ontology
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


class Statement(DataRecord):
    relevance: Ontology
    subject: Ontology
    conditions: Sequence[Ontology]
    evidence: Sequence[Ontology]
    evidenceLevel: Sequence[Ontology]
    source: Record
    sourceId: str
    displayNameTemplate: str
