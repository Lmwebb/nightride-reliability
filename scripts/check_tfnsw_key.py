# Test the connection to TfNSW api through a GET request.

import os

import requests

URL = "https://api.transport.nsw.gov.au/v1/gtfs/realtime/buses"
key = os.environ["TFNSW_API_KEY"]

resp = requests.get(URL, headers={"Authorization": f"apikey {key}"}, timeout=30)

print("Status:", resp.status_code)
print("Content-Type:", resp.headers.get("Content-Type"))
print("Bytes:", len(resp.content))