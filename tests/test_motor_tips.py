"""Motor tip directions, retained mounting geometry and relief clearances."""
from dataclasses import replace
from pathlib import Path
import math
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters,LAYOUTS,arm_layouts,validate,save_parameters,load_parameters
from freecad.rotorforge.motor_pads import (MOTOR_PAD_SHAPES,EXTENDED_MOTOR_PAD_SHAPES,
    motor_pad_primitives,motor_pad_interior,motor_pad_bound,motor_tip_slots)


class MotorTipTests(unittest.TestCase):
    def test_new_outlines_keep_the_motor_and_root_patterns(self):
        for layout in LAYOUTS:
            original=Parameters(Layout=layout,Wheelbase=270)
            for shape in EXTENDED_MOTOR_PAD_SHAPES:
                p=replace(original,MotorPadShape=shape)
                self.assertEqual(arm_layouts(p),arm_layouts(original))
                self.assertEqual(validate(p)[0],[])

    def test_each_tip_and_slot_points_away_from_the_body(self):
        for layout in LAYOUTS:
            for shape in EXTENDED_MOTOR_PAD_SHAPES:
                p=Parameters(Layout=layout,Wheelbase=270,MotorPadShape=shape)
                for arm in arm_layouts(p):
                    for a,b,radius in motor_tip_slots(p,arm):
                        for point in (a,b):
                            delta=tuple(point[i]-arm['motor'][i] for i in (0,1))
                            self.assertGreater(sum(delta[i]*arm['unit'][i] for i in (0,1)),p.MotorPadDiameter/2-1)
                            self.assertAlmostEqual(delta[0]*arm['unit'][1]-delta[1]*arm['unit'][0],0)
                    points=motor_pad_primitives(p)[0]['points']
                    self.assertEqual(max(x for x,y in points),p.MotorPadDiameter/2+p.MotorTipLength)

    def test_outline_envelope_includes_the_extended_tip(self):
        for shape in EXTENDED_MOTOR_PAD_SHAPES:
            p=Parameters(MotorBoltCircle=22.627416997969522,MotorHoleRotation=45,MotorPadShape=shape)
            points=motor_pad_primitives(p)[0]['points'];bound=motor_pad_bound(p)
            self.assertTrue(all(math.hypot(x,y)<=bound+1e-9 for x,y in points))
            self.assertGreater(bound,p.MotorPadDiameter/math.sqrt(2))
            self.assertLess(motor_pad_interior((24,0),p),0)

    def test_tip_slot_toggle_preserves_its_dimensions(self):
        p=Parameters(MotorPadShape='Arrowhead',MotorTipSlotWidth=3.5,MotorTipSlotLength=6.5)
        off=replace(p,MotorTipSlotEnabled=False)
        self.assertFalse(motor_tip_slots(off));self.assertEqual(off.MotorTipSlotWidth,3.5)
        self.assertEqual(off.MotorTipSlotLength,6.5)
        self.assertEqual(motor_tip_slots(replace(off,MotorTipSlotEnabled=True)),motor_tip_slots(p))
        self.assertEqual(motor_pad_primitives(off),motor_pad_primitives(p))

    def test_earlier_profiles_ignore_tip_settings(self):
        for shape in MOTOR_PAD_SHAPES[:4]:
            p=Parameters(MotorBoltCircle=22.627416997969522,MotorHoleRotation=45,MotorPadShape=shape,MotorTipLength=-1,MotorTipSlotLength=1,MotorTipSlotWidth=40)
            self.assertEqual(validate(p)[0],[])
            self.assertEqual(motor_tip_slots(p),())

    def test_unsafe_slots_and_tips_are_rejected(self):
        for shape in EXTENDED_MOTOR_PAD_SHAPES:
            p=Parameters(MotorBoltCircle=22.627416997969522,MotorHoleRotation=45,MotorPadShape=shape)
            for changes in ({'MotorTipLength':-1},{'MotorTipSlotLength':2},
                            {'MotorTipSlotLength':24},{'MotorTipSlotWidth':0},
                            {'MotorTipSlotWidth':10,'MotorTipSlotLength':10},
                            {'MotorPadCornerRadius':0}):
                with self.subTest(shape=shape,changes=changes):
                    self.assertTrue(validate(replace(p,**changes))[0])

    def test_tip_slots_follow_their_configured_total_dimensions(self):
        p=Parameters(MotorPadShape='Tapered nose')
        a,b,radius=motor_tip_slots(p)[0]
        self.assertAlmostEqual(math.dist(a,b)+2*radius,p.MotorTipSlotLength)
        self.assertEqual(2*radius,p.MotorTipSlotWidth)
        self.assertGreaterEqual(min(motor_pad_interior(pt,p) for pt in (a,b))-radius,p.MinimumWeb)
        self.assertEqual(validate(replace(p,MotorTipSlotEnabled=False,MotorTipSlotLength=1,MotorTipSlotWidth=10))[0],[])

    def test_rectangular_and_larger_motor_patterns(self):
        for shape in EXTENDED_MOTOR_PAD_SHAPES:
            for along,across in ((16,16),(16,19),(19,16),(19,19)):
                p=Parameters(MotorBoltCircle=22.627416997969522,MotorHoleRotation=45,MotorPadShape=shape,MotorPadDiameter=36,MotorSpacingX=along,MotorSpacingY=across)
                self.assertEqual(validate(p)[0],[])

    def test_old_settings_and_json_roundtrip(self):
        old=Parameters().to_dict()
        for name in ('MotorTipLength','MotorTipSlotEnabled','MotorTipSlotWidth','MotorTipSlotLength'):old.pop(name)
        self.assertEqual(Parameters.from_dict(old),Parameters())
        p=Parameters(MotorPadShape='Arrowhead',MotorTipLength=10,MotorTipSlotWidth=4,MotorTipSlotLength=8)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'motor_tip.json';save_parameters(path,p)
            self.assertEqual(load_parameters(path),p)


if __name__=='__main__':unittest.main()
