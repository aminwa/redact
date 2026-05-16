import pytest
from redact.core.ner import NEREngine
from redact.core.entities import EntityType

_ner = NEREngine()


def test_email_detection():
    ents = _ner.extract("reach me at hello@example.com anytime")
    assert any(e.type == EntityType.EMAIL for e in ents)


def test_ssn_detection():
    ents = _ner.extract("SSN: 123-45-6789")
    assert any(e.type == EntityType.SSN for e in ents)


def test_phone_detection():
    ents = _ner.extract("call me on 415-555-1234")
    assert any(e.type == EntityType.PHONE for e in ents)


def test_no_false_positive_on_clean_text():
    ents = _ner.extract("the weather today is quite nice")
    email_ents = [e for e in ents if e.type == EntityType.EMAIL]
    ssn_ents   = [e for e in ents if e.type == EntityType.SSN]
    assert len(email_ents) == 0
    assert len(ssn_ents) == 0


def test_entity_has_correct_offsets():
    text = "email: test@domain.com done"
    ents = _ner.extract(text)
    email = next(e for e in ents if e.type == EntityType.EMAIL)
    assert text[email.start:email.end] == email.text


def test_multiple_emails():
    text = "a@x.com and b@y.com"
    ents = _ner.extract(text)
    emails = [e for e in ents if e.type == EntityType.EMAIL]
    assert len(emails) == 2
