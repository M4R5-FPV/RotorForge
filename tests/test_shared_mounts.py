"""Coaxial arm mounts, correct front direction, and Deadcat compensation."""
from dataclasses import replace
from pathlib import Path
import math
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters, PLATE_DESIGNS, STANDOFF_COUNTS, arm_layouts, motor_centres, standoff_layouts, standoff_pairs, validate, save_parameters, load_parameters, bottom_bounds, top_bounds, plate_levels
from tests.frame_cases import FRAME_CASES, FPV_CASES
from freecad.rotorforge.fpv import camera_mounts,camera_slots,camera_pivot_height,camera_cage_height


class SharedMountTests(unittest.TestCase):
    def test_snap_all_root_holes_both_plate_modes(self):
        for preset in FRAME_CASES.values():
            for mode in PLATE_DESIGNS:
                p=replace(preset,PlateDesign=mode,TopWidth=50,StandoffCount=STANDOFF_COUNTS[2],
                    StandoffFrontMount='Arm outer hole',StandoffRearMount='Arm outer hole',
                    StandoffPair3Mount='Rear arm inner hole',StandoffPair4Mount='Front arm inner hole')
                self.assertEqual(validate(p)[0],[])
                stands=standoff_layouts(p)
                self.assertEqual({s['point'] for s in stands},{b for a in arm_layouts(p) for b in a['bolts']})
                self.assertTrue(all(s['shared_arm'] for s in stands))
                self.assertEqual({s['length'] for s in stands},{p.StandoffHeight})
                self.assertEqual({s['base'] for s in stands},{plate_levels(p)['deck_z']})
                self.assertEqual({s['grip_length'] for s in stands},{p.BottomThickness+p.ArmThickness+(p.ClampThickness if mode=='3 plates' else 0)})

    def test_manual_alignment_allowed_near_misses_rejected(self):
        p=Parameters(TopWidth=50)
        bolt=arm_layouts(p)[0]['bolts'][1]
        p=replace(p,StandoffWidth=2*bolt[0],StandoffLength=2*bolt[1])
        self.assertEqual(validate(p)[0],[])
        self.assertTrue(all(s['shared_arm'] for s in standoff_layouts(p)))
        self.assertTrue(validate(replace(p,StandoffWidth=p.StandoffWidth+.01))[0])
        self.assertTrue(validate(replace(p,StandoffHoleDiameter=2.2))[0])

    def test_snap_follows_changed_arm_geometry(self):
        p=FPV_CASES['5-inch FPV Deadcat']
        before={s['point'] for s in standoff_layouts(p)}
        p=replace(p,FrontSpread=1.35)
        self.assertEqual(validate(p)[0],[])
        self.assertNotEqual(before,{s['point'] for s in standoff_layouts(p)})
        self.assertTrue(all(s['shared_arm'] for s in standoff_layouts(p)))

    def test_deadcat_front_and_rear_growth(self):
        p=FPV_CASES['5-inch FPV Deadcat']
        previous=None
        for spread in (1,1.05,1.1,1.2,1.3,1.4):
            q=replace(p,FrontSpread=spread)
            self.assertEqual(validate(q)[0],[])
            fr,fl,rl,rr=motor_centres(q)
            self.assertGreater(fr[1],0); self.assertLess(rr[1],0)
            self.assertAlmostEqual(fr[0]/rr[0],spread)
            self.assertAlmostEqual(math.dist(fr,rl),q.Wheelbase)
            self.assertAlmostEqual(math.dist(fl,rr),q.Wheelbase)
            arms=arm_layouts(q)
            self.assertAlmostEqual(arms[0]['length'],arms[2]['length'])
            if previous: self.assertGreater(arms[2]['length'],previous)
            previous=arms[2]['length']

    def test_tabs_capture_bottom_and_top(self):
        for mode in PLATE_DESIGNS:
            p=replace(Parameters(),FPVEnabled=True,StandoffHeight=30,PlateDesign=mode)
            self.assertEqual(validate(p)[0],[])
            for m in camera_mounts(p):
                self.assertEqual(m['z0'],p.BottomThickness)
                self.assertEqual(m['z1'],plate_levels(p)['top_z'])
                self.assertEqual(len(m['tabs_y']),2)
            self.assertGreaterEqual(top_bounds(p)[1],80+p.MinimumWeb)
            self.assertGreaterEqual(bottom_bounds(p)[1],top_bounds(p)[1])
            from freecad.rotorforge.fpv import camera_vertical_limits
            low,high=camera_vertical_limits(p)
            self.assertAlmostEqual(camera_pivot_height(p),camera_cage_height(p)/2)
        p=replace(p,StandoffHeight=22)
        self.assertEqual(validate(p)[0],[])
        p=replace(p,PlateDesign='2 plates')
        self.assertTrue(any('camera does not clear' in e for e in validate(p)[0]))

    def test_new_parameters_roundtrip(self):
        p=replace(FPV_CASES['5-inch FPV Deadcat'],CameraTabClearance=.15)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'frame.json';save_parameters(path,p)
            self.assertEqual(load_parameters(path),p)


if __name__=='__main__':unittest.main()
