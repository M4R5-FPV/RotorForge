import unittest,math
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.flex_options import FLEX_OPTIONS,FLEX_ROLES
from freecad.rotorforge.flex import flex_roles
from freecad.rotorforge.protection_layout import guard_layout,guard_vents,usb_window,motor_service_slots
from freecad.rotorforge.parameters import arm_layouts
from freecad.rotorforge.arm_roots import fillet_root_limit
class Protection060Tests(unittest.TestCase):
 def test_removed_mounts_have_no_controls_parameters_or_roles(self):
  for prefix in ('FlexRear','FlexVTX','FlexGPS','FlexELRS','FlexClampSlit'):
   self.assertFalse(any(k.startswith(prefix) for k in Parameters.__dataclass_fields__))
   self.assertFalse(any(k.startswith(prefix) for k in FLEX_OPTIONS))
  self.assertFalse(any(r.startswith('Rear') for r in FLEX_ROLES))
 def test_old_saved_settings_are_ignored_and_zip_choice_migrates(self):
  p=Parameters.from_dict(dict(FlexRearEnabled=True,FlexRearGPS=True,FlexVTXCount='2',FlexProtectorRetention='Zip ties'))
  self.assertEqual(p.FlexProtectorRetention,'Linked screw access');self.assertEqual(flex_roles(p),());self.assertNotIn('FlexRearEnabled',p.to_dict())
 def test_extension_reaches_forward_row_and_retains_existing_sleeves(self):
  p=Parameters(FlexSideGuards=True,StandoffCount='6 (3 pairs)',StandoffPair3Y=-90)
  a=guard_layout(p)[0];b=guard_layout(replace(p,FlexGuardExtendFront=True))[0]
  self.assertGreater(b['front'],a['front']);self.assertEqual(len(b['stands']),3)
  self.assertTrue({s['point'] for s in a['stands']}<={s['point'] for s in b['stands']})
 def test_usb_option_only_active_on_extended_selected_side(self):
  p=Parameters(FlexSideGuards=True,FlexGuardUSBEnabled=True)
  self.assertTrue(all(usb_window(p,g) is None for g in guard_layout(p)))
  q=replace(p,FlexGuardExtendFront=True,FlexGuardUSBSide='Right',FlexGuardUSBY=-3.)
  a,b=guard_layout(q);self.assertIsNone(usb_window(q,a));self.assertEqual(usb_window(q,b)[0],q.StackOffsetY-3.)
 def test_all_vent_shapes_are_bounded_and_webs_remain(self):
  for name in FLEX_OPTIONS['FlexGuardVentShape'][3]:
   p=Parameters(FlexSideGuards=True,FlexGuardVentShape=name);g=guard_layout(p)[0];vents=guard_vents(p,g);self.assertTrue(vents)
   for v in vents:
    self.assertGreater(v['height'],0);self.assertGreater(v['width'],0);self.assertGreater(v['z']-v['height']/2,g['z']);self.assertLess(v['z']+v['height']/2,g['top'])
 def test_solid_ignores_vent_settings(self):
  p=Parameters(FlexSideGuards=True,FlexGuardStyle='Solid');self.assertEqual(guard_vents(p,guard_layout(p)[0]),())
 def test_service_slots_follow_actual_motor_holes(self):
  p=Parameters(FlexProtectorRetention='Linked screw access',MotorPadRotation=25.,MotorHoleRotation=33.)
  for a in arm_layouts(p):
   slots=motor_service_slots(p,a);self.assertEqual({b for _,b,_ in slots},set(a['motor_holes']));self.assertTrue(all(start==a['motor'] for start,_,_ in slots))
 def test_root_limit_covers_mounting_stock(self):
  p=Parameters(ArmRootLength=2.)
  for a in arm_layouts(p):
   limit=fillet_root_limit(p,a);self.assertGreaterEqual(limit,p.ArmRootLength)
   for x,y in a['bolts']:self.assertGreaterEqual(limit,(x-a['root'][0])*a['unit'][0]+(y-a['root'][1])*a['unit'][1]+p.RootHoleDiameter/2+p.MinimumWeb-1e-8)
