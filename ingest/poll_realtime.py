import os
import gzip
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from google.protobuf.json_format import MessageToDict
from google.transit import gtfs_realtime_pb2

URL = "https://api.transport.nsw.gov.au/v1/gtfs/realtime/buses"
OUTPUT_DIR = Path("samples")
VOLUME_ROOT = "/Volumes/nightride/landing/tfnsw"
TEST_ROUTE_ID = os.environ.get("TEST_ROUTE_ID", "")

def is_nightride(route_id):
	# Analyses the route_id string, to determine if it's a night route.
	route_part = route_id.split("_")[-1]
	return route_part.startswith("N") and len(route_part) >= 2 and route_part[1].isdigit()

def keep(route_id):
	# Run a check for a test route id otherwise runs is_nightride.
	if TEST_ROUTE_ID:
		return route_id == TEST_ROUTE_ID
	return is_nightride(route_id)

def fetch_feed(api_key):
	# Fetches the response from tfnsw api, returning a readable message.
	resp = requests.get(URL, headers={"Authorization": f"apikey {api_key}"}, timeout=30)
	resp.raise_for_status()

	feed = gtfs_realtime_pb2.FeedMessage()
	feed.ParseFromString(resp.content)

	return feed

def to_lines(feed):
	# Converts the feed, to a dictionary appending the filtered lines as json to a list lines
	feed_dict = MessageToDict(feed, preserving_proto_field_name=True)
	feed_timestamp = feed_dict["header"]["timestamp"]
	
	lines = []

	for entity in feed_dict["entity"]:
		if "trip_update" not in entity:
			continue

		route_id = entity["trip_update"]["trip"].get("route_id", "")

		if keep(route_id):
			entity["feed_timestamp"] = feed_timestamp
			lines.append(json.dumps(entity))

	return lines


def write_lines(lines, output_dir):
	# Converting used time to UTC, to avoid daylight savings
	# Writes the trips to a compressed files, returning the files path

	stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
	path = Path(output_dir) / f"trip_updates_{stamp}.jsonl.gz"
	path.parent.mkdir(exist_ok=True)

	with gzip.open(path, "wt", encoding="utf-8") as f:
		for line in lines:
			f.write(line + "\n")
	return path

def upload_file(local_path, host, token):
	# Uploads the saved file to Databricks using a PUT request

	data = local_path.read_bytes()
	date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
	
	folder = "test" if TEST_ROUTE_ID else "trip_updates"
	remote_path = f"{VOLUME_ROOT}/{folder}/date={date}/{local_path.name}"

	url = f"{host}/api/2.0/fs/files{remote_path}"

	resp = requests.put(url, headers={"Authorization": f"Bearer {token}"}, data=data, timeout=60)
	resp.raise_for_status()

	return remote_path

def poll_once(api_key, host, token):
	# Call the api, fetching the data, and converting it to a dictionary to be uploaded to Databricks

	feed = fetch_feed(api_key)
	lines = to_lines(feed)
	
	if not lines:
		print("No trips kept")
		return

	path = write_lines(lines, OUTPUT_DIR)

	remote_path = upload_file(path,host,token)
	
	print("Remote path:", remote_path, "Lines kept:", len(lines))

def run(api_key, host, token, duration_minutes, interval_seconds):
	# Runs poll-once at fixed intervals 

	end_time = time.monotonic() + duration_minutes * 60
	ok, failed = 0, 0

	while time.monotonic() < end_time:
		started = time.monotonic()
		try:
			poll_once(api_key, host, token)
			ok += 1
		except Exception as error:
			failed += 1
			print("Poll failed:", error)
		elapsed = time.monotonic() - started
		time.sleep(max(0, interval_seconds - elapsed))
	print("ok:", ok, "failed:", failed)

def main():
	# Holds all variable stores in the environment and calls run
	api_key = os.environ["TFNSW_API_KEY"].strip()
	host = os.environ["DATABRICKS_HOST"].strip()
	token = os.environ["DATABRICKS_TOKEN"].strip()
	duration = int(os.environ.get("POLL_MINUTES", "330"))
	interval = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
	run(api_key, host, token, duration, interval)

if __name__ == "__main__":
	main()


