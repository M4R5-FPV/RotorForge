"""Native editor mode switches, JSON load and current Help inventory."""
import os,sys,json,tempfile,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.path.insert(0,str(root/'tests'))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App
from PySide import QtWidgets
from unittest.mock import patch
from dataclasses import replace
from freecad.rotorforge.gui import FrameDialog,LABELS,TIPS
from freecad.rotorforge.editor_sections import FIELD_LOCATION,FIELD_ORDER,HIDDEN_FIELDS
from freecad.rotorforge.parameters import Parameters,ENUMERATIONS,save_parameters
from test_guard_options089 import vtx_frame
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
checks=[];failures=[]
try:
 win=FrameDialog();p=vtx_frame(FlexGuardFitMode='Between plates',FlexGuardWireEnabled=True,
                            FlexGuardVTXY=-2.,FlexGuardVTXZ=-1.,FlexGuardWirePairs='Rear')
 win.set_values(p);win.refresh()
 assert win.values()==p
 assert not win.controls['FlexGuardWirePairs'].isEnabled()
 assert win.controls['FlexGuardVTXY'].isEnabled() and win.controls['FlexGuardVTXZ'].value()==-1.
 win.controls['FlexGuardFitMode'].setCurrentText('Plate-edge wrap');win.refresh()
 assert win.controls['FlexGuardWirePairs'].isEnabled() and win.controls['FlexGuardWirePairs'].currentText()=='Rear'
 win.controls['FlexGuardFitMode'].setCurrentText('Between plates');win.refresh()
 checks.append('Fit switch uses one wire span and restores saved pair selection')
 win.controls['FlexGuardVTXOpening'].setChecked(False);win.refresh()
 assert not win.controls['FlexGuardVTXY'].isEnabled()
 assert win.controls['FlexGuardVTXY'].value()==-2.
 win.controls['FlexGuardVTXOpening'].setChecked(True);win.refresh()
 win.controls['FlexGuardVTXLength'].setValue(32.);win.controls['FlexGuardVTXHeight'].setValue(16.);win.refresh()
 assert not win.controls['FlexGuardVTXClearance'].isEnabled()
 checks.append('VTX controls retain values and disable irrelevant automatic clearance')
 p=vtx_frame(FlexGuardFitMode='Between plates',FlexGuardWireEnabled=True)
 with tempfile.TemporaryDirectory() as t:
  path=Path(t)/'settings.json';save_parameters(path,p);warnings=[]
  with patch.object(QtWidgets.QFileDialog,'getOpenFileName',return_value=(str(path),'')),patch.object(QtWidgets.QMessageBox,'warning',side_effect=lambda *args:warnings.append(args[-1])):win.load()
  assert not warnings,warnings
  assert win.values()==p and win.generate.isEnabled()
 win.show();QtWidgets.QApplication.processEvents()
 category,scroll=win.section_pages['Side guards'];win.tabs.setCurrentWidget(win.category_tabs[category]);win.category_tabs[category].setCurrentWidget(scroll)
 win.resize(1440,1000);QtWidgets.QApplication.processEvents()
 win.grab().save(str(out/'SideGuardOptions.png'));assert win.preview.last_error is None
 checks.append('Actual Load action preserves new options and paints preview')
 # Keep hand-edited explanations for older controls, update exact option metadata.
 path=root/'docs/help_controls.json';old={c['key']:c for c in json.loads(path.read_text())}
 from freecad.rotorforge.flex_options import FLEX_OPTIONS
 controls=[]
 for key in sorted(set(Parameters.__dataclass_fields__)-set(HIDDEN_FIELDS),key=lambda k:FIELD_ORDER.get(k,10000)):
  category,tab,group=FIELD_LOCATION[key]
  entry=old.get(key,{})
  entry.update(key=key,label=LABELS.get(key,win.controls[key].objectName() or key),tab=tab,category=category,group=group,default=getattr(Parameters(),key))
  if key in ENUMERATIONS:entry['choices']=list(ENUMERATIONS[key])
  else:entry.setdefault('choices',[])
  if key in FLEX_OPTIONS:
   entry['help']=entry['tip']=TIPS[key]
  controls.append(entry)
 path.write_text(json.dumps(controls,indent=2,ensure_ascii=False))
 checks.append('Help inventory matches all '+str(len(controls))+' current visible controls')
 win.close()
except Exception:failures.append(traceback.format_exc())
(out/'checks.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2))
print(json.dumps(dict(checks=checks,failures=failures)),flush=True)
os._exit(1 if failures else 0)
