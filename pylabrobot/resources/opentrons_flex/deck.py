import textwrap
from typing import Optional, List

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.deck import Deck
from pylabrobot.resources.resource import Resource
from pylabrobot.resources.trash import Trash


class OTDeck(Deck):
  """ The Opentrons deck for the flex robot. """

  def __init__(self, size_x: float = 624.3, size_y: float = 565.2, size_z: float = 900,
    origin: Coordinate = Coordinate(0, 0, 0),
    no_trash: bool = False, name: str = "deck"):
    # size_z is probably wrong

    super().__init__(size_x=size_x, size_y=size_y, size_z=size_z, origin=origin)

    self.slots = {
      "A1": None,
      "A2": None,
      "A3": None,
      "B1": None,
      "B2": None,
      "B3": None,
      "C1": None,
      "C2": None,
      "C3": None,
      "D1": None,
      "D2": None,
      "D3": None,
      "D4": None, # staging slot 13
      "C4": None, # staging slot 14
      "B4": None, # staging slot 15
      "A4": None, # staging slot 16
    }


    self.slot_locations = {
      "A1": Coordinate(x=0.0,   y=0.0,   z=0.0),
      "A2": Coordinate(x=132.5, y=0.0,   z=0.0),
      "A3": Coordinate(x=265.0, y=0.0,   z=0.0),
      "B1": Coordinate(x=0.0,   y=90.5,  z=0.0),
      "B2": Coordinate(x=132.5, y=90.5,  z=0.0),
      "B3": Coordinate(x=265.0, y=90.5,  z=0.0),
      "C1": Coordinate(x=0.0,   y=181.0, z=0.0),
      "C2": Coordinate(x=132.5, y=181.0, z=0.0),
      "C3": Coordinate(x=265.0, y=181.0, z=0.0),
      "D1": Coordinate(x=0.0,   y=271.5, z=0.0),
      "D2": Coordinate(x=132.5, y=271.5, z=0.0),
      "D3": Coordinate(x=265.0, y=271.5, z=0.0),
      "D4": Coordinate(x=397.5, y=271.5, z=14.51), # staging slot 13
      "C4": Coordinate(x=397.5, y=181.0, z=14.51), # staging slot 14
      "B4": Coordinate(x=397.5, y=90.5,  z=14.51), # staging slot 15
      "A4": Coordinate(x=397.5, y=0.0,   z=14.51), # staging slot 16
    }

    if not no_trash:
      self._assign_trash()

  def _assign_trash(self):
    """ Assign the trash area to the deck.

    Because all opentrons operations require that the resource passed references a parent, we need
    to create a dummy resource to represent the container of the actual trash area.
    """

    trash_container = Resource(
      name="trash_container",
      size_x=172.86,
      size_y=165.86,
      size_z=82,
    )

    actual_trash = Trash(
      name="trash",
      size_x=172.86,
      size_y=165.86,
      size_z=82,
    )

    # Trash location used to be Coordinate(x=86.43, y=82.93, z=0),
    # this is approximately the center of the trash area.
    # LiquidHandler will now automatically find the center of the trash before discarding tips,
    # so this location is no longer needed and we just use Coordinate.zero().
    # The actual location of the trash is determined by the slot number (10).
    trash_container.assign_child_resource(actual_trash, location=Coordinate.zero())
    self.assign_child_at_slot(trash_container, "D1")


  def assign_child_resource(
    self,
    resource: Resource,
    location: Coordinate,
    reassign: bool = True
  ):
    """ Assign a resource to a slot.

    ..warning:: This method exists only for deserialization. You should use
    :meth:`assign_child_at_slot` instead.
    """
    if location in self.slot_locations.keys():
      super().assign_child_resource(resource, location=location)
    else:
      raise ValueError("invalid slot assignment")

  def assign_child_at_slot(self, resource: Resource, slot: str):
    # pylint: disable=arguments-renamed
    if slot in self.slot_locations.keys():
      super().assign_child_resource(resource, location=self.slot_locations[slot])
      self.slots[slot]= resource
    else: raise ValueError("Invalid slot")


  def unassign_child_resource(self, resource: Resource):
    if resource not in self.slots.values():
      raise ValueError(f"Resource {resource.name} is not assigned to this deck")

    for key, value in self.slots.items():
      if value.name == resource.name:
          self.slots[key] = None
    super().unassign_child_resource(resource)

  def get_slot(self, resource: Resource) -> str:
    """ Get the slot number of a resource. """

    for key, value in self.slots.items():
      if value is not None:
        if value.name == resource.name:
            return key


  def summary(self) -> str:
    """ Get a summary of the deck.

    >>> print(deck.summary())

    Deck: 624.3mm x 565.2mm

    +-----------------+-----------------+-----------------+-----------------+
    |                 |                 |                 |                 |
    | 10: Trash       | 11: Empty       | 12: Empty       | 13: Empty       |
    |                 |                 |                 |                 |
    +-----------------+-----------------+-----------------+-----------------+
    |                 |                 |                 |                 |
    |  7: tip_rack_1  |  8: tip_rack_2  |  9: tip_rack_3  | 14: Empty       |
    |                 |                 |                 |                 |
    +-----------------+-----------------+-----------------+-----------------+
    |                 |                 |                 |                 |
    |  4: my_plate    |  5: my_other... |  6: Empty       | 15: Empty       |
    |                 |                 |                 |                 |
    +-----------------+-----------------+-----------------+-----------------+
    |                 |                 |                 |                 |
    |  1: Empty       |  2: Empty       |  3: Empty       | 16: Empty       |
    |                 |                 |                 |                 |
    +-----------------+-----------------+-----------------+-----------------+
    """

    def _get_slot_name(slot: str) -> str:
      """ Get slot name, or 'Empty' if slot is empty. If the name is too long, truncate it. """
      length = 11
      resource = self.slots[slot]
      if resource is None:
        return "Empty".ljust(length)
      name = resource.name
      if len(name) > 10:
        name = name[:8] + "..."
      return name.ljust(length)

    summary_ = f"""
      Deck: {self.get_size_x()}mm x {self.get_size_y()}mm

      +-----------------+-----------------+-----------------+-----------------+
      |                 |                 |                 |                 |
      |  D1: {_get_slot_name("D1")} | D2: {_get_slot_name("D2")} | D3: {_get_slot_name("D3")} | D4: {_get_slot_name("D4")} |
      |                 |                 |                 |                 |
      +-----------------+-----------------+-----------------+-----------------+
      |                 |                 |                 |                 |
      |  C1: {_get_slot_name("C1")} |  C2: {_get_slot_name("C2")} |  C3: {_get_slot_name("C3")} | C4: {_get_slot_name("C4")} |
      |                 |                 |                 |                 |
      +-----------------+-----------------+-----------------+-----------------+
      |                 |                 |                 |                 |
      |  B1: {_get_slot_name("B1")} |  B2: {_get_slot_name("B2")} |  B3: {_get_slot_name("B3")} | B4: {_get_slot_name("B4")} |
      |                 |                 |                 |                 |
      +-----------------+-----------------+-----------------+-----------------+
      |                 |                 |                 |                 |
      |  A1: {_get_slot_name("A1")} |  A2: {_get_slot_name("A2")} |  A3: {_get_slot_name("A3")} | A4: {_get_slot_name("A4")} |
      |                 |                 |                 |                 |
      +-----------------+-----------------+-----------------+-----------------+
    """


    return textwrap.dedent(summary_)
