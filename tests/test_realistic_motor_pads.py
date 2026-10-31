"""Additional FPV-style outlines, mounting clearances and saved settings."""
from dataclasses import replace
from pathlib import Path
import math,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters,LAYOUTS,arm_layouts,validate,save_parameters,load_parameters
from freecad.rotorforge.motor_pads import (MOTOR_PAD_SHAPES,REALISTIC_MOTOR_PAD_SHAPES,NEW_MOTOR_PAD_SHAPES,
    motor_pad_primitives,motor_pad_interior,motor_pad_bound,motor_tip_slots,motor_corner_control)

class RealisticMotorPadTests(unittest.TestCase):
    def test_original_choices_are_retained(self):
        self.assertEqual(MOTOR_PAD_SHAPES[:6],('Round','Rounded square','Chamfered square','Four-lobe','Tapered nose','Arrowhead'))
        self.assertEqual(Parameters().MotorPadShape,'Round')
        self.assertEqual(len(set(MOTOR_PAD_SHAPES)),22)

    def test_layout_and_mounting_centres_are_unchanged(self):
        for layout in LAYOUTS:
            original=Parameters(Layout=layout,Wheelbase=270,MotorBoltCircle=22.627416997969522,MotorHoleRotation=45)
            for shape in REALISTIC_MOTOR_PAD_SHAPES:
                p=replace(original,MotorPadShape=shape)
                self.assertEqual(arm_layouts(p),arm_layouts(original))
                self.assertEqual(validate(p)[0],[])

    def test_teardrop_neck_is_tangent(self):
        for width in (10,14,22):
            p=Parameters(MotorPadShape='Teardrop',ArmWidth=width)
            circle,neck=motor_pad_primitives(p)
            start,tangent=neck['points'][3],neck['points'][2]
            self.assertAlmostEqual(math.hypot(*tangent),circle['radius'])
            self.assertAlmostEqual(sum(tangent[i]*(tangent[i]-start[i]) for i in (0,1)),0,places=9)
            self.assertEqual(abs(start[1])*2,width)

    def test_scallops_remove_edge_material(self):
        p=Parameters(MotorPadShape='Scalloped shield')
        cuts=[d for d in motor_pad_primitives(p) if d.get('operation')=='cut']
        self.assertEqual(len(cuts),3)
        for cut in cuts:
            pt=tuple(c*.9 for c in cut['centre'])
            self.assertLess(motor_pad_interior(pt,p),0)
            self.assertGreater(motor_pad_interior(pt,replace(p,MotorPadShape='Shouldered')),0)
        self.assertNotEqual(motor_pad_primitives(p),motor_pad_primitives(replace(p,MotorPadCornerRadius=3)))

    def test_larger_and_rectangular_patterns(self):
        for shape in REALISTIC_MOTOR_PAD_SHAPES:
            for sx,sy in ((16,16),(16,19),(19,16),(19,19)):
                p=Parameters(MotorBoltCircle=22.627416997969522,MotorHoleRotation=45,MotorPadShape=shape,MotorPadDiameter=36,MotorSpacingX=sx,MotorSpacingY=sy)
                self.assertEqual(validate(p)[0],[])
                from freecad.rotorforge.parameters import motor_hole_offsets
                for x,y in motor_hole_offsets(p):self.assertGreaterEqual(motor_pad_interior((x,y),p),p.MotorHoleDiameter/2+p.MinimumWeb)
                bound=motor_pad_bound(p)
                for d in motor_pad_primitives(p):
                    if d.get('operation')=='cut':continue
                    extent=math.hypot(*d['centre'])+d['radius'] if d['kind']=='circle' else max(math.hypot(*pt) for pt in d['points'])
                    self.assertLessEqual(extent,bound+1e-9)

    def test_controls_and_invalid_sizes(self):
        for shape in REALISTIC_MOTOR_PAD_SHAPES:
            p=Parameters(MotorBoltCircle=22.627416997969522,MotorHoleRotation=45,MotorPadShape=shape,MotorTipLength=-1,MotorTipSlotLength=1,MotorTipSlotWidth=40)
            self.assertEqual(validate(p)[0],[])
            self.assertFalse(motor_tip_slots(p))
            self.assertEqual(motor_corner_control(p),shape in ('Shouldered','Scalloped shield')+NEW_MOTOR_PAD_SHAPES)
            if not shape.startswith('Bolt-following'):self.assertTrue(validate(replace(p,MotorPadDiameter=18))[0])
        for shape in ('Shouldered','Scalloped shield')+NEW_MOTOR_PAD_SHAPES:
            for radius in (0,16):self.assertTrue(validate(Parameters(MotorBoltCircle=22.627416997969522,MotorHoleRotation=45,MotorPadShape=shape,MotorPadCornerRadius=radius))[0])

    def test_personal_settings_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            for shape in REALISTIC_MOTOR_PAD_SHAPES:
                p=Parameters(MotorBoltCircle=22.627416997969522,MotorHoleRotation=45,MotorPadShape=shape);path=Path(directory)/'motor_pad.json'
                save_parameters(path,p);self.assertEqual(load_parameters(path),p)

if __name__=='__main__':unittest.main()
