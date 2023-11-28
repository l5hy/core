import base64
from datetime import datetime, timedelta
import json

import requests
from update_traffic_sensor_state import update_traffic_sensor_state

CLIENT_ID = "4lLqpr4revmEOTYojvlS5eSUMQEa"
SECRET = "W1IxsFa7DXgyUeORcVQNDcklukIa"
TOKEN_URL = "https://ext-api.vasttrafik.se/token"
API_BASE_URL = "https://ext-api.vasttrafik.se/ts/v1"

class JourneyPlanner:
    def __init__(self, key, secret, expiry=59):
        """
        Initialize the JourneyPlanner.

        :param key: The API key.
        :param secret: The API secret.
        :param expiry: Token expiry time in minutes.
        """
        self._key = key
        self._secret = secret
        self._expiry = expiry
        self._token = None
        self._token_expire_date = None
        self.update_token()

    def update_token(self):
        """
        Get token from key and secret.
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + base64.b64encode(
                (self._key + ":" + self._secret).encode()).decode()
            }
        data = {"grant_type": "client_credentials"}

        response = requests.post(TOKEN_URL, data=data, headers=headers)

        if response.status_code == 200:
            obj = json.loads(response.content.decode("UTF-8"))
            self._token = obj["access_token"]
            self._token_expire_date = (
                datetime.now() +
                timedelta(minutes=self._expiry))
        else:
            print(f"Failed to generate token. Status code: {response.status_code}")
            print(f"Response content: {response.content.decode('UTF-8')}")

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

journey_planner = JourneyPlanner(CLIENT_ID, SECRET)
journey_planner.update_token()
traffic_data = journey_planner.get_traffic_data()

if traffic_data:
    formatted_traffic_data = journey_planner.format_traffic_data_for_ui(traffic_data)
    update_traffic_sensor_state(journey_planner)
