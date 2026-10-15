import os

import requests
from dotenv import load_dotenv

load_dotenv()
URL = "http://127.0.0.1:8000"
KEY = os.getenv("API_KEYS").split(",")[0]
issue = {"title": "read_csv ignores sep=';'",
        "body": "```python\nimport pandas as pd, io\n"
                "print(pd.read_csv(io.StringIO('a;b\\n1;2'), sep=';').shape)\n```\n"
                "I expected 2 columns but got 1."}

print("health sin clave:", requests.get(f"{URL}/health").status_code)                     # 200
print("triage sin clave:", requests.post(f"{URL}/triage", json=issue).status_code)       # 401
print("triage clave falsa:", requests.post(f"{URL}/triage", json=issue,
                                        headers={"X-API-Key": "falsa"}).status_code)   # 401
codes = [requests.post(f"{URL}/triage", json=issue, headers={"X-API-Key": KEY}).status_code
        for _ in range(12)]
print("12 peticiones válidas:", codes)                                                   # 10×200, 2×429