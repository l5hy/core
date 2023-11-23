import requests
import json
import base64
from datetime import datetime
from datetime import timedelta
import geocoder

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
        urlformat = "{baseurl}/{service}{parameters}&format=json"
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
        response = self._request(service=request_url)
        return response

    # Journeys
    def get_journeys(self, origin, dest):
        return self.api_call('journeys?originGid=' + str(origin) + '&destinationGid=' + str(dest) + '&')

    # LOCATION
    def get_locations(self, name):
        return self.api_call('locations/by-text?q=' + name)['results']

    def get_locations_lat_long(self, latitude, longitude):
        return self.api_call(f'locations/by-coordinates?latitude={latitude}&longitude={longitude}&radiusInMeters=500&limit=10&offset=0')['results']


jp = JourneyPlanner(
    key=CLIENT_ID,
    secret=SECRET)


#getting nearby vasttrafik stops from the location
def nearstop_vastra():


    g = geocoder.ip('me')
    stops = jp.get_locations_lat_long(g.latlng[0], g.latlng[1])
    nearest_stops = {stop["name"]: stop["straightLineDistanceInMeters"] for stop in stops}
    list_stops = list((nearest_stops.items()))
    list_stops.sort(key=lambda x: x[1])
    print("Nearest Stops are :")
    for stop in list_stops:
        print(f'{"".join(stop[:-1])}  -  {stop[-1]} meters')


nearstop_vastra()