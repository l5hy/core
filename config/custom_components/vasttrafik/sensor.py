"""Support for Västtrafik public transport."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components import persistent_notification
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

from homeassistant.helpers import location
from homeassistant.helpers.entity import Entity

from .vt_utils import JourneyPlanner, JPImpl
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.components import zone
from homeassistant.const import CONF_DELAY, CONF_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import Throttle
from homeassistant.util.dt import now

_LOGGER = logging.getLogger(__name__)
SOURCE = 'Vasttrafik'
ATTR_ACCESSIBILITY = "accessibility"
ATTR_DIRECTION = "direction"
ATTR_HEADING = "heading"
ATTR_LINE = "line"
ATTR_TRACK = "track"
ATTR_DESCRIPTION = "description"

CONF_DEPARTURES = "departures"
CONF_FROM = "from"
CONF_HEADING = "heading"
CONF_LINES = "lines"

DEFAULT_DELAY = 2

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEPARTURES): [
            {
                vol.Required(CONF_FROM): cv.string,
                vol.Optional(CONF_DELAY, default=DEFAULT_DELAY): cv.positive_int,
                vol.Required(CONF_HEADING): cv.string,
            }
        ]
    }
)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the departure sensor."""
    planner = JourneyPlanner()
    jpi = JPImpl()
    nearby = jpi.nearby_stops()
    sensors = []
    geo_locations = []
    stop_locations = []
    for departure in config[CONF_DEPARTURES]:
        org = planner.get_locations(departure.get(CONF_FROM))[0]
        dest = planner.get_locations(departure.get(CONF_HEADING))[0]
        originGid = planner.get_locations(departure.get(CONF_FROM))[0]['gid']
        destGid = planner.get_locations(departure.get(CONF_HEADING))[0]['gid']
        route = departure.get(CONF_FROM) +" -> "+ departure.get(CONF_HEADING)
        geo_locations.append(VTGeolocationEvent(org['name'], org['latitude'],org['longitude']))
        geo_locations.append(VTGeolocationEvent(dest['name'], dest['latitude'],dest['longitude']))
        sensors.append(
                VasttrafikDepartureSensor(
                    planner,
                    departure.get(CONF_NAME),
                    departure.get(CONF_FROM),
                    departure.get(CONF_HEADING),
                    departure.get(CONF_DELAY),
                )
            )
        journey = planner.get_journeys(originGid, destGid)
        if journey:
            detailsRef = journey.get('results')[0].get('detailsReference')
            detailsList = jpi.trip_details_reduction(detailsRef)
            stop_coords = jpi.get_coords(detailsList)
            for c in range(len(stop_coords)):
                if (not c == 0) and (not c==len(stop_coords) - 1):
                    stop_locations.append(StopsGeolocationEvent(stop_coords[c].get('name') + " ("+route+ ")",stop_coords[c].get('latitude'), stop_coords[c].get('longitude')))
    for n in nearby:
        sensors.append(VasttrafikDepartureSensor(
            planner,
            n[0] + " (Nearby)",
            n[0],
            'Centralstation',
            DEFAULT_DELAY,
        ))
    add_entities(geo_locations)
    add_entities(stop_locations)
    add_entities(sensors)


class StopsGeolocationEvent(GeolocationEvent):
    """Represents a geolocation event."""
    _attr_should_poll = False
    _attr_icon = "mdi:bus"
    _attr_entity_picture = "https://png.pngtree.com/png-vector/20190118/ourmid/pngtree-vector-stop-icon-png-image_327307.jpg"
    def __init__(
        self,
        name: str,
        latitude: float,
        longitude: float,
    ) -> None:
        """Initialize entity with data provided."""
        self._attr_name = name
        self._attr_source = "vt_entity"
        self._latitude = latitude
        self._longitude = longitude

    @property
    def source(self) -> str:
        """Return source value of this external event."""
        return SOURCE

    @property
    def latitude(self) -> float | None:
        """Return latitude value of this external event."""
        return self._latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude value of this external event."""
        return self._longitude

class VTGeolocationEvent(GeolocationEvent):
    """Represents a geolocation event."""

    _attr_should_poll = False
    _attr_icon = "mdi:bus"
    _attr_entity_picture = "https://www.freepnglogos.com/uploads/pin-png/gps-location-map-pin-icon-2.png"
    def __init__(
        self,
        name: str,
        latitude: float,
        longitude: float,

    ) -> None:
        """Initialize entity with data provided."""
        self._attr_name = name
        self._attr_source = "vt_entity"
        self._latitude = latitude
        self._longitude = longitude

    @property
    def source(self) -> str:
        """Return source value of this external event."""
        return SOURCE

    @property
    def latitude(self) -> float | None:
        """Return latitude value of this external event."""
        return self._latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude value of this external event."""
        return self._longitude


class VasttrafikDepartureSensor(SensorEntity):
    """Implementation of a Vasttrafik Departure Sensor."""

    _attr_attribution = "Data provided by Västtrafik"
    _attr_icon = "mdi:train"
    def __init__(self, planner, name, departure, heading, delay):
        """Initialize the sensor."""
        self._planner = planner
        self._name = departure + " -> " + heading
        self._departure = self.get_station_id(departure)
        self._heading = self.get_station_id(heading)
        self.jpi = JPImpl()
        trips = self.jpi.possible_trips(self._departure["station_id"],self._heading["station_id"])
        self._attr_description = self.jpi.advanced_travel_plan(trips)
        self._delay = timedelta(minutes=delay)
        self._lines = None
        self._departureboard = None
        self._state = None
        self._alert_eta = None
        self._attributes = None

    def get_station_id(self, location):
        """Get the station ID."""
        if location.isdecimal():
            station_info = {"station_name": location, "station_id": location}
        else:
            station_gid = self._planner.get_locations(location)[0]["gid"]
            station_info = {"station_name": location, "station_id": station_gid}
        return station_info

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def native_value(self):
        """Return the next departure time."""
        return self._state

    def notify(self, message="Your stop is nearing"):
        persistent_notification.async_create(
            self.hass, message,title="Stop nearing alert"
        )
        self.hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self) -> None:
        """Get the departure board."""
        try:
            self._departureboard = self._planner.get_departures_stop_area(
                self._departure["station_id"]
            )
        except:
             _LOGGER.debug("Unable to read departure board, updating token")
             self._planner.update_token()

        if not self._departureboard:
            _LOGGER.debug(
                "No departures from departure station %s to destination station %s",
                self._departure["station_name"],
                self._heading["station_name"] if self._heading else "ANY",
            )
            self._state = "Estimated time not found"
            self._attributes = {}
        else:
            for departure in self._departureboard:
                line = departure["serviceJourney"]["line"].get("shortName")
                if departure.get("isCancelled"):
                    continue
                if not self._lines or line in self._lines:
                    params = {}
                    travel_info = ""
                    if self._heading:
                        journeys = self._planner.get_journeys(self._departure.get('station_id'), self._heading.get('station_id'))
                        trips = self.jpi.possible_trips(self._departure.get('station_id'), self._heading.get('station_id'))
                        eta = self.jpi.get_eta(trips)
                        if not self._alert_eta:
                            self._alert_eta = eta
                        for e in self._alert_eta:
                            if self.jpi.compare_time(e) <= 0:
                                eta_alert ="We are now nearing "+self._heading["station_name"]+". Get ready to get off ;)"
                                self.notify(message=eta_alert)

                        journey_details = journeys["results"][1]["tripLegs"][0]["serviceJourney"]

                        trips = self.jpi.possible_trips(self._departure["station_id"],self._heading["station_id"])

                        travel_info = self.jpi.advanced_travel_plan(trips)
                        param_nr = 0
                        for x in range(len(travel_info)):
                            if x == 0:
                                self._state = travel_info[x]
                            else:
                                params[str(x) + "."] = travel_info[x]
                            param_nr = x
                        params[str(param_nr + 1) + " ."] = "Wheel chair accessible" if journey_details["line"].get("isWheelchairAccessible") else "Not wheel chair accessible"

                    self._attributes = params
                    break


