"""Run with ordinary Python: python -m unittest discover -s tests -v."""
from dataclasses import replace
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters, motor_centres, arm_layouts, validate, save_parameters, load_parameters, PLATE_DESIGNS, bottom_bounds, mid_bounds, plate_levels, standoff_layouts, standoff_heights, STANDOFF_COUNTS, standoff_holes, standoff_pairs, standoff_pair_count
from tests.frame_cases import FRAME_CASES, FPV_CASES


class LayoutTests(unittest.TestCase):
    def test_all_standoff_counts_and_presets(self):
        for name, preset in FRAME_CASES.items():
            for mode in PLATE_DESIGNS:
                for count, number in zip(STANDOFF_COUNTS, (4, 6, 8)):
                    with self.subTest(preset=name, mode=mode, count=number):
                        p = replace(preset, PlateDesign=mode, StandoffCount=count)
                        self.assertEqual(validate(p)[0], [])
                        self.assertEqual(len(standoff_holes(p)), number)
                        self.assertEqual(standoff_pair_count(p), number // 2)
                        self.assertEqual(len(set(standoff_holes(p))), number)
                        for pair in standoff_pairs(p):
                            self.assertIn((-pair['width']/2, pair['y']), standoff_holes(p))
                            self.assertIn((pair['width']/2, pair['y']), standoff_holes(p))
                        stands = standoff_layouts(p)
                        self.assertTrue(all(abs(s['base']+s['length']-plate_levels(p)['top_z']) < 1e-8 for s in stands))
                        if mode == '3 plates':
                            self.assertEqual(sum(s['mount']=='Mid plate' for s in stands), 4 if number > 4 else 2)
                        else:
                            self.assertEqual({s['length'] for s in stands}, {25})

    def test_extra_pair_mount_uses_plate_coverage(self):
        p = replace(Parameters(), StandoffCount=STANDOFF_COUNTS[1], StandoffPair3Y=5)
        self.assertEqual(validate(p)[0], [])
        extra = [s for s in standoff_layouts(p) if s['position']=='Pair 3']
        self.assertEqual({s['mount'] for s in extra}, {'Mid plate'})
        self.assertEqual({s['length'] for s in extra}, {25})
        p = replace(p, StandoffPair3Y=41)
        self.assertEqual(validate(p)[0], [])
        extra = [s for s in standoff_layouts(p) if s['position']=='Pair 3']
        self.assertEqual({s['mount'] for s in extra}, {'Bottom plate'})
        self.assertEqual({s['length'] for s in extra}, {33})

    def test_extra_pair_conflicts_are_rejected(self):
        p = replace(Parameters(), StandoffCount=STANDOFF_COUNTS[2])
        for changes in (dict(StandoffPair3Y=-60), dict(StandoffPair3Y=-41, StandoffPair3Width=34),
                        dict(StandoffPair4Y=34, StandoffPair4Width=34), dict(StandoffPair3Width=2),
                        dict(StandoffPair3Width=60), dict(StandoffPair3Y=15.25, StandoffPair3Width=30.5)):
            with self.subTest(changes=changes):
                self.assertTrue(validate(replace(p, **changes))[0])
        self.assertEqual(validate(replace(Parameters(), StandoffPair3Width=0, StandoffPair4Width=0))[0], [])

    def test_old_presets_retain_four_standoffs(self):
        data = Parameters().to_dict()
        for name in tuple(data):
            if name == 'StandoffCount' or name.startswith('StandoffPair'):
                del data[name]
        p = Parameters.from_dict(data)
        self.assertEqual(p.StandoffCount, STANDOFF_COUNTS[0])
        self.assertEqual(len(standoff_holes(p)), 4)

    def test_standoff_layout_json_roundtrip(self):
        p = replace(Parameters(), StandoffCount=STANDOFF_COUNTS[2], StandoffPair3Y=-39,
                    StandoffPair3Width=12, StandoffPair4Y=42, StandoffPair4Width=16)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'eight.json'
            save_parameters(path, p)
            self.assertEqual(load_parameters(path), p)

    def test_stretched_x_widens_motor_span(self):
        p = FRAME_CASES['5-inch Stretched X']
        fr,fl,rl,rr = motor_centres(p)
        width, length = fr[0]-fl[0], fr[1]-rr[1]
        self.assertGreater(width,length)
        self.assertAlmostEqual(width/length,p.LengthToWidth)
        self.assertAlmostEqual(math.dist(fr,rl),p.Wheelbase)
        old_wide = Parameters.from_dict({"Layout":"Stretched X","LengthToWidth":.8})
        self.assertAlmostEqual(old_wide.LengthToWidth,1.25)
        fr,fl,rl,rr = motor_centres(old_wide)
        self.assertAlmostEqual((fr[0]-fl[0])/(fr[1]-rr[1]),1.25)

    def test_common_and_custom_standoff_heights(self):
        for height in (22,25,30,27.5):
            for mode in PLATE_DESIGNS:
                p = replace(Parameters(),PlateDesign=mode,StandoffHeight=height)
                heights = standoff_heights(p)
                self.assertEqual(heights['Rear'],height)
                self.assertEqual(heights['Front'],height+(8 if mode=='3 plates' else 0))
                top = plate_levels(p)['top_z']
                self.assertTrue(all(abs(s['base']+s['length']-top)<1e-9 for s in standoff_layouts(p)))

    def test_presets_and_diagonal_definition(self):
        for name, p in FRAME_CASES.items():
            with self.subTest(name=name):
                self.assertEqual(validate(p)[0], [])
                fr, fl, rl, rr = motor_centres(p)
                self.assertAlmostEqual(math.dist(fr, rl), p.Wheelbase, places=9)
                self.assertAlmostEqual(math.dist(fl, rr), p.Wheelbase, places=9)
                self.assertAlmostEqual(fr[0], -fl[0])
                if p.Layout == "Deadcat":
                    self.assertAlmostEqual(fr[0] / rr[0], p.FrontSpread)
                if p.Layout == "True X":
                    self.assertAlmostEqual(math.dist(fr, fl), math.dist(fr, rr))
                for mode in PLATE_DESIGNS:
                    self.assertEqual(validate(replace(p, PlateDesign=mode))[0], [])

    def test_plate_extents_and_hardware_heights(self):
        three = Parameters()
        two = replace(three, PlateDesign="2 plates")
        self.assertEqual(bottom_bounds(three), (-43.5, 82.5))
        self.assertEqual(mid_bounds(three), (-57.5, 24))
        self.assertEqual(bottom_bounds(two), (-57.5, 57.5))
        self.assertEqual(plate_levels(two)["arm_z"], -5)
        self.assertEqual({s["length"] for s in standoff_layouts(two)}, {25})
        self.assertEqual({s["position"]: s["length"] for s in standoff_layouts(three)}, {"Front":33,"Rear":25})

    def test_short_mid_and_front_standoff_conflicts_rejected(self):
        for p in (replace(Parameters(), MidRearReach=35), replace(Parameters(), MidFrontReach=2),
                  replace(Parameters(), MidFrontReach=50), replace(Parameters(),MidFrontReach=18.5)):
            self.assertTrue(validate(p)[0])
        self.assertEqual(validate(replace(Parameters(), PlateDesign="2 plates", ClampThickness=0,
                                          MidFrontReach=0, MidRearReach=0))[0], [])

    def test_legacy_presets_gain_plate_selector(self):
        legacy = Parameters().to_dict()
        for name in ("PlateDesign", "BottomFrontExtension", "MidFrontReach", "MidRearReach"):
            del legacy[name]
        self.assertEqual(Parameters.from_dict(legacy).PlateDesign,"3 plates")
        legacy["BodyLength"] = 130
        self.assertEqual(Parameters.from_dict(legacy).MidRearReach,65)

    def test_arm_mounts_are_aligned_and_spaced(self):
        for p in FRAME_CASES.values():
            for arm in arm_layouts(p):
                a, b = arm["bolts"]
                self.assertAlmostEqual(math.dist(a, b), p.RootBoltSpacing)
                self.assertAlmostEqual((a[0] + b[0]) / 2, arm["root"][0])
                self.assertAlmostEqual((a[1] + b[1]) / 2, arm["root"][1])

    def test_overlapping_props_rejected(self):
        errors, _ = validate(replace(Parameters(), Wheelbase=160))
        self.assertTrue(any("Propellers overlap" in error for error in errors))

    def test_motor_bolt_edge_clearance(self):
        p = replace(Parameters(), MotorBoltCircle=19*math.sqrt(2), MotorHoleRotation=45)
        self.assertTrue(any("Motor pad" in error for error in validate(p)[0]))
        self.assertEqual(validate(replace(p, MotorPadDiameter=36))[0], [])

    def test_stack_conflict_and_crossing_arm_tails_rejected(self):
        self.assertTrue(validate(replace(Parameters(), StackOffsetY=15))[0])
        self.assertTrue(any("arms intersect" in error for error in validate(replace(Parameters(), RootExtension=35))[0]))

    def test_json_roundtrip_and_untrusted_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frame.json"
            p = FRAME_CASES['5-inch Deadcat']
            save_parameters(path, p)
            self.assertEqual(load_parameters(path), p)
            path.write_text('{"schema":"wrong","units":"mm","parameters":{}}')
            with self.assertRaises(ValueError):
                load_parameters(path)
        for data in ({"Wheelbase": float("nan")}, {"ArmWidth": True}, {"Wheelbase": "250"},
                     {"ShowReferences": "yes"}, {"Layout": "H"}, {"PlateDesign":"4 plates"},
                     {"StandoffCount": 6}, {"StandoffCount": "10 (5 pairs)"}, {"unknown": 1}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                Parameters.from_dict(data)


if __name__ == "__main__":
    unittest.main()
