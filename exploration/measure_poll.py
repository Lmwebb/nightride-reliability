# Converts one poll to JSON and gzips it to compare file sizes,
# then estimates the total size of a full night of polling.

import os
import gzip
import json

import requests
from google.protobuf.json_format import MessageToDict
from google.transit import gtfs_realtime_pb2

URL = "https://api.transport.nsw.gov.au/v1/gtfs/realtime/buses"
key = os.environ["TFNSW_API_KEY"]

resp = requests.get(URL, headers={"Authorization": f"apikey {key}"}, timeout=30)
resp.raise_for_status()

feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(resp.content)

feed_dict = MessageToDict(feed, preserving_proto_field_name=True)

print("First level keys:", feed_dict.keys(), "Total entities in dictionary:", len(feed_dict["entity"]))

print(json.dumps(feed_dict["entity"][0], indent=2))

json_byte = json.dumps(feed_dict).encode("utf-8")
raw_size = len(resp.content)
json_size = len(json_byte)
gzip_size = len(gzip.compress(json_byte))

print(f"raw size: {raw_size/1000000:.2f} json size: {json_size/1000000:.2f} gzip size: {gzip_size/1000000:.2f}")

print(f"Estimated size of one night of polls in MB: {(gzip_size/1000000) * 330:.2f}")