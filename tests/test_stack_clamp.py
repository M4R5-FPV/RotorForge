"""Combined FC clamp and optional strap controls, independent of FreeCAD."""
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters, PLATE_DESIGNS, TWO_PLATE_ARM_POSITIONS, STANDOFF_COUNTS, arm_brace_layouts, plate_levels, standoff_layouts, stack_reference_z, stack_mounting_role, bottom_stack_hole_diameter, strap_slots, validate, save_parameters, load_parameters
from tests.frame_cases import FRAME_CASES, FPV_CASES


class StackClampTests(unittest.TestCase):
    def test_one_clamp_covers_all_arms_and_fc(self):
        for preset in FRAME_CASES.values():
            for position in TWO_PLATE_ARM_POSITIONS:
                for count in STANDOFF_COUNTS:
                    p=replace(preset,PlateDesign='2 plates',ArmBracesEnabled=True,TwoPlateArmPosition=position,StandoffCount=count)
                    self.assertEqual(validate(p)[0],[])
                    clamps=arm_brace_layouts(p)
                    self.assertEqual(len(clamps),1)
                    upper=position=='Above bottom plate'
                    self.assertEqual(clamps[0]['role'],'ArmClampPlate' if upper else 'ArmLowerClampPlate')
                    self.assertEqual(len(clamps[0]['bolts']),8)
                    self.assertEqual(len(clamps[0]['stack_holes']),4)
                    self.assertEqual(stack_mounting_role(p),'ArmClampPlate' if upper else 'BottomPlate')
                    self.assertEqual(plate_levels(p)['stack_deck_z'],clamps[0]['z']+clamps[0]['thickness'] if upper else p.BottomThickness)
                    self.assertEqual(next(s['length'] for s in standoff_layouts(p) if s['position']=='Rear'),p.StandoffHeight)

    def test_access_holes_are_distinct_from_stack_mounting(self):
        p=Parameters()
        self.assertEqual(bottom_stack_hole_diameter(p),6)
        self.assertEqual(p.StackHoleDiameter,3.2)
        p=replace(p,PlateDesign='2 plates')
        self.assertEqual(bottom_stack_hole_diameter(p),3.2)
        p=replace(p,ArmBracesEnabled=True)
        self.assertEqual(bottom_stack_hole_diameter(p),3.2)
        p=replace(p,TwoPlateArmPosition='Above bottom plate')
        self.assertEqual(bottom_stack_hole_diameter(p),6)
        self.assertTrue(validate(replace(p,StackAccessDiameter=2))[0])

    def test_stack_envelope_follows_carrier(self):
        for position in TWO_PLATE_ARM_POSITIONS:
            p=replace(Parameters(),PlateDesign='2 plates',ArmBracesEnabled=True,TwoPlateArmPosition=position)
            deck=p.BottomThickness+p.ArmThickness+p.ArmBraceThickness if position=='Above bottom plate' else p.BottomThickness
            self.assertEqual(stack_reference_z(p),deck+p.StackMountHeight)

    def test_strap_geometry_and_checks_can_be_disabled(self):
        p=Parameters()
        self.assertEqual(len(strap_slots(p)),4)
        self.assertTrue(validate(replace(p,StrapSlotWidth=20))[0])
        p=replace(p,StrapSlotsEnabled=False,StrapSlotWidth=20,StrapSlotLength=0,StrapEdgeInset=0)
        self.assertEqual(strap_slots(p),())
        self.assertEqual(validate(p)[0],[])
        self.assertTrue(validate(replace(p,StrapSlotsEnabled=True))[0])

    def test_new_settings_round_trip_and_legacy_defaults(self):
        old=Parameters.from_dict({'PlateDesign':'2 plates','ArmBracesEnabled':True})
        self.assertTrue(old.StrapSlotsEnabled)
        self.assertEqual(old.StackAccessDiameter,6)
        p=replace(old,StrapSlotsEnabled=False,StackMountHeight=4,StackHeight=16)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'clamp.json';save_parameters(path,p)
            self.assertEqual(load_parameters(path),p)
        with self.assertRaises(ValueError):Parameters.from_dict({'StrapSlotsEnabled':'no'})


if __name__=='__main__':unittest.main()
