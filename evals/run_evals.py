"""Evalúa la clasificación del agente sobre los issues reservados (evals/dataset.jsonl)."""
import argparse
import asyncio
import json
import os
import time
from collections import defaultdict
from datetime import date
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from app.agent import LLM, build_graph, flush_tracing, mcp_connection, triage

LABELS = ["Bug", "Docs", "Enhancement", "Usage Question"]


def clean_body(body):
    return (body or "").split("### Installed Versions")[0][:1500]  # sin el bloque de versiones


def sample(issues, per_label):
    if not per_label:
        return issues
    by_label = defaultdict(list)
    for it in issues:
        by_label[it["label"]].append(it)
    return [it for label in LABELS for it in by_label[label][:per_label]]


def report(path, name):
    all_recs = [json.loads(line) for line in path.open(encoding="utf-8")]
    last = list({r["number"]: r for r in all_recs}.values())  # último intento por issue
    recs = [r for r in last if r["pred"] != "ERROR"]
    errors = len(last) - len(recs)
    if not recs:
        print("Sin resultados válidos todavía.")
        return
    y, p = [r["label"] for r in recs], [r["pred"] for r in recs]
    md = [f"# Eval clasificación: {name} ({date.today()})", "",
        f"- Issues evaluados: {len(recs)} (errores técnicos excluidos: {errors})",
        f"- Accuracy: {accuracy_score(y, p):.2%}",
        f"- F1 macro: {f1_score(y, p, labels=LABELS, average='macro', zero_division=0):.3f}",
        f"- needs_human: {sum(r['needs_human'] for r in recs) / len(recs):.1%}",
        f"- Latencia media: {sum(r['seconds'] for r in recs) / len(recs):.1f} s",
        "", "## Matriz de confusión (filas = real, columnas = predicción)",
        "```", "orden: " + ", ".join(LABELS),
        str(confusion_matrix(y, p, labels=LABELS)), "```", "",
        "```", classification_report(y, p, labels=LABELS, zero_division=0), "```"]
    path.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


async def main(args):
    os.environ["ENABLE_REPRODUCE"] = args.reproduce
    model = LLM.model.replace(":", "-")
    name = f"{model}_{args.prompt}_repro{args.reproduce}_n{args.per_label or 'all'}"
    path = Path(f"evals/results/run_{name}.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if path.exists():  # permite reanudar; los ERROR se vuelven a intentar
        done = {json.loads(line)["number"] for line in path.open(encoding="utf-8")
                if json.loads(line)["pred"] != "ERROR"}

    issues = sample([json.loads(line) for line in open("evals/dataset.jsonl", encoding="utf-8")], args.per_label)
    client = MultiServerMCPClient(mcp_connection())
    graph = build_graph(await client.get_tools())

    with path.open("a", encoding="utf-8") as f:
        for i, it in enumerate(issues, 1):
            if it["number"] in done:
                continue
            t = time.time()
            try:
                out = await triage(it["title"], clean_body(it["body"]),
                                prompt_version=args.prompt, graph=graph)
                pred, needs_human = out["result"].label, out["result"].needs_human
            except Exception as e:  # un error no detiene la evaluación
                pred, needs_human = "ERROR", True
                print(f"  error en #{it['number']}: {e}")
            rec = {"number": it["number"], "label": it["label"], "pred": pred,
                "needs_human": needs_human, "seconds": round(time.time() - t, 1)}
            f.write(json.dumps(rec) + "\n")
            f.flush()
            print(f"{i}/{len(issues)} #{it['number']} real={it['label']} pred={pred} ({rec['seconds']}s)",
                flush=True)
    flush_tracing()
    report(path, name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default="v2")
    parser.add_argument("--reproduce", default="1", choices=["0", "1"])
    parser.add_argument("--per-label", type=int, default=10, help="issues por etiqueta; 0 = todos")
    asyncio.run(main(parser.parse_args()))