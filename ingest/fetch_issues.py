"""Descarga issues cerrados de pandas-dev/pandas por etiqueta y los guarda en JSONL."""
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()  # lee el archivo .env y carga GITHUB_TOKEN como variable de entorno

API = "https://api.github.com"
REPO = "pandas-dev/pandas"
TARGET_LABELS = ["Bug", "Docs", "Enhancement", "Usage Question"]
PER_LABEL = 400  # máximo por etiqueta -> ~1.500 en total
OUTPUT = Path("data/raw/issues.jsonl")

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
})


def get(url, params=None):
    """GET con manejo de rate limit: si se agotan las consultas, espera y reintenta."""
    while True:
        r = session.get(url, params=params, timeout=30)
        if r.status_code in (403, 429):
            if r.headers.get("X-RateLimit-Remaining") == "0":
                wait = int(r.headers["X-RateLimit-Reset"]) - time.time() + 5
                print(f"Rate limit alcanzado. Esperando {wait:.0f} s...")
                time.sleep(max(wait, 0))
                continue
            if "Retry-After" in r.headers:  # límite secundario (demasiadas consultas seguidas)
                time.sleep(int(r.headers["Retry-After"]))
                continue
        r.raise_for_status()  # cualquier otro error (401 token malo, 404...) detiene el script
        return r


def fetch_label(label):
    """Recorre todas las páginas de issues cerrados con una etiqueta."""
    url = f"{API}/repos/{REPO}/issues"
    params = {"state": "closed", "labels": label, "per_page": 100}
    issues = []
    while url and len(issues) < PER_LABEL:
        r = get(url, params)
        for item in r.json():
            if "pull_request" in item:  # descartar PRs
                continue
            issues.append(item)
        url = r.links.get("next", {}).get("url")  # siguiente página o None
        params = None  # la URL "next" ya trae los parámetros
        print(f"  {label}: {len(issues)} issues | quedan {r.headers.get('X-RateLimit-Remaining')} consultas")
        time.sleep(0.5)  # ser amable con la API
    return issues[:PER_LABEL]


def to_record(item):
    """Deja solo los campos útiles del issue."""
    labels = [label["name"] for label in item["labels"]]
    targets = [target for target in labels if target in TARGET_LABELS]
    return {
        "number": item["number"],
        "title": item["title"],
        "body": item["body"] or "",  # algunos issues no tienen cuerpo (None)
        "labels": labels,
        "target_labels": targets,
        "url": item["html_url"],
        "created_at": item["created_at"],
        "closed_at": item["closed_at"],
    }


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    by_number = {}
    for label in TARGET_LABELS:
        print(f"Descargando '{label}'...")
        for item in fetch_label(label):
            by_number[item["number"]] = to_record(item)  # el dict evita duplicados entre etiquetas

    # quedarse solo con issues que tienen exactamente UNA etiqueta objetivo
    clean = [rec | {"label": rec["target_labels"][0]}for rec in by_number.values() if len(rec["target_labels"]) == 1]

    with OUTPUT.open("w", encoding="utf-8") as f:
        for rec in clean:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Guardados {len(clean)} issues en {OUTPUT} (descartados por ambigüedad: {len(by_number) - len(clean)})")


if __name__ == "__main__":
    main()