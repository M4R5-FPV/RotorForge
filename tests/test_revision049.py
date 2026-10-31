"""Visible catalogue boundaries, old settings, windows and direct VTX placement."""
import unittest,sys,math,warnings
from pathlib import Path
from dataclasses import fields,replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters,validate,arm_layouts
from freecad.rotorforge.motor_pads import RETAINED_PAD_SHAPES,NEW_MOTOR_PAD_SHAPES,MOTOR_PAD_SHAPES,REPLACED_PAD_SHAPES
from freecad.rotorforge.design_options import ARM_BEAM_SHAPES
from freecad.rotorforge.battery import GRIP_PATTERNS,clipped_grip_segments,groove_segments
from freecad.rotorforge.equipment_mass import equipment_items
from freecad.rotorforge.fpv import vtx_deck_z
class Revision048Tests(unittest.TestCase):
 def test_replacement_boundary_and_migration(self):
  self.assertEqual(MOTOR_PAD_SHAPES[:10],RETAINED_PAD_SHAPES)
  self.assertEqual(MOTOR_PAD_SHAPES[9],'Scalloped shield')
  self.assertEqual(len(NEW_MOTOR_PAD_SHAPES),12)
  self.assertFalse(set(REPLACED_PAD_SHAPES)&set(MOTOR_PAD_SHAPES))
  for old,new in REPLACED_PAD_SHAPES.items():
   with warnings.catch_warnings(record=True) as notes:
    warnings.simplefilter('always');p=Parameters.from_dict(dict(Parameters().to_dict(),MotorPadShape=old))
    self.assertEqual(p.MotorPadShape,new);self.assertTrue(notes)
 def test_vtx_is_on_carrier_without_user_spacer(self):
  self.assertNotIn('VTXMountHeight',{f.name for f in fields(Parameters)})
  for mode in ('2 plates','3 plates'):
   p=Parameters(FPVEnabled=True,PlateDesign=mode,StandoffHeight=35)
   self.assertEqual(validate(p)[0],[])
   item=next(i for i in equipment_items(p) if i['part']=='VTX')
   self.assertAlmostEqual(item['centre_mm'][2],vtx_deck_z(p)+p.VTXHeight/2)
  self.assertEqual(Parameters.from_dict(dict(Parameters().to_dict(),VTXMountHeight=99)),Parameters())
 def test_window_profiles_are_retired(self):
  self.assertEqual(len(ARM_BEAM_SHAPES),6)
  self.assertNotIn('ArmWindowWidth',{f.name for f in fields(Parameters)})
  for name in ('Slot beam','Twin window beam','Bridge beam'):
   p=Parameters.from_dict(dict(Parameters().to_dict(),ArmBeamShape=name,ArmWindowWidth=20))
   self.assertEqual(p.ArmBeamShape,'Broad shoulder');self.assertEqual(validate(p)[0],[])
 def test_ten_more_grips_and_clipping(self):
  self.assertEqual(len(GRIP_PATTERNS),25)
  for name in GRIP_PATTERNS[15:]:
   p=Parameters(LiPoPadEnabled=True,LiPoPadPattern=name)
   seg=groove_segments(p,(-20,-40,20,40));trimmed=clipped_grip_segments(p,seg,(-20,-40,20,40))
   self.assertTrue(trimmed);self.assertLessEqual(len(trimmed),len(seg))
   for a,b in trimmed:
    self.assertTrue(all(-20-p.LiPoPadGrooveWidth-1e-8<=x<=20+p.LiPoPadGrooveWidth+1e-8 and -40-p.LiPoPadGrooveWidth-1e-8<=y<=40+p.LiPoPadGrooveWidth+1e-8 for x,y in (a,b)))
