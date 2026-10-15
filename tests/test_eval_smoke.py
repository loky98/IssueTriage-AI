import asyncio
import json

import pytest

pytestmark = pytest.mark.eval  # no corre por defecto; tiene costo


def test_agent_classifies_real_issues():
    from app.agent import triage
    issues = [json.loads(line) for line in open("evals/dataset.jsonl", encoding="utf-8")][:5]

    async def run_all():  # un solo event loop para todos los issues
        results = [await triage(i["title"], i["body"][:1500]) for i in issues]
        return sum(r["result"].label == i["label"] for r, i in zip(results, issues))

    assert asyncio.run(run_all()) >= 3