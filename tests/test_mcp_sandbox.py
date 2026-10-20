from mcp_server.server import _run_isolated, run_snippet


def test_snippet_does_not_see_parent_secrets(monkeypatch):
    monkeypatch.setenv("FAKE_SECRET", "s3cr3t")
    p = _run_isolated("import importlib; print(importlib.import_module('os').environ.get('FAKE_SECRET'))")
    assert p.returncode == 0, p.stderr
    assert p.stdout.strip() == "None"


def test_pandas_still_imports_in_isolated_env():
    out = run_snippet("import pandas as pd; print(pd.DataFrame({'a': [1, 2]}).a.sum())")
    assert out["returncode"] == 0, out["stderr"]
    assert out["stdout"].strip() == "3"


def test_blocked_modules_are_rejected():
    assert "error" in run_snippet("import os")
