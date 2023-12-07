"""Support for Västtrafik public transport."""
from __future__ import annotations

from datetime import timedelta, datetime
import logging

from homeassistant.components import persistent_notification
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from .vt_utils import JourneyPlanner, JPImpl
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.components.geo_location import GeolocationEvent
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
                vol.Optional(CONF_FROM): cv.string,
                vol.Optional(CONF_DELAY, default=DEFAULT_DELAY): cv.positive_int,
                vol.Optional(CONF_HEADING): cv.string,
                vol.Optional(CONF_LINES, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional(CONF_NAME): cv.string,
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
    for departure in config[CONF_DEPARTURES]:
        loc = planner.get_locations(departure.get(CONF_FROM))[0]
        geo_locations.append(VTGeolocationEvent(loc['name'], loc['latitude'],loc['longitude']))
        sensors.append(
                VasttrafikDepartureSensor(
                    planner,
                    departure.get(CONF_NAME),
                    departure.get(CONF_FROM),
                    departure.get(CONF_HEADING),
                    departure.get(CONF_DELAY),
                    departure.get(CONF_LINES),
                )
            )
    for n in nearby:
        sensors.append(VasttrafikDepartureSensor(
            planner,
            n[0] + " (Nearby)",
            n[0],
            None,
            DEFAULT_DELAY,
            None,
        ))
    add_entities(sensors)
    add_entities(geo_locations)

class VTGeolocationEvent(GeolocationEvent):
    """Represents a geolocation event."""

    _attr_should_poll = False
    _attr_icon = "mdi:bus"

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

    def __init__(self, planner, name, departure, heading, delay, lines=None):
        """Initialize the sensor."""
        self._planner = planner
        self._name = name if name else departure
        self._departure = self.get_station_id(departure)
        self._heading = self.get_station_id(heading) if heading else None
        self.jpi = JPImpl()
        self._attr_description = "-"
        if heading:
            trips = self.jpi.possible_trips(self._departure["station_id"],self._heading["station_id"])
            self._attr_description = self.jpi.advanced_travel_plan(trips)
        self._lines = lines
        self._delay = timedelta(minutes=delay)
        self._departureboard = None
        self._state = None
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

    def notify(self):
        persistent_notification.async_create(
            self.hass, "Your stop is nearing", title="Get off bus alert"
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
                    if departure.get("estimatedTime"):
                        estTime = datetime.fromisoformat(departure.get("estimatedTime"))
                        formatted_timestamp = estTime.strftime('%H:%M')
                        print(self.jpi.compare_time(estTime))
                        self._state = formatted_timestamp
                    heading = self._heading.get('station_name') if self._heading else "-"
                    direction = departure["serviceJourney"].get("direction")
                    line = departure["serviceJourney"]["line"].get("transportMode").capitalize() +" "+departure["serviceJourney"]["line"].get("shortName")
                    accessibility = departure["serviceJourney"]["line"].get("isWheelchairAccessible")
                    if self._heading:
                        journeys = self._planner.get_journeys(self._departure.get('station_id'), self._heading.get('station_id'))
                        journey_details = journeys["results"][0]["tripLegs"][0]["serviceJourney"]
                        direction = journey_details["direction"]
                        accessibility = journey_details["line"].get("isWheelchairAccessible")
                        line = journey_details["line"].get("transportMode").capitalize() +" "+journey_details["line"].get("shortName")
                        trips = self.jpi.possible_trips(self._departure["station_id"],self._heading["station_id"])
                        self._attr_description = self.jpi.advanced_travel_plan(trips)
                    params = {
                        ATTR_ACCESSIBILITY: "Wheel chair accessible" if accessibility else "Not wheel chair accessible",
                        ATTR_DIRECTION: direction,
                        ATTR_HEADING: heading,
                        ATTR_LINE: line,
                        ATTR_TRACK: departure["stopPoint"].get("platform"),
                        ATTR_DESCRIPTION: self._attr_description
                    }

                    self._attributes = {k: v for k, v in params.items() if v}
                    break


