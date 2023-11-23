

import requests

def update_traffic_sensor_state(formatted_traffic_data):
    """
    Update the traffic sensor state in Home Assistant.

    :param formatted_traffic_data: Formatted traffic data for the UI.
    """
    # Assuming you have a service in Home Assistant that updates the sensor state
    # Modify the URL and other parameters accordingly
    url = "http://localhost:8123/api/services/python_script/update_traffic_sensor_state"
    headers = {
        "Content-Type": "application/json",
        # Add any other headers needed, e.g., authentication headers
    }

    # Prepare the data to be sent to the service
    service_data = {
        "domain": "python_script",
        "service": "update_traffic_sensor_state",  # Update service name if needed
        "data": {
            "formatted_traffic_data": formatted_traffic_data
        }
    }

    try:
        response = requests.post(url, json=service_data, headers=headers)

        print(f"Status code: {response.status_code}")
        print(f"Response content: {response.content.decode('UTF-8')}")

        if response.status_code == 200:
            print("Traffic sensor state updated successfully")
        else:
            print("Failed to update sensor state. Check the response content for details.")
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Exception details: {str(e)}")
