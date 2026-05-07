import re
import spacy
from .entities import Entity, EntityType

_SPACY_LABEL_MAP = {
    "PERSON": EntityType.PERSON,
    "ORG":    EntityType.ORG,
    "GPE":    EntityType.LOCATION,
    "LOC":    EntityType.LOCATION,
    "DATE":   EntityType.DATE,
}

_REGEX_PATTERNS: list[tuple[EntityType, re.Pattern]] = [
    (EntityType.EMAIL, re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
    (EntityType.SSN,   re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    (EntityType.PHONE, re.compile(r"\b(?:\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b")),
    (EntityType.CARD,  re.compile(r"\b(?:\d[ \-]?){13,18}\d\b")),
]

_nlp_cache: dict[str, spacy.language.Language] = {}


def _nlp(model: str) -> spacy.language.Language:
    if model not in _nlp_cache:
        _nlp_cache[model] = spacy.load(model, disable=["textcat"])
    return _nlp_cache[model]


class NEREngine:
    def __init__(self, model: str = "en_core_web_sm"):
        self._model = model

    def extract(self, text: str) -> list[Entity]:
        doc = _nlp(self._model)(text)
        entities: list[Entity] = []

        for ent in doc.ents:
            etype = _SPACY_LABEL_MAP.get(ent.label_)
            if etype:
                entities.append(Entity(
                    type=etype,
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    source="ner",
                ))

        for etype, pat in _REGEX_PATTERNS:
            for m in pat.finditer(text):
                entities.append(Entity(
                    type=etype,
                    text=m.group(0),
                    start=m.start(),
                    end=m.end(),
                    source="regex",
                ))

        return entities
