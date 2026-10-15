import pytest

from app.guardrails import GuardrailError, check_input, mask_pii, unverified_issue_refs


def test_mask_pii_hides_email_and_tokens():
    text = mask_pii("mail me at a.b@example.com token ghp_" + "x" * 36)
    assert "<EMAIL>" in text and "<GITHUB_TOKEN>" in text
    assert "example.com" not in text


def test_out_of_domain_is_rejected():
    with pytest.raises(GuardrailError):
        check_input("My car won't start", "engine noise")


def test_pandas_issue_is_accepted_and_truncated():
    title, body = check_input("read_csv bug", "pd.read_csv " + "x" * 10_000)
    assert title == "read_csv bug" and len(body) == 6000


def test_unverified_issue_refs():
    assert unverified_issue_refs("see #123 and #456", "context mentions #123") == ["456"]