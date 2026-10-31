import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.front_bumper import BUMPER_SHAPES
from freecad.rotorforge import geometry as g
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];fail=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([]);Gui.getMainWindow=lambda:None
 def reject(*a,**k):raise AssertionError('Native build in live preview')
 g.build_shapes=reject;g.build_for_update=reject
 win=FrameDialog();win.resize(1400,1000)
 for shape in BUMPER_SHAPES:
  p=Parameters(FlexFrontBumper=True,FlexBumperShape=shape,PrintedPartColour='Orange')
  win.set_values(p);win.refresh();assert win.values()==p
  for role in ('Overall','FrontBumper'):
   idx=win.preview_mode.findData(role);assert idx>=0,role;win.preview_mode.setCurrentIndex(idx)
   win.preview.grab();assert win.preview.last_error is None,win.preview.last_error
  assert win.controls['FlexBumperProjection'].isEnabled()==(shape!='Follow bottom plate')
 for y in (20.,24.,40.,46.):
  q=Parameters(FPVEnabled=True,StandoffHeight=35.,FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardCloseFront=True,FlexGuardWireEnabled=True,FlexGuardWirePairs='Front',FlexGuardWireFrontY=y)
  win.set_values(q);win.refresh();win.preview_mode.setCurrentIndex(win.preview_mode.findData('ElectronicsGuardLeft'));win.preview.grab();assert win.preview.last_error is None
 win.set_values(p);win.refresh()
 win.show();win.jump_to_control('TPU > Front bumper > Create front bumper');app.processEvents();win.grab().save(str(out/'BumperEditor.png'))
 win.set_values(Parameters());win.refresh();assert not win.controls['FlexBumperWall'].isEnabled()
 win.close();checks.append('Fourteen styles, front-pocket travel previews, material colour, Overall/part views and disabled controls round-trip without CAD builds')
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'gui_front_bumper.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));os._exit(1 if fail else 0)
