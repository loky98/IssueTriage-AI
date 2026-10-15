"""Servidor MCP con herramientas para triage de issues de pandas."""
import os
import re
import subprocess
import sys

from mcp.server.fastmcp import FastMCP

from ingest.fetch_issues import API, REPO, get

mcp = FastMCP("issuetriage-tools", host="0.0.0.0", port=8001)


BLOCKED = re.compile(r"\b(os|subprocess|shutil|socket|requests|urllib|ctypes)\b|__import__|\beval\(|\bexec\(")


@mcp.tool()
def search_github_issues(query: str, limit: int = 5) -> list[dict]:
    """Busca issues en GitHub del repo pandas-dev/pandas que coincidan con el texto."""
    r = get(f"{API}/search/issues", {"q": f"{query} repo:{REPO} is:issue", "per_page": limit})
    return [{"number": i["number"], "title": i["title"], "state": i["state"], "url": i["html_url"]}
            for i in r.json()["items"]]


@mcp.tool()
def get_issue(number: int) -> dict:
    """Obtiene título, estado, etiquetas y cuerpo de un issue de pandas por su número."""
    i = get(f"{API}/repos/{REPO}/issues/{number}").json()
    return {"number": i["number"], "title": i["title"], "state": i["state"],
            "labels": [label["name"] for label in i["labels"]],
            "body": (i["body"] or "")[:3000], "url": i["html_url"]}


@mcp.tool()
def run_snippet(code: str) -> dict:
    if BLOCKED.search(code):
        return {"error": "blocked: code uses system/network modules"}
    """Ejecuta un fragmento de código Python/pandas (máx. 30 s) y devuelve su salida o error."""
    try:
        p = subprocess.run(
            [sys.executable, "-I", "-c", code],stdin=subprocess.DEVNULL,capture_output=True, text=True, timeout=30)
        return {"stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:], "returncode": p.returncode}
    except subprocess.TimeoutExpired:
        return {"error": "timeout (30 s)"}


if __name__ == "__main__":
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))  # en Docker: streamable-http