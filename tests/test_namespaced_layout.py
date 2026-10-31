"""Namespaced startup, packaged assets and coexistence with other FreeCAD addons."""
from pathlib import Path
import subprocess,sys,tempfile,unittest,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
class NamespacedLayoutTests(unittest.TestCase):
 def test_mod_layout_and_metadata(self):
  self.assertTrue((ROOT/'freecad/rotorforge/init_gui.py').is_file())
  for path in ('freecad/__init__.py','Init.py','InitGui.py'):self.assertFalse((ROOT/path).exists())
  tree=ET.parse(ROOT/'package.xml');ns={'p':'https://wiki.freecad.org/Package_Metadata'}
  for icon in tree.findall('.//p:icon',ns):self.assertTrue((ROOT/icon.text).is_file())
 def test_plain_import_is_lightweight(self):
  expected=ET.parse(ROOT/'package.xml').getroot().find('{https://wiki.freecad.org/Package_Metadata}version').text
  script=f"import sys;from freecad.rotorforge import __version__;assert __version__=={expected!r};assert not any(n in sys.modules for n in ('FreeCAD','Part','FreeCADGui','freecad.rotorforge.geometry','freecad.rotorforge.gui'))"
  result=subprocess.run([sys.executable,'-c',script],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_native_namespace_allows_other_addons(self):
  with tempfile.TemporaryDirectory() as d:
   other=Path(d)/'freecad/coexistence_example';other.mkdir(parents=True);(other/'__init__.py').write_text('value=42')
   code=f"import sys;sys.path.insert(0,{d!r});import freecad.rotorforge,freecad.coexistence_example;assert freecad.coexistence_example.value==42"
   result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
 def test_runtime_assets_are_inside_package(self):
  from freecad.rotorforge.paths import icon_path,help_path
  self.assertTrue(Path(icon_path()).is_file());self.assertTrue(Path(help_path()).is_file())
  self.assertIn('freecad/rotorforge/resources',Path(help_path()).as_posix())
 def test_legacy_proxy_module_is_only_a_bridge(self):
  text=(ROOT/'rotorforge/document.py').read_text()
  self.assertIn('import_module("freecad.rotorforge.document")',text)
  self.assertNotIn('class ParameterProxy',text)
