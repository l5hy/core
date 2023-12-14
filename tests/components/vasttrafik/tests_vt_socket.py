import unittest
from unittest.mock import patch, MagicMock
from unittest.mock import patch, Mock
from vt_utils import JourneyPlanner
from vt_utils import JPImpl
import pytest
import socket
from datetime import datetime, timedelta

#unit test for traffic situation
class TestGetTrafficData(unittest.TestCase):

    def setUp(self):
        self._key = '4lLqpr4revmEOTYojvlS5eSUMQEa'
        self._secret = 'W1IxsFa7DXgyUeORcVQNDcklukIa'
        self.your_instance = JourneyPlanner(key=self._key, secret=self._secret)
        self.your_instance._token_expire_date = datetime.now() + timedelta(hours=1)

    @patch('vt_utils.requests.get')
    def test_get_traffic_data_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content.decode.return_value = '{"some": "traffic_data"}'

        result = self.your_instance.get_traffic_data()

        expected_result = self.your_instance.format_traffic_data_for_ui({"some": "traffic_data"})

        self.assertEqual(result, expected_result, "The result does not match the expected result.")

    @patch('vt_utils.requests.get')
    def test_get_traffic_data_failure(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.content.decode.return_value = '{"error": "not_found"}'

        result = self.your_instance.get_traffic_data()

        self.assertIsNone(result)

        mock_print = MagicMock()
        with patch('builtins.print', mock_print):
            self.your_instance.get_traffic_data()
            mock_print.assert_called_with("Failed to fetch traffic data. Status code: 404")
            mock_print.reset_mock()

#test for the nearest stops function

class TestNearbyStops(unittest.TestCase):

    def setUp(self):
        import mock
        self.mock_get_locations_lat_long = mock.MagicMock()
        self.jp = mock.Mock()
        self.jp.get_locations_lat_long = self.mock_get_locations_lat_long
    @pytest.mark.enable_socket
    @patch('vt_utils.JourneyPlanner.get_locations_lat_long')
    def test_nearby_stops(self, mock_get_locations_lat_long):
        # Mock data for get_locations_lat_long
        mock_stops_data = [
            {
                "name": "Stop1",
                "straightLineDistanceInMeters": 100
            },
            {
                "name": "Stop2",
                "straightLineDistanceInMeters": 200
            },
            {
                "name": "Stop3",
                "straightLineDistanceInMeters": 150
            }
        ]

        # Configure the mock method to return the mock data
        mock_get_locations_lat_long.return_value = mock_stops_data

        # Call the function
        result = JPImpl().nearby_stops()

        # Assert the returned value
        expected_result = [
            ("Stop1", 100),
            ("Stop3", 150),
            ("Stop2", 200)
        ]
        self.assertEqual(result, expected_result)

