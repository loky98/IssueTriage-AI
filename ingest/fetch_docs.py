"""Convierte la guía de usuario de pandas (.rst) en secciones de texto limpio (JSONL)."""
import json
import re
from pathlib import Path

SRC = Path("data/raw/pandas-repo/doc/source/user_guide")
OUTPUT = Path("data/processed/docs.jsonl")
DOCS_URL = "https://pandas.pydata.org/docs/user_guide/{page}.html"
MIN_CHARS = 200  # secciones más cortas no aportan contexto útil

UNDERLINE = re.compile(r'^([=\-~^"*+#`])\1{2,}\s*$')  # líneas tipo ===== o -----


def clean_rst(text):
    """Quita la sintaxis de reStructuredText y deja texto legible."""
    text = text.replace("{{ header }}", "")
    # :func:`~pandas.read_csv` -> pandas.read_csv ;  :ref:`texto <etiqueta>` -> texto
    text = re.sub(r":[\w:]+:`~?([^`<]+?)(?:\s*<[^>]+>)?`", r"\1", text)
    # `texto <https://...>`_ -> texto
    text = re.sub(r"`([^`<]+?)\s*<[^>]+>`_+", r"\1", text)
    # ``codigo`` -> codigo
    text = re.sub(r"``([^`]+)``", r"\1", text)
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(".. _") or stripped.startswith(".. currentmodule"):
            continue  # anclas internas y directivas sin contenido
        if stripped.startswith(".. "):
            continue  # línea de directiva (.. ipython:: python, .. note::); su contenido indentado se conserva
        if re.match(r"^\s+:[\w-]+:", line):
            continue  # opciones de directiva como :suppress:
        lines.append(line.rstrip())
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()  # colapsar líneas en blanco


def split_sections(raw):
    """Divide el .rst por títulos. Un título es una línea seguida de una línea de ====/----."""
    lines = raw.splitlines()
    sections, title, buffer = [], "Introducción", []
    i = 0
    while i < len(lines):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if line.strip() and not UNDERLINE.match(line) and UNDERLINE.match(nxt):
            sections.append((title, "\n".join(buffer)))  # cerrar la sección anterior
            title, buffer = line.strip(), []
            i += 2  # saltar título + subrayado
            continue
        if not UNDERLINE.match(line):  # descartar sobrelíneas sueltas
            buffer.append(line)
        i += 1
    sections.append((title, "\n".join(buffer)))
    return sections


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with OUTPUT.open("w", encoding="utf-8") as f:
        for path in sorted(SRC.glob("*.rst")):
            raw = path.read_text(encoding="utf-8")
            for title, body in split_sections(raw):
                text = clean_rst(body)
                if len(text) < MIN_CHARS:
                    continue
                f.write(json.dumps({
                    "source": f"user_guide/{path.name}",
                    "section": clean_rst(title),
                    "url": DOCS_URL.format(page=path.stem),
                    "text": text,
                }, ensure_ascii=False) + "\n")
                count += 1
    print(f"Guardadas {count} secciones en {OUTPUT}")


if __name__ == "__main__":
    main()