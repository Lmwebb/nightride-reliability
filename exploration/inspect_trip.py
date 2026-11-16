# Inspects one live trip's data fields and stop-by-stop predictions.
# Run it twice a few minutes apart, to find passed stops are dropped off and predictions change.

import os
from datetime import datetime

import requests
from google.transit import gtfs_realtime_pb2

URL = "https://api.transport.nsw.gov.au/v1/gtfs/realtime/buses"
key = os.environ["TFNSW_API_KEY"]

resp = requests.get(URL, headers={"Authorization": f"apikey {key}"}, timeout=30)
resp.raise_for_status()

feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(resp.content)

tu = None
for entity in feed.entity:
	if entity.trip_update.trip.route_id == "2509_333":
		tu = entity.trip_update
		break

print("Found Trip:", tu.trip.trip_id)

print("Trip fields:", tu.trip.trip_id, "Trip route_id:", tu.trip.route_id, "Trip start_date:", tu.trip.start_date, "Trip start_time:", tu.trip.start_time, "Trip schedule_relationship:", tu.trip.schedule_relationship)

print("Remaining stops:", len(tu.stop_time_update))


for stu in tu.stop_time_update:
	print(f"{stu.stop_sequence:>3}, {stu.stop_id},  delay={stu.arrival.delay}, arrives={datetime.fromtimestamp(stu.arrival.time)}")

