from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DOMAIN
from .coordinator import ZeppCloudCoordinator


@dataclass(frozen=True, kw_only=True)
class ZeppSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def val(key: str):
    return lambda data: data.get(key)


SENSORS: tuple[ZeppSensorDescription, ...] = (
    ZeppSensorDescription(
        key="heart_rate",
        translation_key="heart_rate",
        icon="mdi:heart-pulse",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("heart_rate"),
        attrs_fn=lambda d: {
            "measurement_time": _iso(d.get("heart_rate_time")),
            "samples_today": d.get("heart_rate_samples_today"),
        },
    ),
    ZeppSensorDescription(
        key="heart_rate_age",
        translation_key="heart_rate_age",
        icon="mdi:clock-alert-outline",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("heart_rate_age_min"),
    ),
    ZeppSensorDescription(
        key="heart_rate_min_today",
        translation_key="heart_rate_min_today",
        icon="mdi:heart-minus",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("heart_rate_min_today"),
    ),
    ZeppSensorDescription(
        key="heart_rate_max_today",
        translation_key="heart_rate_max_today",
        icon="mdi:heart-plus",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("heart_rate_max_today"),
    ),
    ZeppSensorDescription(
        key="heart_rate_avg_today",
        translation_key="heart_rate_avg_today",
        icon="mdi:heart",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("heart_rate_avg_today"),
    ),
    ZeppSensorDescription(
        key="sleep_resting_hr",
        translation_key="sleep_resting_hr",
        icon="mdi:heart-outline",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("sleep_resting_hr"),
    ),
    ZeppSensorDescription(
        key="spo2",
        translation_key="spo2",
        icon="mdi:water-percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("spo2"),
        attrs_fn=lambda d: {"measurement_time": _iso(d.get("spo2_time"))},
    ),
    ZeppSensorDescription(
        key="blood_pressure",
        translation_key="blood_pressure",
        icon="mdi:gauge",
        value_fn=val("blood_pressure"),
        attrs_fn=lambda d: {
            "measurement_time": _iso(d.get("blood_pressure_time")),
            "pulse": d.get("blood_pressure_pulse"),
            "source": d.get("blood_pressure_source"),
            "measurements_today": d.get("blood_pressure_measurements_today"),
        },
    ),
    ZeppSensorDescription(
        key="blood_pressure_systolic",
        translation_key="blood_pressure_systolic",
        icon="mdi:arrow-up-bold-circle-outline",
        native_unit_of_measurement="mmHg",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("blood_pressure_systolic"),
    ),
    ZeppSensorDescription(
        key="blood_pressure_diastolic",
        translation_key="blood_pressure_diastolic",
        icon="mdi:arrow-down-bold-circle-outline",
        native_unit_of_measurement="mmHg",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("blood_pressure_diastolic"),
    ),
    ZeppSensorDescription(
        key="blood_pressure_pulse",
        translation_key="blood_pressure_pulse",
        icon="mdi:heart-pulse",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("blood_pressure_pulse"),
    ),
    ZeppSensorDescription(
        key="blood_pressure_measurements_today",
        translation_key="blood_pressure_measurements_today",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("blood_pressure_measurements_today"),
    ),
    ZeppSensorDescription(
        key="blood_pressure_systolic_min_today",
        translation_key="blood_pressure_systolic_min_today",
        icon="mdi:arrow-down",
        native_unit_of_measurement="mmHg",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("blood_pressure_systolic_min_today"),
    ),
    ZeppSensorDescription(
        key="blood_pressure_systolic_max_today",
        translation_key="blood_pressure_systolic_max_today",
        icon="mdi:arrow-up",
        native_unit_of_measurement="mmHg",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("blood_pressure_systolic_max_today"),
    ),
    ZeppSensorDescription(
        key="blood_pressure_systolic_avg_today",
        translation_key="blood_pressure_systolic_avg_today",
        icon="mdi:approximately-equal",
        native_unit_of_measurement="mmHg",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("blood_pressure_systolic_avg_today"),
    ),
    ZeppSensorDescription(
        key="blood_pressure_diastolic_min_today",
        translation_key="blood_pressure_diastolic_min_today",
        icon="mdi:arrow-down",
        native_unit_of_measurement="mmHg",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("blood_pressure_diastolic_min_today"),
    ),
    ZeppSensorDescription(
        key="blood_pressure_diastolic_max_today",
        translation_key="blood_pressure_diastolic_max_today",
        icon="mdi:arrow-up",
        native_unit_of_measurement="mmHg",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("blood_pressure_diastolic_max_today"),
    ),
    ZeppSensorDescription(
        key="blood_pressure_diastolic_avg_today",
        translation_key="blood_pressure_diastolic_avg_today",
        icon="mdi:approximately-equal",
        native_unit_of_measurement="mmHg",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("blood_pressure_diastolic_avg_today"),
    ),
    ZeppSensorDescription(
        key="stress",
        translation_key="stress",
        icon="mdi:head-heart-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("stress"),
        attrs_fn=lambda d: {"measurement_time": _iso(d.get("stress_time"))},
    ),
    ZeppSensorDescription(
        key="stress_min",
        translation_key="stress_min",
        icon="mdi:arrow-down-bold",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("stress_min"),
    ),
    ZeppSensorDescription(
        key="stress_max",
        translation_key="stress_max",
        icon="mdi:arrow-up-bold",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("stress_max"),
    ),
    ZeppSensorDescription(
        key="stress_avg",
        translation_key="stress_avg",
        icon="mdi:approximately-equal",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("stress_avg"),
    ),
    ZeppSensorDescription(
        key="steps",
        translation_key="steps",
        icon="mdi:walk",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=val("steps"),
    ),
    ZeppSensorDescription(
        key="distance",
        translation_key="distance",
        icon="mdi:map-marker-distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=val("distance_km"),
    ),
    ZeppSensorDescription(
        key="calories",
        translation_key="calories",
        icon="mdi:fire",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=val("calories"),
    ),
    ZeppSensorDescription(
        key="active_minutes",
        translation_key="active_minutes",
        icon="mdi:run",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=val("active_minutes"),
    ),
    ZeppSensorDescription(
        key="step_goal",
        translation_key="step_goal",
        icon="mdi:target",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("step_goal"),
    ),
    ZeppSensorDescription(
        key="step_goal_progress",
        translation_key="step_goal_progress",
        icon="mdi:progress-check",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("step_goal_progress"),
    ),
    ZeppSensorDescription(
        key="calorie_goal",
        translation_key="calorie_goal",
        icon="mdi:target",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("calorie_goal"),
    ),
    ZeppSensorDescription(
        key="calorie_goal_progress",
        translation_key="calorie_goal_progress",
        icon="mdi:progress-check",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("calorie_goal_progress"),
    ),
    ZeppSensorDescription(
        key="active_minutes_goal",
        translation_key="active_minutes_goal",
        icon="mdi:target",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("active_minutes_goal"),
    ),
    ZeppSensorDescription(
        key="active_minutes_goal_progress",
        translation_key="active_minutes_goal_progress",
        icon="mdi:progress-check",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("active_minutes_goal_progress"),
    ),
    ZeppSensorDescription(
        key="sleep_score",
        translation_key="sleep_score",
        icon="mdi:sleep",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("sleep_score"),
        attrs_fn=lambda d: {
            "sleep_date": d.get("sleep_date"),
            "awakenings": d.get("sleep_awakenings"),
        },
    ),
    ZeppSensorDescription(
        key="sleep_total",
        translation_key="sleep_total",
        icon="mdi:bed-clock",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("sleep_total_min"),
    ),
    ZeppSensorDescription(
        key="sleep_light",
        translation_key="sleep_light",
        icon="mdi:weather-night",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("sleep_light_min"),
    ),
    ZeppSensorDescription(
        key="sleep_deep",
        translation_key="sleep_deep",
        icon="mdi:power-sleep",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("sleep_deep_min"),
    ),
    ZeppSensorDescription(
        key="sleep_rem",
        translation_key="sleep_rem",
        icon="mdi:brain",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("sleep_rem_min"),
    ),
    ZeppSensorDescription(
        key="sleep_awake",
        translation_key="sleep_awake",
        icon="mdi:eye-outline",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("sleep_awake_min"),
    ),
    ZeppSensorDescription(
        key="sleep_start",
        translation_key="sleep_start",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=val("sleep_start"),
    ),
    ZeppSensorDescription(
        key="sleep_end",
        translation_key="sleep_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=val("sleep_end"),
    ),
    ZeppSensorDescription(
        key="sleep_awakenings",
        translation_key="sleep_awakenings",
        icon="mdi:eye",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("sleep_awakenings"),
    ),
    ZeppSensorDescription(
        key="training_load",
        translation_key="training_load",
        icon="mdi:chart-line",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("training_load"),
    ),
    ZeppSensorDescription(
        key="day_training_load",
        translation_key="day_training_load",
        icon="mdi:chart-timeline-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("day_training_load"),
    ),
    ZeppSensorDescription(
        key="vo2_max",
        translation_key="vo2_max",
        icon="mdi:lungs",
        native_unit_of_measurement="mL/kg/min",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=val("vo2_max"),
    ),
    ZeppSensorDescription(
        key="cloud_checked",
        translation_key="cloud_checked",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=val("cloud_checked_at"),
        attrs_fn=lambda d: {
            "endpoint_failures": d.get("endpoint_failures"),
            "failed_endpoints": d.get("failed_endpoints"),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ZeppCloudCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ZeppCloudSensor(coordinator, entry, description) for description in SENSORS
    )


class ZeppCloudSensor(CoordinatorEntity[ZeppCloudCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZeppCloudCoordinator,
        entry: ConfigEntry,
        description: ZeppSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.data[CONF_NAME],
            manufacturer="Zepp Health / Amazfit",
            model="Zepp Cloud",
        )

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self):
        fn = self.entity_description.attrs_fn
        if not fn:
            return None
        attrs = fn(self.coordinator.data or {})
        return {k: v for k, v in attrs.items() if v is not None}


def _iso(value: Any) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None
