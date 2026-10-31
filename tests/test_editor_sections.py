"""Every saved parameter stays reachable when the editor is reorganized."""
from pathlib import Path
import sys,unittest
from dataclasses import fields
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.editor_sections import SECTIONS,FIELD_LOCATION,HIDDEN_FIELDS
class EditorSectionTests(unittest.TestCase):
 def test_every_parameter_classified_once(self):
  names=[n for _c,_p,_d,groups in SECTIONS for _g,keys in groups for n in keys]
  self.assertEqual(len(names),len(set(names)))
  self.assertFalse(set(names)&HIDDEN_FIELDS)
  self.assertEqual(set(names)|HIDDEN_FIELDS,{f.name for f in fields(Parameters)})
 def test_focused_pages_for_formerly_mixed_tasks(self):
  for field,path in [('MotorPadShape',('Arms','Motors')),('StackSpacing',('Hardware','Stack')),('StrapSlotsEnabled',('Hardware','Straps')),('RootBoltLayout',('Arms','Bolts')),('KeystoneEnabled',('Arms','Clamps & key')),('CameraTiltMax',('FPV','Tilt & position')),('CameraBaseMode',('FPV','Side plates')),('BottomCentreWidth',('Frame','Centre widths'))]:
   self.assertEqual(FIELD_LOCATION[field][:2],path)
if __name__=='__main__':unittest.main()
