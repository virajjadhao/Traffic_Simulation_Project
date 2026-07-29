from typing import Any, Dict, List

import pytest

from src.controllers.base import BaseController
from src.controllers.fixed_time_signal import FixedTimeSignalController
from src.controllers.registry import ControllerRegistry, register_controller
from src.controllers.roundabout import RoundaboutController
from src.vehicles.vehicle import Vehicle


def test_registry_standard_controllers() -> None:
    """Verify that the standard controllers are correctly registered."""
    cls_signal = ControllerRegistry.get_controller_class("fixed_time_signal")
    assert cls_signal is FixedTimeSignalController

    cls_roundabout = ControllerRegistry.get_controller_class("roundabout")
    assert cls_roundabout is RoundaboutController


def test_registry_error_handling() -> None:
    """Verify that looking up non-existent controllers raises ValueError."""
    with pytest.raises(ValueError, match="is not registered"):
        ControllerRegistry.get_controller_class("invalid_controller_key_123")


def test_registry_custom_registration() -> None:
    """Verify that a custom controller can be dynamically registered."""

    @register_controller("custom_test")
    class CustomTestController(BaseController):
        def update(self, delta_time: float, active_vehicles: List[Vehicle]) -> None:
            pass

        def get_state(self) -> Dict[str, Any]:
            return {"type": "custom_test"}

        def reset(self) -> None:
            pass

    cls_custom = ControllerRegistry.get_controller_class("custom_test")
    assert cls_custom is CustomTestController
