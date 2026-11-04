import json
import tempfile
import unittest
from pathlib import Path
from freecad.rotorforge.parameters import Parameters, save_parameters, load_parameters
from freecad.rotorforge.hardware_preferences import from_settings, validate_preferences

class HardwarePreferenceTests(unittest.TestCase):
 def prefs(self):
  return dict(version=1,created=True,visible=False,options=dict(groups=['Arm bolts','Stack hardware'],nuts=True,engagement=4.5),hidden_roles=['TopPlate'])
 def test_roundtrip_preserves_frame_and_hardware(self):
  p=Parameters(ArmNutMount='M3 press nut',StackPressNuts=True)
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'settings.json';save_parameters(path,p,self.prefs())
   self.assertEqual(load_parameters(path),p)
   self.assertEqual(from_settings(json.loads(path.read_text())),self.prefs())
 def test_legacy_missing_preferences_is_distinct_from_explicit_off(self):
  self.assertIsNone(from_settings({'parameters':{}}))
  value=self.prefs();value['created']=False
  self.assertFalse(from_settings({'hardware_references':value})['created'])
 def test_invalid_options_rejected_before_overwriting_file(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'settings.json';path.write_text('original')
   for field,value in [('groups',['Unknown']),('nuts','yes'),('engagement',float('nan'))]:
    prefs=self.prefs();prefs['options'][field]=value
    with self.assertRaises(ValueError):save_parameters(path,Parameters(),prefs)
    self.assertEqual(path.read_text(),'original')
 def test_reject_invalid_visibility_and_schema(self):
  for field,value in [('visible','true'),('created',1),('version',2),('hidden_roles','TopPlate')]:
   prefs=self.prefs();prefs[field]=value
   with self.assertRaises(ValueError):validate_preferences(prefs)
