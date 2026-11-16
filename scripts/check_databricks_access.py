# Test the connection to Databricks through a GET request.

import os

import requests

host = os.environ["DATABRICKS_HOST"].strip()
token = os.environ["DATABRICKS_TOKEN"].strip()

URL = f"{host}/api/2.0/fs/directories/Volumes/nightride/landing/tfnsw/"


resp = requests.get(URL, headers={"Authorization": f"Bearer {token}"}, timeout=30)


print("Status:", resp.status_code, "Response:", resp.text)
