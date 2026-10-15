import pytest
from pydantic import ValidationError

from app.schemas import TriageResult

BASE = {"reasoning": "r", "label": "Bug", "suggested_reply": "x", "needs_human": False}


def test_percentage_confidence_is_normalized():
    assert TriageResult(**BASE, confidence=95).confidence == 0.95


def test_invalid_label_is_rejected():
    with pytest.raises(ValidationError):
        TriageResult(**{**BASE, "label": "Question"}, confidence=0.5)