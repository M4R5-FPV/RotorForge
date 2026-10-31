"""Width controls and previews remain kernel-free in native FreeCAD Qt."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCADGui as Gui
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
  for width in (24.,0.,80.):
   p=Parameters(FlexFrontBumper=True,FlexBumperShape=shape,FlexBumperWidth=width)
   win.set_values(p);win.refresh();assert win.values()==p
   assert win.controls['FlexBumperWidth'].isEnabled()==(shape!='Follow bottom plate')
   for role in ('Overall','FrontBumper'):
    win.preview_mode.setCurrentIndex(win.preview_mode.findData(role));win.preview.grab();assert win.preview.last_error is None,win.preview.last_error
   checks.append([shape,width])
 win.show();win.jump_to_control('TPU > Front bumper > Bumper toe width (0 = automatic)');app.processEvents();win.grab().save(str(out/'BumperWidthEditor.png'))
 win.set_values(Parameters());win.refresh();assert not win.controls['FlexBumperWidth'].isEnabled();win.close()
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'gui_bumper_width.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));os._exit(1 if fail else 0)
