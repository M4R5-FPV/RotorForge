import unittest
from dataclasses import replace
from types import SimpleNamespace
from freecad.rotorforge.parameters import Parameters,ENUMERATIONS
from freecad.rotorforge.appearance import PRINTED_COLOURS,CARBON_COLOR,printed_colour,printed_hex,printed_groove,apply_material,design_signature
class View:
 def __init__(self,modern=True):
  self.PropertiesList=['ShapeAppearance'] if modern else ['ShapeMaterial'];self.ShapeColor=(.1,.2,.3)
  material=SimpleNamespace(DiffuseColor=None,SpecularColor=None,Shininess=None,Transparency=None)
  if modern:self.ShapeAppearance=[material]
  else:self.ShapeMaterial=material
class PrintedColourTests(unittest.TestCase):
 def test_choices_roundtrip_and_signature(self):
  p=Parameters();self.assertEqual(tuple(PRINTED_COLOURS),ENUMERATIONS['PrintedPartColour'])
  for colour in PRINTED_COLOURS:
   q=replace(p,PrintedPartColour=colour);self.assertEqual(q,Parameters.from_dict(q.to_dict()));self.assertEqual(design_signature(p),design_signature(q))
 def test_every_flexible_role_and_pad_receive_same_colour(self):
  from freecad.rotorforge.flex_options import FLEX_ROLES
  for modern in (True,False):
   for colour in PRINTED_COLOURS:
    p=Parameters(PrintedPartColour=colour)
    for role in FLEX_ROLES+('LiPoPad',):
     view=View(modern);apply_material(view,role,('TopPlate',),p);self.assertEqual(view.ShapeColor,printed_colour(p));self.assertEqual(view.Transparency,0)
     material=view.ShapeAppearance[0] if modern else view.ShapeMaterial;self.assertEqual(material.DiffuseColor,printed_colour(p));self.assertEqual(material.Shininess,2.)
 def test_carbon_and_electronics_colours_are_independent(self):
  p=Parameters(PrintedPartColour='Orange');v=View();apply_material(v,'TopPlate',('TopPlate',),p);self.assertEqual(v.ShapeColor,CARBON_COLOR)
  for role in ('StackEnvelope','BatteryEnvelope','VTXEnvelope','MotorEnvelopes'):
   v=View();apply_material(v,role,('TopPlate',),p)
   from freecad.rotorforge.reference_options import SIMPLE
   self.assertEqual(v.ShapeColor,SIMPLE[role][0] if role in SIMPLE else (.1,.2,.3))
 def test_previews_have_contrasting_grip_channels(self):
  for c in PRINTED_COLOURS:
   p=Parameters(PrintedPartColour=c);self.assertNotEqual(printed_hex(p),printed_groove(p))
