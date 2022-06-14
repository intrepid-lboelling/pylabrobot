""" Tests for LiquidHandler """
# pylint: disable=missing-class-docstring

import io
import textwrap
import unittest
import unittest.mock

from . import backends
from .liquid_handler import LiquidHandler
from .resources import Coordinate, TIP_CAR_480_A00, PLT_CAR_L5AC_A00, Cos_96_DW_1mL, Cos_96_DW_500ul
from .resources.ml_star import STF_L, HTF_L


class TestLiquidHandlerLayout(unittest.TestCase):
  def setUp(self):
    star = backends.STAR()
    self.lh = LiquidHandler(star)

  def test_resource_assignment(self):
    tip_car = TIP_CAR_480_A00(name="tip carrier")
    tip_car[0] = STF_L(name="tips_01")
    tip_car[1] = STF_L(name="tips_02")
    tip_car[3] = HTF_L("tips_04")

    plt_car = PLT_CAR_L5AC_A00(name="plate carrier")
    plt_car[0] = Cos_96_DW_1mL(name="aspiration plate")
    plt_car[2] = Cos_96_DW_500ul(name="dispense plate")

    self.lh.assign_resource(tip_car, rails=1)
    self.lh.assign_resource(plt_car, rails=21)

    # Test placing a carrier at a location where another carrier is located.
    with self.assertRaises(ValueError):
      dbl_plt_car_1 = PLT_CAR_L5AC_A00(name="double placed carrier 1")
      self.lh.assign_resource(dbl_plt_car_1, rails=1)

      dbl_plt_car_2 = PLT_CAR_L5AC_A00(name="double placed carrier 2")
      self.lh.assign_resource(dbl_plt_car_2, rails=2)

      dbl_plt_car_3 = PLT_CAR_L5AC_A00(name="double placed carrier 3")
      self.lh.assign_resource(dbl_plt_car_3, rails=20)

    # Test carrier with same name.
    with self.assertRaises(ValueError):
      same_name_carrier = PLT_CAR_L5AC_A00(name="plate carrier")
      self.lh.assign_resource(same_name_carrier, rails=10)
    # Should not raise when replacing.
    self.lh.assign_resource(same_name_carrier, rails=10, replace=True)
    # Should not raise when unassinged.
    self.lh.unassign_resource("plate carrier")
    self.lh.assign_resource(same_name_carrier, rails=10, replace=True)

    # Test unassigning unassigned resource
    self.lh.unassign_resource("plate carrier")
    with self.assertRaises(KeyError):
      self.lh.unassign_resource("plate carrier")
    with self.assertRaises(KeyError):
      self.lh.unassign_resource("this resource is completely new.")

    # Test invalid rails.
    with self.assertRaises(ValueError):
      self.lh.assign_resource(plt_car, rails=-1)
    with self.assertRaises(ValueError):
      self.lh.assign_resource(plt_car, rails=42)
    with self.assertRaises(ValueError):
      self.lh.assign_resource(plt_car, rails=27)

  def test_get_resource(self):
    tip_car = TIP_CAR_480_A00(name="tip carrier")
    tip_car[0] = STF_L(name="tips_01")
    plt_car = PLT_CAR_L5AC_A00(name="plate carrier")
    plt_car[0] = Cos_96_DW_1mL(name="aspiration plate")
    self.lh.assign_resource(tip_car, rails=1)
    self.lh.assign_resource(plt_car, rails=10)

    # Get resource.
    self.assertEqual(self.lh.get_resource("tip carrier").name, "tip carrier")
    self.assertEqual(self.lh.get_resource("plate carrier").name, "plate carrier")

    # Get subresource.
    self.assertEqual(self.lh.get_resource("tips_01").name, "tips_01")
    self.assertEqual(self.lh.get_resource("aspiration plate").name, "aspiration plate")

    # Get unknown resource.
    self.assertIsNone(self.lh.get_resource("unknown resource"))

  def test_subcoordinates(self):
    tip_car = TIP_CAR_480_A00(name="tip carrier")
    tip_car[0] = STF_L(name="tips_01")
    tip_car[3] = HTF_L(name="tips_04")
    plt_car = PLT_CAR_L5AC_A00(name="plate carrier")
    plt_car[0] = Cos_96_DW_1mL(name="aspiration plate")
    plt_car[2] = Cos_96_DW_500ul(name="dispense plate")
    self.lh.assign_resource(tip_car, rails=1)
    self.lh.assign_resource(plt_car, rails=10)

    # Rails 10 should be left of rails 1.
    self.assertGreater(self.lh.get_resource("plate carrier").location.x,
                       self.lh.get_resource("tip carrier").location.x)

    # Verified with Hamilton Method Editor.
    # Carriers.
    self.assertEqual(self.lh.get_resource("tip carrier").location,
                     Coordinate(100.0, 63.0, 100.0))
    self.assertEqual(self.lh.get_resource("plate carrier").location,
                     Coordinate(302.5, 63.0, 100.0))

    # Subresources.
    self.assertEqual(self.lh.get_resource("tips_01").location,
                     Coordinate(117.900, 145.800, 164.450))
    self.assertEqual(self.lh.get_resource("tips_04").location,
                     Coordinate(117.900, 433.800, 131.450))

    self.assertEqual(self.lh.get_resource("dispense plate").location,
                     Coordinate(320.500, 338.000, 188.150))
    self.assertEqual(self.lh.get_resource("aspiration plate").location,
                     Coordinate(320.500, 146.000, 187.150))

  def build_layout(self):
    tip_car = TIP_CAR_480_A00(name="tip carrier")
    tip_car[0] = STF_L(name="tips_01")
    tip_car[1] = STF_L(name="tips_02")
    tip_car[3] = HTF_L("tips_04")

    plt_car = PLT_CAR_L5AC_A00(name="plate carrier")
    plt_car[0] = Cos_96_DW_1mL(name="aspiration plate")
    plt_car[2] = Cos_96_DW_500ul(name="dispense plate")

    self.lh.assign_resource(tip_car, rails=1, replace=True)
    self.lh.assign_resource(plt_car, rails=21, replace=True)

  @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
  def test_summary(self, out):
    with self.assertRaises(ValueError):
      self.lh.summary()

    self.build_layout()
    self.maxDiff = None # pylint: disable=invalid-name
    expected_out = textwrap.dedent("""
    Rail     Resource                   Type                Coordinates (mm)
    ===============================================================================================
    (1)  ├── tip carrier                TIP_CAR_480_A00     (100.000, 063.000, 100.000)
         │   ├── tips_01                STF_L               (117.900, 145.800, 164.450)
         │   ├── tips_02                STF_L               (117.900, 241.800, 164.450)
         │   ├── <empty>
         │   ├── tips_04                HTF_L               (117.900, 433.800, 131.450)
         │   ├── <empty>
         │
    (21) ├── plate carrier              PLT_CAR_L5AC_A00    (550.000, 063.000, 100.000)
         │   ├── aspiration plate       Cos_96_DW_1mL       (568.000, 146.000, 187.150)
         │   ├── <empty>
         │   ├── dispense plate         Cos_96_DW_500ul     (568.000, 338.000, 188.150)
         │   ├── <empty>
         │   ├── <empty>
    """[1:])
    self.lh.summary()
    self.assertEqual(out.getvalue(), expected_out)

  def test_parse_lay_file(self):
    fn = "./pyhamilton/testing/test_data/test_deck.lay"
    self.lh.load_from_lay_file(fn)

    self.assertEqual(self.lh.get_resource("TIP_CAR_480_A00_0001").location, \
                     Coordinate(122.500, 63.000, 100.000))
    self.assertEqual(self.lh.get_resource("tips_01").location, \
                     Coordinate(140.400, 145.800, 164.450))
    self.assertEqual(self.lh.get_resource("STF_L_0001").location, \
                     Coordinate(140.400, 241.800, 164.450))
    self.assertEqual(self.lh.get_resource("tips_04").location, \
                     Coordinate(140.400, 433.800, 131.450))

    self.assertEqual(self.lh.get_resource("TIP_CAR_480_A00_0001")[0].name, "tips_01")
    self.assertEqual(self.lh.get_resource("TIP_CAR_480_A00_0001")[1].name, "STF_L_0001")
    self.assertIsNone(self.lh.get_resource("TIP_CAR_480_A00_0001")[2])
    self.assertEqual(self.lh.get_resource("TIP_CAR_480_A00_0001")[3].name, "tips_04")
    self.assertIsNone(self.lh.get_resource("TIP_CAR_480_A00_0001")[4])

    self.assertEqual(self.lh.get_resource("PLT_CAR_L5AC_A00_0001").location, \
                     Coordinate(302.500, 63.000, 100.000))
    self.assertEqual(self.lh.get_resource("Cos_96_DW_1mL_0001").location, \
                     Coordinate(320.500, 146.000, 187.150))
    self.assertEqual(self.lh.get_resource("Cos_96_DW_500ul_0001").location, \
                     Coordinate(320.500, 338.000, 188.150))
    self.assertEqual(self.lh.get_resource("Cos_96_DW_1mL_0002").location, \
                     Coordinate(320.500, 434.000, 187.150))
    self.assertEqual(self.lh.get_resource("Cos_96_DW_2mL_0001").location, \
                     Coordinate(320.500, 530.000, 187.150))

    self.assertEqual(self.lh.get_resource("PLT_CAR_L5AC_A00_0001")[0].name, "Cos_96_DW_1mL_0001")
    self.assertIsNone(self.lh.get_resource("PLT_CAR_L5AC_A00_0001")[1])
    self.assertEqual(self.lh.get_resource("PLT_CAR_L5AC_A00_0001")[2].name, "Cos_96_DW_500ul_0001")
    self.assertEqual(self.lh.get_resource("PLT_CAR_L5AC_A00_0001")[3].name, "Cos_96_DW_1mL_0002")
    self.assertEqual(self.lh.get_resource("PLT_CAR_L5AC_A00_0001")[4].name, "Cos_96_DW_2mL_0001")

    self.assertEqual(self.lh.get_resource("PLT_CAR_L5AC_A00_0002").location, \
                     Coordinate(482.500, 63.000, 100.000))
    self.assertEqual(self.lh.get_resource("Cos_96_DW_1mL_0003").location, \
                     Coordinate(500.500, 146.000, 187.150))
    self.assertEqual(self.lh.get_resource("Cos_96_DW_500ul_0003").location, \
                     Coordinate(500.500, 242.000, 188.150))
    self.assertEqual(self.lh.get_resource("Cos_96_PCR_0001").location, \
                     Coordinate(500.500, 434.000, 186.650))

    self.assertEqual(self.lh.get_resource("PLT_CAR_L5AC_A00_0002")[0].name, "Cos_96_DW_1mL_0003")
    self.assertEqual(self.lh.get_resource("PLT_CAR_L5AC_A00_0002")[1].name, "Cos_96_DW_500ul_0003")
    self.assertIsNone(self.lh.get_resource("PLT_CAR_L5AC_A00_0002")[2])
    self.assertEqual(self.lh.get_resource("PLT_CAR_L5AC_A00_0002")[3].name, "Cos_96_PCR_0001")
    self.assertIsNone(self.lh.get_resource("PLT_CAR_L5AC_A00_0002")[4])

  def test_parse_json_file(self):
    pass

  def test_serialize_json(self):
    pass


if __name__ == "__main__":
  unittest.main()
