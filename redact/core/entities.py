from dataclasses import dataclass
from enum import Enum


class EntityType(str, Enum):
    PERSON   = "PERSON"
    EMAIL    = "EMAIL"
    PHONE    = "PHONE"
    ORG      = "ORG"
    LOCATION = "LOCATION"
    CARD     = "CARD"
    SSN      = "SSN"
    DATE     = "DATE"


@dataclass
class Entity:
    type:   EntityType
    text:   str
    start:  int
    end:    int
    source: str  # "ner" | "llm" | "regex"


REPLACEMENT = {
    EntityType.PERSON:   "[NAME]",
    EntityType.EMAIL:    "[EMAIL]",
    EntityType.PHONE:    "[PHONE]",
    EntityType.ORG:      "[ORG]",
    EntityType.LOCATION: "[LOCATION]",
    EntityType.CARD:     "[CARD]",
    EntityType.SSN:      "[SSN]",
    EntityType.DATE:     "[DATE]",
}
