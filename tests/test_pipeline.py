from redact.core.entities import Entity, EntityType
from redact.core.pipeline import redact, compare, _dedup


def _e(etype, text, start, end, source="ner"):
    return Entity(type=etype, text=text, start=start, end=end, source=source)


def test_redact_label():
    text = "Contact john@example.com for details"
    entities = [_e(EntityType.EMAIL, "john@example.com", 8, 24)]
    assert redact(text, entities) == "Contact [EMAIL] for details"


def test_redact_block():
    text = "Call 555-867-5309"
    entities = [_e(EntityType.PHONE, "555-867-5309", 5, 17)]
    result = redact(text, entities, style="block")
    assert "█" in result
    assert "555" not in result


def test_redact_multiple():
    text = "Alice emailed bob@test.com"
    entities = [
        _e(EntityType.PERSON, "Alice", 0, 5),
        _e(EntityType.EMAIL,  "bob@test.com", 14, 26),
    ]
    result = redact(text, entities)
    assert "[NAME]" in result
    assert "[EMAIL]" in result
    assert "Alice" not in result


def test_redact_overlapping_spans():
    text = "John Smith works here"
    entities = [
        _e(EntityType.PERSON, "John Smith", 0, 10),
        _e(EntityType.PERSON, "John",       0, 4),
    ]
    result = redact(text, entities)
    assert result.count("[NAME]") == 1


def test_dedup_prefers_longer():
    a = _e(EntityType.PERSON, "John Smith", 0, 10)
    b = _e(EntityType.PERSON, "John",       0, 4)
    result = _dedup([a, b])
    assert len(result) == 1
    assert result[0].text == "John Smith"


def test_compare_both():
    ner = [_e(EntityType.EMAIL, "a@b.com", 0, 7)]
    llm = [_e(EntityType.EMAIL, "a@b.com", 0, 7, source="llm")]
    result = compare(ner, llm)
    assert len(result["both"]) == 1
    assert len(result["ner_only"]) == 0
    assert len(result["llm_only"]) == 0


def test_compare_ner_only():
    ner = [_e(EntityType.PERSON, "Alice", 0, 5)]
    llm = [_e(EntityType.EMAIL,  "x@y.com", 20, 27, source="llm")]
    result = compare(ner, llm)
    assert len(result["ner_only"]) == 1
    assert len(result["llm_only"]) == 1


def test_redact_empty():
    assert redact("hello world", []) == "hello world"


def test_redact_full_text():
    text = "SSN: 123-45-6789"
    entities = [_e(EntityType.SSN, "123-45-6789", 5, 16)]
    assert redact(text, entities) == "SSN: [SSN]"
