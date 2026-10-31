"""Optional arm sandwiches and FPV cover dimensions without the CAD kernel."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters, TWO_PLATE_ARM_POSITIONS, plate_levels, standoff_layouts, arm_brace_layouts, arm_clamp_grip, top_bounds, top_interior_distance, validate
from tests.frame_cases import FRAME_CASES, FPV_CASES
from freecad.rotorforge.fpv import camera_slots,camera_cage_height


class ArmOptionTests(unittest.TestCase):
    def test_backwards_compatible_defaults(self):
        p=Parameters.from_dict({})
        self.assertFalse(p.KeystoneEnabled or p.ArmBracesEnabled)
        self.assertEqual(p.TwoPlateArmPosition,'Below bottom plate')
        self.assertEqual(plate_levels(replace(p,PlateDesign='2 plates'))['arm_z'],-5)

    def test_two_plate_placement_and_grip(self):
        for position in TWO_PLATE_ARM_POSITIONS:
            for brace in (False,True):
                p=replace(Parameters(),PlateDesign='2 plates',TwoPlateArmPosition=position,ArmBracesEnabled=brace)
                self.assertEqual(validate(p)[0],[])
                self.assertEqual(arm_clamp_grip(p),7+(2 if brace else 0))
                self.assertEqual(plate_levels(p)['arm_z'],2 if position.startswith('Above') else -5)
                if brace:
                    self.assertEqual([len(b['bolts']) for b in arm_brace_layouts(p)],[8])
                    self.assertEqual(arm_brace_layouts(p)[0]['z'],7 if position.startswith('Above') else -7)

    def test_rear_actual_height_with_mixed_mounts(self):
        for rear,front in (('Custom position','Arm outer hole'),('Arm inner hole','Custom position'),
                           ('Arm outer hole','Arm inner hole')):
            p=replace(Parameters(),PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',
                      ArmBracesEnabled=True,TopWidth=50,StandoffRearMount=rear,StandoffFrontMount=front)
            stands=standoff_layouts(p)
            self.assertEqual(validate(p)[0],[])
            self.assertEqual(next(s['length'] for s in stands if s['position']=='Rear'),p.StandoffHeight)
            self.assertTrue(all(s['base']+s['length']==plate_levels(p)['top_z'] for s in stands))
            self.assertEqual(camera_cage_height(p),plate_levels(p)['top_z']-2)
            for s in stands:
                if s['shared_arm']:
                    self.assertEqual(s['base'],9)
                    self.assertEqual(s['grip_length'],9)

    def test_irrelevant_options_are_ignored(self):
        p=replace(Parameters(),ArmBracesEnabled=True,ArmBraceThickness=0,TwoPlateArmPosition='Above bottom plate')
        self.assertEqual(arm_brace_layouts(p),())
        self.assertEqual(validate(p)[0],[])
        p=replace(p,PlateDesign='2 plates',ArmBracesEnabled=False,KeystoneEnabled=True,KeystoneClearance=-1)
        self.assertEqual(validate(p)[0],[])

    def test_fpv_front_recess_is_explicit_and_supports_tabs(self):
        p=Parameters(FPVEnabled=True,TopFrontShape='Camera U recess',TopFrontRecessWidth=14.,TopFrontDepth=30.,TopFrontSetback=0.)
        self.assertEqual(validate(p)[0],[])
        self.assertLess(top_interior_distance((0,top_bounds(p)[1]-5),p),0)
        for a,b,r in camera_slots(p,'TopPlate'):
            self.assertGreaterEqual(min(top_interior_distance(q,p) for q in (a,b)),r+p.MinimumWeb-1e-6)

    def test_vtx_cover_and_clearance(self):
        p=replace(Parameters(),FPVEnabled=True)
        self.assertLessEqual(top_bounds(p)[0],p.VTXOffsetY-p.VTXLength/2-p.MinimumWeb)
        self.assertTrue(validate(replace(p,VTXHeight=30))[0])
        self.assertTrue(validate(replace(p,TopWidth=35))[0])


if __name__=='__main__':unittest.main()
