"""Support for MIMO ASR sensors."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MIMO ASR sensor."""
    async_add_entities([MimoAsrSensor(config_entry)])

class MimoAsrSensor(SensorEntity):
    """Representation of a MIMO ASR sensor."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._attr_name = "MIMO ASR Status"
        self._attr_unique_id = f"{config_entry.entry_id}_status"
        self._state = "ready"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        self._state = "ready"
