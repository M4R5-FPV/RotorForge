"""Portable validation of transmitter reference appearance settings."""
import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,ENUMERATIONS,validate
from freecad.rotorforge.design_options import OPTIONS
from freecad.rotorforge.editor_sections import SECTIONS


class VTXReferenceAppearanceTests(unittest.TestCase):
 def test_styles_roundtrip_and_validate(self):
  self.assertEqual(ENUMERATIONS['VTXReferenceStyle'],('Automatic','Exposed PCB','Finned enclosure','Analog enclosed'))
  for digital in ('Analog','Digital'):
   for style in ENUMERATIONS['VTXReferenceStyle']:
    p=Parameters(FPVEnabled=True,VideoSystem=digital,DetailedVTXReference=True,VTXReferenceStyle=style)
    self.assertEqual(Parameters.from_dict(p.to_dict()),p)
    self.assertFalse(validate(p)[0],style)
 def test_legacy_design_defaults_to_automatic(self):
  p=Parameters.from_dict({'VideoSystem':'Analog','DetailedVTXReference':True})
  self.assertEqual(p.VTXReferenceStyle,'Automatic')
 def test_editor_has_style_control(self):
  self.assertIn('finned',OPTIONS['VTXReferenceStyle'][2].lower())
  pages=[(group,fields) for _,tab,_,sections in SECTIONS if tab=='Detailed references' for group,fields in sections]
  self.assertEqual([group for group,fields in pages if 'VTXReferenceStyle' in fields],['VTX body appearance'])
