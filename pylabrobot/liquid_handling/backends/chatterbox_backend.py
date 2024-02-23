# pylint: disable=unused-argument

from typing import List
import sys

from pylabrobot.liquid_handling.backends.backend import LiquidHandlerBackend
from pylabrobot.resources import Resource
from pylabrobot.liquid_handling.standard import (
    Pickup,
    PickupTipRack,
    Drop,
    DropTipRack,
    Aspiration,
    AspirationPlate,
    Dispense,
    DispensePlate,
    Move,
)


class ChatterBoxBackend(LiquidHandlerBackend):
    """Chatter box backend for 'How to Open Source'"""

    def __init__(self, num_channels: int = 8, file=sys.stdout):
        """Initialize a chatter box backend."""
        super().__init__()
        self._num_channels = num_channels
        self._file = file

    async def setup(self):
        await super().setup()
        print("Setting up the robot.", file=self._file)

    async def stop(self):
        await super().stop()
        print("Stopping the robot.", file=self._file)

    @property
    def num_channels(self) -> int:
        return self._num_channels

    async def assigned_resource_callback(self, resource: Resource):
        print(f"Resource {resource.name} was assigned to the robot.", file=self._file)

    async def unassigned_resource_callback(self, name: str):
        print(f"Resource {name} was unassigned from the robot.", file=self._file)

    async def pick_up_tips(
        self, ops: List[Pickup], use_channels: List[int], **backend_kwargs
    ):
        print(f"Picking up tips {ops}.", file=self._file)

    async def drop_tips(
        self, ops: List[Drop], use_channels: List[int], **backend_kwargs
    ):
        print(f"Dropping tips {ops}.", file=self._file)

    async def aspirate(
        self, ops: List[Aspiration], use_channels: List[int], **backend_kwargs
    ):
        print(f"Aspirating {ops}.", file=self._file)

    async def dispense(
        self, ops: List[Dispense], use_channels: List[int], **backend_kwargs
    ):
        print(f"Dispensing {ops}.", file=self._file)

    async def pick_up_tips96(self, pickup: PickupTipRack, **backend_kwargs):
        print(f"Picking up tips from {pickup.resource.name}.", file=self._file)

    async def drop_tips96(self, drop: DropTipRack, **backend_kwargs):
        print(f"Dropping tips to {drop.resource.name}.", file=self._file)

    async def aspirate96(self, aspiration: AspirationPlate):
        print(f"Aspirating {aspiration.volume} from {aspiration.resource}.", file=self._file)

    async def dispense96(self, dispense: DispensePlate):
        print(f"Dispensing {dispense.volume} to {dispense.resource}.", file=self._file)

    async def move_resource(self, move: Move, **backend_kwargs):
        print(f"Moving {move}.", file=self._file)
