"""Top-front controls retain values, enable by shape and appear in editor search."""
import os,sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge.parameters import Parameters
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];fail=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([]);Gui.getMainWindow=lambda:None
 win=FrameDialog();p=Parameters(FPVEnabled=True,TopFrontShape='Camera U recess',TopFrontRecessWidth=24.,TopFrontDepth=18.,TopFrontSetback=5.)
 win.set_values(p);win.refresh();assert win.values()==p
 assert win.controls['TopFrontShape'].count()==20
 assert win.controls['TopFrontRecessWidth'].isEnabled() and win.controls['TopFrontSetback'].isEnabled()
 assert not win.controls['TopFrontTipWidth'].isEnabled()
 win.set_values(replace(p,TopFrontShape='Flat-tip nose'));win.refresh()
 assert win.controls['TopFrontTipWidth'].isEnabled() and not win.controls['TopFrontRecessWidth'].isEnabled()
 win.set_values(replace(p,TopFrontShape='Straight'));win.refresh()
 assert not win.controls['TopFrontDepth'].isEnabled() and not win.controls['TopFrontSetback'].isEnabled()
 assert win.values().TopFrontRecessWidth==24.
 win.close();checks.append('20 shapes, all five controls round-trip, inactive dimensions retained and disabled')
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'gui_top_front.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));os._exit(1 if fail else 0)
