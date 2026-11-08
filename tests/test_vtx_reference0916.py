"""Portable tests for strict separation between analog and digital VTX styles."""
import ast, unittest
from pathlib import Path
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.design_options import OPTIONS

class VTXModelIsolationTests(unittest.TestCase):
 def test_automatic_style_is_distinct_by_video_system(self):
  # The CAD module requires FreeCAD; inspect the pure resolver without import.
  source=Path(__file__).resolve().parents[1]/'freecad/rotorforge/detailed_references.py'
  tree=ast.parse(source.read_text())
  resolver=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='vtx_reference_kind')
  isolated=ast.Module(body=[resolver],type_ignores=[])
  ns={};exec(compile(ast.fix_missing_locations(isolated),str(source),'exec'),ns)
  resolve=ns['vtx_reference_kind']
  self.assertEqual(resolve(False),'analog_enclosed')
  self.assertEqual(resolve(True),'digital')
  self.assertEqual(resolve(False,'Exposed PCB'),'analog_exposed')
  self.assertEqual(resolve(True,'Analog enclosed'),'analog_enclosed')
  self.assertEqual(resolve(False,'Finned enclosure'),'digital')
 def test_existing_saved_styles_are_accepted(self):
  for style in ('Automatic','Exposed PCB','Finned enclosure','Analog enclosed'):
   for video in ('Analog','Digital'):
    p=Parameters(FPVEnabled=True,VideoSystem=video,VTXReferenceStyle=style,DetailedVTXReference=True)
    self.assertFalse(validate(p)[0])
    self.assertEqual(Parameters.from_dict(p.to_dict()).VTXReferenceStyle,style)
 def test_ui_description_mentions_commercial_analog(self):
  self.assertIn('commercial',OPTIONS['VTXReferenceStyle'][2].lower())
  self.assertIn('Analog enclosed',OPTIONS['VTXReferenceStyle'][3])
