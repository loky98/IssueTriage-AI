"""Guardrails de entrada y salida del agente."""
import re

MAX_BODY_CHARS = 6000
ALLOWED_TOOLS = {"search_github_issues", "get_issue", "run_snippet"}
DOMAIN_TERMS = re.compile(
    r"\bpd\.|\b(pandas|dataframe|series|groupby|read_csv|dtype|index|numpy|merge|pivot|to_datetime)\b", re.I)
PII_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<EMAIL>"),
    (re.compile(r"\b(ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{20,}"), "<GITHUB_TOKEN>"),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"), "<API_KEY>"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<AWS_KEY>"),
]
ISSUE_REF = re.compile(r"#(\d{3,6})\b")


class GuardrailError(ValueError):
    """Entrada rechazada por un guardrail."""


def mask_pii(text):
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def check_input(title, body):
    """Rechaza entradas fuera de dominio; recorta y enmascara datos sensibles."""
    if not DOMAIN_TERMS.search(f"{title}\n{body}"):
        raise GuardrailError("Out of domain: the issue does not look related to pandas")
    return mask_pii(title), mask_pii(body[:MAX_BODY_CHARS])


def unverified_issue_refs(reply, evidence):
    """Números de issue citados en la respuesta que no aparecen en la evidencia."""
    return [n for n in ISSUE_REF.findall(reply) if f"#{n}" not in evidence and f"/issues/{n}" not in evidence]