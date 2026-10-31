"""Editor remains kernel-free with closure and all guard vent profiles."""
import sys,os,json,traceback,time
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets
Gui.getMainWindow=lambda:None
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge.flex_options import GUARD_VENT_SHAPES
from freecad.rotorforge import geometry,protection_geometry,flex_geometry
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True);checks=[];failures=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
 def reject(*a,**kw):raise AssertionError('Native solid builder called during preview')
 geometry.build_shapes=reject;protection_geometry.side_guards=reject;flex_geometry.make_flex=reject
 dialog=FrameDialog();dialog.resize(1400,900);dialog.show();app.processEvents();t=time.monotonic()
 for i,name in enumerate(GUARD_VENT_SHAPES):
  p=Parameters(FPVEnabled=True,FlexSideGuards=True,FlexGuardCloseFront=True,FlexGuardVentShape=name,FlexGuardFCVentShape=name)
  dialog.set_values(p);dialog.refresh();assert dialog.values()==p
  assert dialog.controls['FlexGuardCloseFront'].isEnabled() and dialog.controls['FlexGuardCameraOverlap'].isEnabled()
  for role in ('Overall','ElectronicsGuardLeft'):
   idx=dialog.preview_mode.findData(role);assert idx>=0;dialog.preview_mode.setCurrentIndex(idx);app.processEvents();pix=dialog.preview.grab();assert dialog.preview.last_error is None,dialog.preview.last_error
   if i in (0,15):pix.save(str(out/(role+str(i)+'.png')))
 dialog.set_values(Parameters());dialog.refresh();assert not dialog.controls['FlexGuardCloseFront'].isEnabled()
 dialog.close();checks.append(dict(name='Sixteen vent choices and enclosure render in Overall and side views without native builds',seconds=round(time.monotonic()-t,2)))
except Exception:failures.append(traceback.format_exc());traceback.print_exc()
(out/'editor066.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
