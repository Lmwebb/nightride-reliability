# Explores the live bus feed, analysing which routes are in it, how route IDs are formatted, 
# and whether the NightRide filter worked correctly.

import os
from collections import Counter

import requests
from google.transit import gtfs_realtime_pb2


URL = "https://api.transport.nsw.gov.au/v1/gtfs/realtime/buses"
key = os.environ["TFNSW_API_KEY"].strip()

resp = requests.get(URL, headers={"Authorization": f"apikey {key}"}, timeout=30)
resp.raise_for_status()

feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(resp.content)

count = 0
for entity in feed.entity:
	if entity.HasField("trip_update"):
		count += 1

print("Entities with trip updates: ", count)

routes = []
for entity in feed.entity:
	if entity.HasField("trip_update"):
		routes.append(entity.trip_update.trip.route_id)
route_counts = Counter(routes)

print("Example of 5 route_id's: ", routes[:5])

def is_nightride(route_id):
	route_part = route_id.split("_")[-1]
	return route_part.startswith("N") and len(route_part) >= 2 and route_part[1].isdigit()

print("Checks nightride function:", is_nightride("2441_N10"))
print("Checks nightride function:", is_nightride("2447_10A"))
print("Checks nightride function:", is_nightride("2442_N"))
print("Checks nightride function:", is_nightride(""))

night_routes = []
for route_id in routes:
	if is_nightride(route_id):
		night_routes.append(route_id)

print("Number of distinct routes:", len(route_counts))
print("Top 10 most common routes:", route_counts.most_common(10))

print("NightRide trip count:", len(night_routes))
print("NightRide routes:", sorted(set(night_routes)))

