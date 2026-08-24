from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DOMAIN
from .coordinator import ZeppCloudCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ZeppCloudCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZeppCloudRefreshButton(coordinator, entry)])


class ZeppCloudRefreshButton(
    CoordinatorEntity[ZeppCloudCoordinator],
    ButtonEntity,
):
    _attr_has_entity_name = True
    _attr_translation_key = "refresh"
    _attr_icon = "mdi:cloud-sync"

    def __init__(
        self,
        coordinator: ZeppCloudCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.data[CONF_NAME],
            manufacturer="Zepp Health / Amazfit",
            model="Zepp Cloud",
        )

    @property
    def extra_state_attributes(self):
        """Expose compact cloud histories for timestamp-accurate Lovelace charts."""
        data = self.coordinator.data or {}
        return {
            "spo2_measurements": data.get("spo2_history", []),
            "blood_pressure_measurements": data.get("blood_pressure_history", []),
        }

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
