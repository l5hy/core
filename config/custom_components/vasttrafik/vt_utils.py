from datetime import timedelta
from datetime import datetime
from dateutil import tz

import requests
import json

AUTH_KEY = 'N1BtdXBSbW1qNlF0WjFRamVTVk1hVFBlVHd3YTowNTlDYUVBeW9qdnJ6RWhEcXdxVDAwQmNLbzhh'
TOKEN_URL = 'https://ext-api.vasttrafik.se/token'
API_BASE_URL = 'https://ext-api.vasttrafik.se/pr/v4'
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M'

class JourneyPlanner:
    def __init__(self, expiry=59):
        self._expiry = expiry
        self.update_token()

    def update_token(self):
        headers = {
            'Authorization': 'Basic '+AUTH_KEY
            }
        data = {'grant_type': 'client_credentials'}

        response = requests.post(TOKEN_URL, data=data, headers=headers)
        obj = json.loads(response.content.decode('UTF-8'))
        self._token = obj['access_token']
        self._token_expire_date = (
            datetime.now() +
            timedelta(minutes=self._expiry))

    def _request(self, service, **parameters):
        """ request builder """
        urlformat = "{baseurl}/{service}?{parameters}&format=json"
        url = urlformat.format(
            baseurl=API_BASE_URL,
            service=service,
            parameters="&".join([
                "{}={}".format(key, value) for key, value in parameters.items()
                ]))
        if datetime.now() > self._token_expire_date:
            self.update_token()
        headers = {'Authorization': 'Bearer ' + self._token}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(res.content.decode('UTF-8'))
        else:
            print('Error: ' + str(res.status_code) +
                            str(res.content))

    def api_call(self, request_url):
        response = self._request(request_url)
        return response

    # Journeys
    def get_journeys(self, origin, dest):
        return self.api_call('journeys?originGid='+str(origin)+'&destinationGid='+str(dest)+'&')

    # LOCATION
    def get_locations(self, name):
        return self.api_call('locations/by-text?q='+name)['results']

    def get_locations_lat_long(self, latitude, longitude):
        return self.api_call(f'locations/by-coordinates?latitude={str(latitude)}&longitude={str(longitude)}&types=stoparea&')['results']

    # STOP AREAS
    def get_departures_stop_area(self, gid):
        return self.api_call(f'stop-areas/{gid}/departures')['results']

    def get_arrivals_stop_area(self, gid):
        return self.api_call(f'stop-areas/{gid}/arrivals')['results']

    def get_departure_details_sa(self, gid, detailsReference):
        return self.api_call(f'stop-areas/{gid}/departures/{detailsReference}/details')['serviceJourneys']

    def get_arrival_details_sa(self, gid, detailsReference):
        return self.api_call(f'stop-areas/{gid}/arrivals/{detailsReference}/details')['serviceJourneys']

    # STOP POINTS
    def get_departures_stop_points(self, gid):
        return self.api_call(f'stop-points/{gid}/departures')['results']

    def get_arrivals_stop_points(self, gid):
        return self.api_call(f'stop-points/{gid}/arrivals')['results']

    def get_departure_details_sp(self, gid, detailsReference):
        return self.api_call(f'stop-points/{gid}/departures/{detailsReference}/details')['serviceJourneys']

    def get_arrival_details_sp(self, gid, detailsReference):
        return self.api_call(f'stop-points/{gid}/departures/{detailsReference}/details')['serviceJourneys']



class JPImpl:
    def __init__(self):
        self.jp = JourneyPlanner()

    def possible_trips(self, start, stop):
        dict = self.jp.get_journeys(start, stop)["results"]
        trips = []
        for x in range (1, len(dict)):
            trips.append(dict[x].get("tripLegs"))
        return trips

    #Returns a list of estimated times of arrival, if there is no transfer during the trip the length will be 1, increasing with the amount of transfers
    def get_eta (self, trip):
    #trip requires triplegs from get_journeys, ie get_journeys(origin, dest)["results"][x]["tripLegs"], where x = 0, 1, 2, 3....
        if len(trip)>1:
            return self.get_eta_transfer(trip)
        else:
            return self.get_eta_no_transfer(trip)
    #returns a list regardless of length

    #Part of get_eta, function specifically for trips with transfers
    def get_eta_transfer(self, trip):
        trip_eta_with_transfer = []
        for t in trip:
            estTime = datetime.fromisoformat(t[0].get("estimatedArrivalTime"))
            trip_eta_with_transfer.append(estTime)

        # for x in range(len(trip)):
        #     print(trip[x][0])
        #     estTime = datetime.fromisoformat(trip[x][0]["estimatedArrivalTime"])
        #     formatted_timestamp = estTime.strftime('%H:%M')
        #     trip_eta_with_transfer.append(formatted_timestamp)
        return trip_eta_with_transfer

    #Part of get_eta, function specifically for trips without transfers
    def get_eta_no_transfer(self,trip):
        estTime = datetime.fromisoformat(trip[0]["estimatedArrivalTime"])
        trip_eta = [estTime]
        return trip_eta

    #Returns the time difference between the "time" variable and the current time in minutes. "time" needs to be a datetime object from a trip dict.
    #needs to be extracted using the datetime.fromisoformat() function.
    def compare_time(self, time):
        cet = tz.gettz("Europe/Stockholm")
        current_dateTime = datetime.now(cet)
        d = time - current_dateTime
        difference = d.total_seconds()/60
        return difference

    def advanced_travel_plan(self, trips):
        return_trips = []
        trip_description= ""
        next_trip = trips[0]

        if len(next_trip) > 1:
            for x in range(0, len(trips)-1):
                if x == 0:
                    trip_description = (" Estimated Departure: " + datetime.fromisoformat(next_trip[x]["origin"]["estimatedTime"]).strftime('%H:%M')
                    + ", Line: " + next_trip[x]["serviceJourney"]["line"].get("shortName")
                    + ", From: " + next_trip[x]["origin"]["stopPoint"]["name"] + " platform " + next_trip[x]["origin"]["stopPoint"]["platform"])
                elif x == len(next_trip) - 1:
                    try:
                        trip_description += (", Swap to Line: " + next_trip[x]["serviceJourney"]["line"].get("shortName")
                        + ", At : " + next_trip[x]["origin"]["stopPoint"]["name"] + " platform " + next_trip[x]["origin"]["stopPoint"]["platform"]
                        + ", End Stop: " + next_trip[x]["destination"]["stopPoint"]["name"] + " platform " + next_trip[x]["destination"]["stopPoint"]["platform"]
                        + ", Estimated Arrival: " + datetime.fromisoformat(next_trip[x]["destination"]["estimatedTime"]).strftime('%H:%M'))
                    except:
                        None
                else:
                    try:
                        trip_description += (", Swap to Line: " + next_trip[x]["serviceJourney"]["line"].get("shortName")
                        + ", At : " + next_trip[x]["origin"]["stopPoint"]["name"] + " platform " + next_trip[x]["origin"]["stopPoint"]["platform"])
                    except:
                        None
        else:
            if next_trip[0]["origin"].get("estimatedTime"):
                trip_description = ("Estimated Departure: " + datetime.fromisoformat(next_trip[0]["origin"]["estimatedTime"]).strftime('%H:%M')
                    + ", Line: " + next_trip[0]["serviceJourney"]["line"].get("shortName")
                    + ", From: " + next_trip[0]["origin"]["stopPoint"]["name"] + " platform " + next_trip[0]["origin"]["stopPoint"]["platform"]
                    + ", To: " + next_trip[0]["destination"]["stopPoint"]["name"] + " platform " + next_trip[0]["destination"]["stopPoint"]["platform"]
                    + ", Estimated Arrival: " + datetime.fromisoformat(next_trip[0]["destination"]["estimatedTime"]).strftime('%H:%M'))
        return_trips.append(trip_description)
        return return_trips

    def get_occupancy_level(self, trips):
        next_trip = trips[0]


    def nearby_stops(self):
        stops = self.jp.get_locations_lat_long(str(57.708110), str(11.938043))
        nearest_stops = {stop["name"]: stop["straightLineDistanceInMeters"] for stop in stops}
        list_stops = list((nearest_stops.items()))
        list_stops.sort(key=lambda x: x[1])
        # print("Nearest Stops are :")
        # for stop in list_stops:
        #     print(f'{"".join(stop[:-1])}  -  {stop[-1]} meters')
        return list_stops
