import os,sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge.parameters import Parameters
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT'])
checks=[];fail=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([]);Gui.getMainWindow=lambda:None
 dialog=FrameDialog();p=Parameters(FPVEnabled=True,FlexCameraMode='Captured inserts',FlexInsertLipSide='Inside only',FlexInsertCornerRadius=.5)
 dialog.set_values(p);dialog.refresh()
 assert dialog.values().FlexInsertLipSide=='Inside only' and dialog.values().FlexInsertCornerRadius==.5
 assert dialog.controls['FlexInsertLipSide'].isEnabled() and dialog.controls['FlexInsertCornerRadius'].isEnabled()
 assert dialog.controls['FlexInsertLipSide'].count()==3
 dialog.set_values(replace(p,FlexCameraMode='Hard mount'));dialog.refresh()
 assert not dialog.controls['FlexInsertLipSide'].isEnabled() and not dialog.controls['FlexInsertCornerRadius'].isEnabled()
 checks.append('Lip selector and radius round-trip; captured-only controls disable in hard mount')
 dialog.close()
 from freecad.rotorforge import geometry as g
 base=Parameters(FPVEnabled=True,FlexCameraMode='Captured inserts',StandoffHeight=35.)
 g.build_for_update(base);changed=replace(base,FlexInsertLipSide='Inside only');g.build_for_update(changed)
 report=g.build_report(changed)
 assert set(report['rebuilt'])<= {'CameraPadLeft','CameraPadRight','FrameCGMarker'},report
 checks.append('Lip-face change reuses carbon plates and arms: '+', '.join(report['rebuilt']))
except Exception:fail.append(traceback.format_exc())
(out/'gui.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));os._exit(1 if fail else 0)
