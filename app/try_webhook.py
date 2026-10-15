import hashlib
import hmac
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
URL = "http://127.0.0.1:8000/webhooks/github"
payload = json.dumps({"action": "opened", "issue": {
    "number": 999999, "title": "DataFrame.merge loses index name",
    "body": "```python\nimport pandas as pd\na=pd.DataFrame({'k':[1]}).rename_axis('idx')\n"
            "print(a.merge(a, on='k').index.name)\n```\nExpected 'idx'."}}).encode()
sig = "sha256=" + hmac.new(os.getenv("GITHUB_WEBHOOK_SECRET").encode(), payload, hashlib.sha256).hexdigest()
headers = {"Content-Type": "application/json", "X-GitHub-Event": "issues"}

r = requests.post(URL, data=payload, headers={**headers, "X-Hub-Signature-256": sig})
print("Firma válida:", r.status_code, r.json())    # 202 accepted
r = requests.post(URL, data=payload, headers={**headers, "X-Hub-Signature-256": "sha256=falsa"})
print("Firma falsa:", r.status_code, r.json())     # 401