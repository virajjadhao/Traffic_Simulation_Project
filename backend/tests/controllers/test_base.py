from typing import Any, Dict, List

import pytest

from src.controllers.base import BaseController
from src.vehicles.vehicle import Vehicle


class DummyController(BaseController):
    """A valid subclass of BaseController that implements all abstract methods."""

    def __init__(self) -> None:
        self.tick_count = 0
        self.is_reset = False

    def update(self, delta_time: float, active_vehicles: List[Vehicle]) -> None:
        self.tick_count += 1

    def get_state(self) -> Dict[str, Any]:
        return {"type": "dummy", "timeInCurrentState": 0.0}

    def reset(self) -> None:
        self.is_reset = True
        self.tick_count = 0


def test_cannot_instantiate_abstract_base_class() -> None:
    # Attempting to instantiate BaseController directly must raise TypeError
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        BaseController()  # type: ignore[abstract]


def test_instantiate_valid_subclass() -> None:
    # Instantiating a subclass implementing all methods should succeed
    controller = DummyController()
    assert isinstance(controller, BaseController)

    # Call methods to verify correctness
    controller.update(0.1, [])
    assert controller.tick_count == 1

    assert controller.get_state() == {"type": "dummy", "timeInCurrentState": 0.0}

    controller.reset()
    assert controller.is_reset is True
    assert controller.tick_count == 0


def test_cannot_instantiate_incomplete_subclass() -> None:
    # Subclass missing the update method
    class IncompleteController(BaseController):
        def get_state(self) -> Dict[str, Any]:
            return {}

        def reset(self) -> None:
            pass

    with pytest.raises(
        TypeError, match="Can't instantiate abstract class IncompleteController"
    ):
        IncompleteController()  # type: ignore[abstract]
