This is an updated version of the live version of the Västtrafik integration.

This updated version includes new features:
    - Journey planning with extended features:
        - handles bus/train/boat swaps
        - includes info about occupancy levels
    - Alerts for upcomming stops
    - Display bus paths on a Map
    - Display nearby bus stops
    - Display current and future trafic situation

To create a journey plan one must add data like this to their configuration.yaml file:
Example sensor:

(singular journey)
sensor:
  - platform: vasttrafik
    departures:
      - from: Brunnsparken
        heading: Grönsakstorget

(multiple journeys)
sensor:
  - platform: vasttrafik
    departures:
      - from: Brunnsparken
        heading: Grönsakstorget
      - from: Bifrost
        heading: Chalmers
      - from: Chalmers
        heading: Bifrost

where "Brunnsparken" is the departure station and "Grönsakstorget" is the end station and are both required fields.

Other functions like nearby bus stops work automatically based on your current location.

Displaying bus paths on Map is done through the built in map integration in homeassistant,
then the Västtrafik integration will populate the map based on what journeys have been specified in the configuration.yaml file.

The integration mainly consists of two files vt_utils.py and sensor.py
    - vt_utils.py:  Most backend logic of the integration, consists of functions which talk with the Västtrafik v4 API
                    and uses that data to return readable information.
    - sensor.py:    Frontend entity used to display data for different journeys that are detirmined by the configuration.yaml
                    file.