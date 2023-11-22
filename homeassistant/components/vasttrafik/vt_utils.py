import requests
import json
import base64
from datetime import datetime
from datetime import timedelta

CLIENT_ID = '7PmupRmmj6QtZ1QjeSVMaTPeTwwa'
SECRET = '059CaEAyojvrzEhDqwqT00BcKo8a'
AUTH_KEY = 'N1BtdXBSbW1qNlF0WjFRamVTVk1hVFBlVHd3YTowNTlDYUVBeW9qdnJ6RWhEcXdxVDAwQmNLbzhh'
TOKEN_URL = 'https://ext-api.vasttrafik.se/token'
API_BASE_URL = 'https://ext-api.vasttrafik.se/pr/v4'
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M'

class JourneyPlanner:
    def __init__(self, key, secret, expiry=59):
        self._key = key
        self._secret = secret
        self._expiry = expiry
        self.update_token()

    def update_token(self):
        """ Get token from key and secret """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode(
                (self._key + ':' + self._secret).encode()).decode()
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
        return self.api_call(f'locations/by-coordinates?latitude={latitude}&longitude={longitude}&radiusInMeters=500&limit=10&offset=0')['results']

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


jp = JourneyPlanner(
    key=CLIENT_ID,
    secret=SECRET)

# TESTING
def test():
    brunnsparken = jp.get_locations('Brunnsparken')
    gid = brunnsparken[0]['gid']
    print(f'Location: {brunnsparken[0]["name"]}')
    print(f'GID: {gid}')
    detailsReference = jp.get_departures_stop_area(gid)[0]['detailsReference']

    print(f'DetailsReference: {detailsReference}')
    print(f'Get Departure Details SA: {jp.get_departure_details_sa(gid, detailsReference)[0]["direction"]} & Transport number {jp.get_departure_details_sa(gid, detailsReference)[0]["line"]["name"]}')
    print(f'Get Arrival details SA: {jp.get_arrival_details_sa(gid, detailsReference)[0]["direction"]} & Transport number {jp.get_arrival_details_sa(gid, detailsReference)[0]["line"]["name"]}')
    print(f'Get Departure details SP: {jp.get_departure_details_sp(gid, detailsReference)[0]["direction"]} & Transport number {jp.get_departure_details_sp(gid, detailsReference)[0]["line"]["name"]}')
    print(f'Get Arrival details SP: {jp.get_arrival_details_sp(gid, detailsReference)[0]["direction"]} & Transport number {jp.get_arrival_details_sp(gid, detailsReference)[0]["line"]["name"]}')
    #print(f'Journeys: {jp.get_journeys(9021014001760000,9022014001760004)["results"]}')

    chalmers = jp.get_locations('Chalmers')
    gid2 = chalmers[0]['gid']
    print(f'Location: {chalmers[0]["name"]}')
    print(f'GID: {gid}')
    print(gid2)
    print(possible_trips(gid, gid2))
    print (reduce_trips(possible_trips(gid, gid2)))




def possible_trips(start, stop):
    dict = jp.get_journeys(start, stop)["results"]
    trips = []
    for x in range (0, len(dict)):
        trips.append(dict[x]["tripLegs"])
    return trips

def reduce_trips (trips):
    return_trips = []
    for x in range(len(trips)):
        string = ""
        print(len(trips[x]))
        if len(trips[x]) > 1:
            z=0
            for y in range(0, len(trips[x])-1):
                if y == 0:
                    string = "Board " + trips[x][y]["serviceJourney"]["line"]["name"] + " at stop " + trips[x][y]["origin"]["stopPoint"]["name"] + ", platform " + trips[x][y]["origin"]["stopPoint"]["platform"] + ". " + "Transfer at " + trips[x][y]["destination"]["stopPoint"]["name"] + ", platform " + trips[x][y]["destination"]["stopPoint"]["platform"] + " to " + trips[x][y+1]["origin"]["stopPoint"]["name"] + ", platform " + trips[x][y+1]["origin"]["stopPoint"]["platform"] + " and board " + trips[x][y+1]["serviceJourney"]["line"]["name"] +  ". "
                if y > 0:
                    string = string + "Then transfer at " + trips[x][y]["destination"]["stopPoint"]["name"] + ", platform " + trips[x][y]["destination"]["stopPoint"]["platform"] + " to " + trips[x][y+1]["origin"]["stopPoint"]["name"] + ", platform " + trips[x][y+1]["origin"]["stopPoint"]["platform"] + " and board " + trips[x][y+1]["serviceJourney"]["line"]["name"] +  ". "
                z = 0 + y
            string = string + "Finally exit vehicle at " + trips[x][z]["destination"]["stopPoint"]["name"] + ", platform " + trips[x][z]["destination"]["stopPoint"]["platform"] + ". "
            return_trips.append(string)
        else:
            string = "Board " + trips[x][0]["serviceJourney"]["line"]["name"] + " at stop " + trips[x][0]["origin"]["stopPoint"]["name"] + ", platform " + trips[x][0]["origin"]["stopPoint"]["platform"] + ". " + "Exit vehicle at " + trips[x][0]["destination"]["stopPoint"]["name"] + " platform " + trips[x][0]["destination"]["stopPoint"]["platform"] + ". "
            return_trips.append(string)
    return return_trips




test()


