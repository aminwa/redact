from .entities import Entity, EntityType, REPLACEMENT


def _dedup(entities: list[Entity]) -> list[Entity]:
    sorted_ents = sorted(entities, key=lambda e: (e.start, -(e.end - e.start)))
    result: list[Entity] = []
    last_end = -1
    for e in sorted_ents:
        if e.start >= last_end:
            result.append(e)
            last_end = e.end
    return result


def redact(text: str, entities: list[Entity], style: str = "label") -> str:
    deduped = _dedup(sorted(entities, key=lambda e: e.start))
    parts: list[str] = []
    pos = 0
    for e in deduped:
        parts.append(text[pos:e.start])
        if style == "block":
            parts.append("█" * len(e.text))
        else:
            parts.append(REPLACEMENT.get(e.type, f"[{e.type.value}]"))
        pos = e.end
    parts.append(text[pos:])
    return "".join(parts)


def compare(
    ner_entities: list[Entity],
    llm_entities: list[Entity],
    overlap_chars: int = 5,
) -> dict[str, list[Entity]]:
    def overlaps(a: Entity, b_list: list[Entity]) -> bool:
        return any(abs(a.start - b.start) <= overlap_chars for b in b_list)

    return {
        "both":     [e for e in ner_entities if overlaps(e, llm_entities)],
        "ner_only": [e for e in ner_entities if not overlaps(e, llm_entities)],
        "llm_only": [e for e in llm_entities if not overlaps(e, ner_entities)],
    }
