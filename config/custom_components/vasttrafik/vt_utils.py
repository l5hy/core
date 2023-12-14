from datetime import timedelta
from datetime import datetime
from dateutil import tz
import geopy.geocoders
from geopy import exc
import sys
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
        return self.api_call('journeys?originGid='+str(origin)+'&destinationGid='+str(dest) + '&' + '&includeOccupancy=true&')

    def get_journeys_details(self, detailsReference):
        return self.api_call(f'journeys/{detailsReference}/details')

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

    def get_traffic_data(self):
        """
        Get traffic data from the API using the obtained token.
        """
        # Check if the token is still valid
        if datetime.now() >= self._token_expire_date:
            self.update_token()

        headers = {
            "Authorization": "Bearer " + self._token,
            "Content-Type": "application/json"
        }

        # the actual endpoint path
        endpoint_url = API_BASE_URL + "/traffic-situations"

        response = requests.get(endpoint_url, headers=headers)

        if response.status_code == 200:
            traffic_data = json.loads(response.content.decode("UTF-8"))
            return self.format_traffic_data_for_ui(traffic_data)
        else:
            print(f"Failed to fetch traffic data. Status code: {response.status_code}")
            print(f"Response content: {response.content.decode('UTF-8')}")
            return None

    ## The traffic data is formatted to extract the essential inputs.

    def format_traffic_data_for_ui(self, traffic_data):
        """
        Format traffic data for the UI.

        :param traffic_data: Raw traffic data from the API.
        :return: Formatted traffic data for the UI.
        """
        formatted_data = []

        for situation in traffic_data:
            severity = situation.get("severity", "")
            description = situation.get("description", "")

            affected_stop_points = situation.get("affectedStopPoints", [])
            stop_points_data = []
            for stop_point in affected_stop_points:
                stop_points_data.append({
                    "name": stop_point.get("name", ""),
                    "municipalityName": stop_point.get("municipalityName", "")
                })

            affected_lines = situation.get("affectedLines", [])
            lines_data = []
            for line in affected_lines:
                directions_data = []
                for direction in line.get("directions", []):
                    directions_data.append({
                        "name": direction.get("name", "")
                    })

                lines_data.append({
                    "designation": line.get("designation", ""),
                    "defaultTransportModeCode": line.get("defaultTransportModeCode", ""),
                    "directions": directions_data
                })

            formatted_data.append({
                "severity": severity,
                "description": description,
                "affectedStopPoints": stop_points_data,
                "affectedLines": lines_data
            })

        return formatted_data

class JPImpl:
    def __init__(self):
        self.jp = JourneyPlanner()

    #Returns a list of all the tripLegs parts of the get_journeys function, using start and stop gid's. Does not include any of the reference codes.
    def possible_trips(self, start, stop):
        dict = self.jp.get_journeys(start, stop)["results"]
        trips = []
        for x in range (1, len(dict)):
            trips.append(dict[x].get("tripLegs"))
        return trips

    #Returns a list of estimated times of arrival, if there is no transfer during the trip the length will be 1, increasing with the amount of transfers
    def get_estimated_arrival_time (self, trip):
    #trip requires triplegs from get_journeys, ie get_journeys(origin, dest)["results"][x].get("tripLegs"), where x = 0, 1, 2, 3....
        if len(trip)>1:
            return self.get_eta_transfer(trip)
        else:
            return self.get_eta_no_transfer(trip)
    #returns a list regardless of length

    #Part of get_eta, function specifically for trips with transfers
    def get_eta_transfer(self, trip):
        trip_eta_with_transfer = []
        for t in trip:
            if t[0].get("estimatedArrivalTime"):
                estTime = datetime.fromisoformat(t[0].get("estimatedArrivalTime"))
                trip_eta_with_transfer.append(estTime)

        # for x in range(len(trip)):
        #     print(trip[x][0])
        #     estTime = datetime.fromisoformat(trip[x][0].get("estimatedArrivalTime"))
        #     formatted_timestamp = estTime.strftime('%H:%M')
        #     trip_eta_with_transfer.append(formatted_timestamp)
        return trip_eta_with_transfer

    #Part of get_eta, function specifically for trips without transfers
    def get_eta_no_transfer(self,trip):
        estTime = datetime.fromisoformat(trip[0].get("estimatedArrivalTime"))
        trip_eta = [estTime]
        return trip_eta

    #Returns the time difference between the "time" variable and the current time in minutes. "time" needs to be a datetime object from a trip dict.
    #needs to be extracted using the datetime.fromisoformat() function.
    def get_time_difference_in_minutes(self, time):
        cet = tz.gettz("Europe/Stockholm")
        current_dateTime = datetime.now(cet)
        d = time - current_dateTime
        difference = d.total_seconds()/60
        return difference

    #Returns a list of dicts, based on the amount of transfers, with reduced amount of information, only information we need
    #Sometimes there's a keyerror with the "estimatedDepartureTime" just ignore and run again, probably when the first part is to walk to the first stop.
    def trip_details_reduction (self, details_reference):
        trip_dict = self.jp.get_journeys_details(details_reference)
        return_list = []
        stop_number = 0
        if trip_dict.get('tripLegs') is None:
            return []
        if len(trip_dict.get('tripLegs')) > 1:
            for y in range(0, len(trip_dict.get("tripLegs"))):
                y_max = len(trip_dict.get("tripLegs"))-1
                new_dict = {
                    "line" : trip_dict.get("tripLegs")[y].get("serviceJourneys")[0].get("line").get("name"),
                    "direction" : trip_dict.get("tripLegs")[y].get("serviceJourneys")[0].get("direction"),
                    "listOfStops" : {}
                }
                stops_dict = {
                }
                for z in range(0, len(trip_dict.get("tripLegs")[y].get("callsOnTripLeg"))):
                    z_max = len(trip_dict.get("tripLegs")[y].get("callsOnTripLeg"))-1
                    reference_object_stop = trip_dict.get("tripLegs")[y].get("callsOnTripLeg")[z].get("stopPoint")
                    reference_object_other = trip_dict.get("tripLegs")[y].get("callsOnTripLeg")[z]
                    if z == 0:
                        stop_dict = {
                            "relativeStopNumber" : z,
                            "stopNumber" : stop_number,
                            "name" : reference_object_stop.get("name"),
                            "platform" : reference_object_stop.get("platform"),
                            "gid" : reference_object_stop.get("gid"),
                            "latitude" : reference_object_stop.get("latitude"),
                            "longitude" : reference_object_stop.get("longitude"),
                            "departure" : reference_object_other.get("estimatedDepartureTime")

                        }
                        if y == 0:
                            stop_dict["origin"] = True
                        else:
                            stop_dict["transferStart"] = True
                        stops_dict[z] = stop_dict
                    elif z == z_max:
                        stop_dict = {
                            "relativeStopNumber" : z,
                            "stopNumber" : stop_number,
                            "name" : reference_object_stop.get("name"),
                            "platform" : reference_object_stop.get("platform"),
                            "gid" : reference_object_stop.get("gid"),
                            "latitude" : reference_object_stop.get("latitude"),
                            "longitude" : reference_object_stop.get("longitude"),
                            "arrival" : reference_object_other.get("estimatedArrivalTime"),
                        }
                        if y == y_max:
                            stop_dict["destination"] = True
                        else:
                            stop_dict["transferStop"] = True
                        stops_dict[z] = stop_dict
                    else:
                        stop_dict = {
                            "relativeStopNumber" : z,
                            "stopNumber" : stop_number,
                            "name" : reference_object_stop.get("name"),
                            "platform" : reference_object_stop.get("platform"),
                            "gid" : reference_object_stop.get("gid"),
                            "latitude" : reference_object_stop.get("latitude"),
                            "longitude" : reference_object_stop.get("longitude"),
                            "arrival" : reference_object_other.get("estimatedArrivalTime"),
                            "departure" : reference_object_other.get("estimatedDepartureTime")
                        }
                        stops_dict[z] = stop_dict
                        stop_number+=1
                new_dict["listOfStops"]= stops_dict
                return_list.append(new_dict)
            return return_list
        else:
            new_dict = {
                "line" : trip_dict.get("tripLegs")[0].get("serviceJourneys")[0].get("line").get("name"),
                "direction" : trip_dict.get("tripLegs")[0].get("serviceJourneys")[0].get("direction"),
                "listOfStops" : {}
            }
            stops_dict = {
            }
            for z in range(0, len(trip_dict.get("tripLegs")[0].get("callsOnTripLeg"))):
                reference_object_stop = trip_dict.get("tripLegs")[0].get("callsOnTripLeg")[z].get("stopPoint")
                reference_object_other = trip_dict.get("tripLegs")[0].get("callsOnTripLeg")[z]
                if z == 0:
                    stop_dict = {
                        "origin" : True,
                        "relativeStopNumber" : z,
                        "stopNumber" : stop_number,
                        "name" : reference_object_stop.get("name"),
                        "platform" : reference_object_stop.get("platform"),
                        "gid" : reference_object_stop.get("gid"),
                        "latitude" : reference_object_stop.get("latitude"),
                        "longitude" : reference_object_stop.get("longitude"),
                        "departure" : reference_object_other.get("estimatedDepartureTime")
                        }
                    stops_dict[z] = stop_dict
                elif z == len(trip_dict.get("tripLegs")[0].get("callsOnTripLeg"))-1:
                    stop_dict = {
                        "destination" : True,
                        "relativeStopNumber" : z,
                        "stopNumber" : stop_number,
                        "name" : reference_object_stop.get("name"),
                        "platform" : reference_object_stop.get("platform"),
                        "gid" : reference_object_stop.get("gid"),
                        "latitude" : reference_object_stop.get("latitude"),
                        "longitude" : reference_object_stop.get("longitude"),
                        "arrival" : reference_object_other.get("estimatedArrivalTime"),
                        "departure" : reference_object_other.get("estimatedDepartureTime")
                    }
                    stops_dict[z] = stop_dict
                else:
                    stop_dict = {
                        "relativeStopNumber" : z,
                        "stopNumber" : stop_number,
                        "name" : reference_object_stop.get("name"),
                        "platform" : reference_object_stop.get("platform"),
                        "gid" : reference_object_stop.get("gid"),
                        "latitude" : reference_object_stop.get("latitude"),
                        "longitude" : reference_object_stop.get("longitude"),
                        "arrival" : reference_object_other.get("estimatedArrivalTime"),
                        "departure" : reference_object_other.get("estimatedDepartureTime")
                    }
                    stops_dict[z] = stop_dict
                    stop_number+=1
            new_dict["listOfStops"] = stops_dict
            return_list.append(new_dict)
            return return_list

    #Requires the output from the trip_details_reduction function
    #Outputs a list of dicts containing latitudes and longitudes, along with if it's a special type of stop in the form of the "type" key.
    def get_trip_stop_coordinates(self, details_list):
        return_list = []
        if len(details_list) == 0:
            return return_list
        if len(details_list) > 1:
            for d in details_list:
                for x in range(len(d.get("listOfStops"))):
                    temp_dict = d.get("listOfStops")[x]
                    new_dict = {
                        "latitude": temp_dict.get("latitude"),
                        "longitude": temp_dict.get("longitude"),
                        "name": temp_dict.get("name")
                    }
                    if "origin" in temp_dict:
                        new_dict["type"] = "origin"
                    elif "transferStart" in temp_dict:
                        new_dict["type"] = "transferStart"
                    elif "transferStop" in temp_dict:
                        new_dict["type"] = "transferStop"
                    elif "destination" in temp_dict:
                        new_dict["type"] = "destination"
                    return_list.append(new_dict)
        else:
            for x in range(len(details_list[0].get("listOfStops"))):
                temp_dict = details_list[0].get("listOfStops")[x]
                new_dict = {
                    "latitude": temp_dict.get("latitude"),
                    "longitude": temp_dict.get("longitude"),
                    "name": temp_dict.get("name")
                    }
                if "origin" in temp_dict:
                    new_dict["type"] = "origin"
                elif "destination" in temp_dict:
                    new_dict["type"] = "destination"
                return_list.append(new_dict)
        return return_list


    def advanced_travel_plan(self, trips):
        return_trips = []
        next_trip = trips[0]

        if len(next_trip) > 1:
            for x in range(0, len(trips)-1):
                if x == 0:
                    return_trips.append(datetime.fromisoformat(next_trip[x].get("origin").get("estimatedTime")).strftime('%H:%M'))
                    return_trips.append("Line: " + next_trip[x].get("serviceJourney").get("line").get("shortName") + ", From: " + next_trip[x].get("origin").get("stopPoint").get("name") + ", Platform " + next_trip[x].get("origin").get("stopPoint").get("platform") +
                                        ", At: " + datetime.fromisoformat(next_trip[x].get("origin").get("estimatedTime")).strftime('%H:%M') + ", Occupancy: " + next_trip[x]["occupancy"].get("level"))
                elif x == len(next_trip) - 1:
                    return_trips.append("Swap to Line: " + next_trip[x].get("serviceJourney").get("line").get("shortName") + ", At: " + next_trip[x].get("origin").get("stopPoint").get("name") + ", Platform " + next_trip[x].get("origin").get("stopPoint").get("platform") + ", Occupancy: " + next_trip[x]["occupancy"].get("level"))
                    return_trips.append("End Stop: " + next_trip[x]["destination"].get("stopPoint").get("name") + ", Platform " + next_trip[x]["destination"].get("stopPoint").get("platform") + ", At: " + datetime.fromisoformat(next_trip[x]["destination"].get("estimatedTime")).strftime('%H:%M'))
                else:
                    try:
                        return_trips.append("Swap to Line: " + next_trip[x].get("serviceJourney").get("line").get("shortName") + ", At: " + next_trip[x].get("origin").get("stopPoint").get("name") + ", Platform " + next_trip[x].get("origin").get("stopPoint").get("platform") + ", Occupancy: " + next_trip[x]["occupancy"].get("level"))
                    except:
                        None
        else:
            if next_trip[0].get("origin").get("estimatedTime"):
                return_trips.append(datetime.fromisoformat(next_trip[0].get("origin").get("estimatedTime")).strftime('%H:%M'))
                return_trips.append("Line: " + next_trip[0].get("serviceJourney").get("line").get("shortName") + ", From: " + next_trip[0].get("origin").get("stopPoint").get("name") + ", Platform " + next_trip[0].get("origin").get("stopPoint").get("platform") + ", At: " +
                                    datetime.fromisoformat(next_trip[0].get("origin").get("estimatedTime")).strftime('%H:%M') + ", Occupancy: " + next_trip[0]["occupancy"].get("level"))
                return_trips.append("End Stop: " + next_trip[0]["destination"].get("stopPoint").get("name") + ", Platform " + next_trip[0]["destination"].get("stopPoint").get("platform") + ", At: " + datetime.fromisoformat(next_trip[0]["destination"].get("estimatedTime")).strftime('%H:%M'))

        return return_trips

#get nearby stops
    def nearby_stops(self):
        stops = self.jp.get_locations_lat_long(str(57.708110), str(11.938043))
        nearest_stops = {stop.get("name"): stop["straightLineDistanceInMeters"] for stop in stops}
        list_stops = list((nearest_stops.items()))
        list_stops.sort(key=lambda x: x[1])
        # print("Nearest Stops are :")
        # for stop in list_stops:
        #     print(f'{"".join(stop[:-1])}  -  {stop[-1]} meters')
        return list_stops


#getting nearby stops by entering the location

    #def find_nearest_stops(self):
        #print("Enter the location you want to find coordinates for:")
        #location_name = sys.stdin.readline().strip()

        #geocoder = geopy.geocoders.Nominatim(user_agent="Vasttrafik")

        #try:
            #location = geocoder.geocode(location_name)
            #print(location.address)
        #except exc.GeocoderNotFound:
            #print("Location not found")

        #stops = self.jp.get_locations_lat_long(location.latitude, location.longitude)

        #nearest_stops = {stop.get("name"): stop["straightLineDistanceInMeters"] for stop in stops}
        #sorted_stops = sorted(nearest_stops.items(), key=lambda x: x[1])

        #print("Nearest Stops are:")
        #for stop in sorted_stops:
            #print(f'{"".join(stop[:-1])}  -  {stop[-1]} meters')

#Instantiate the class and call the function directly
#JPImpl().find_nearest_stops()