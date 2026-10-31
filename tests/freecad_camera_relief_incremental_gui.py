import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge import geometry as g
p=Parameters(FPVEnabled=True)
g.build_for_update(p)
q=replace(p,CameraTabCutterDiameter=1.)
g.build_for_update(q)
report=g.build_report(q)
assert set(report['rebuilt']) <= {'CameraMountLeft','CameraMountRight','FrameCGMarker'},report
assert g.build_shape(q,'CameraMountLeft').Volume > g.build_shape(p,'CameraMountLeft').Volume
import FreeCADGui as Gui
from PySide import QtWidgets
from freecad.rotorforge.gui import FrameDialog
app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
Gui.getMainWindow=lambda:None
dialog=FrameDialog();dialog.set_values(q);dialog.refresh()
assert dialog.controls['CameraTabCutterDiameter'].isEnabled()
assert dialog.values().CameraTabCutterDiameter==1.
dialog.set_values(replace(q,CameraTabReliefs=False));dialog.refresh()
assert not dialog.controls['CameraTabCutterDiameter'].isEnabled()
data={'rebuilt':report['rebuilt'],'gui':'controls and disabled-state round-trip passed'}
(Path(os.environ['ROTORFORGE_TEST_OUTPUT'])/'cache_gui.json').write_text(json.dumps(data,indent=2))
print(data,flush=True)
os._exit(0)
