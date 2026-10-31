import sys,os,json,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
from dataclasses import replace
import FreeCAD as App
from PySide import QtWidgets
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge import document as d,geometry as g
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);fail=[];checks=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([]);win=FrameDialog()
 p=Parameters(StrapCount='1 strap',StrapSingleY=-4.,StrapOpeningStyle='Outline cutouts')
 win.set_values(p);win.refresh();assert win.values()==p
 c=win.controls['StrapOpeningStyle'];assert [c.itemText(i) for i in range(c.count())]==['Slots','Outline cutouts']
 assert win.controls['StrapSingleY'].isEnabled() and not win.controls['StrapOffsetY'].isEnabled()
 assert win.controls['StrapSingleY'].minimum()<0
 win.preview_mode.setCurrentIndex(win.preview_mode.findData('TopPlate'));win.preview.grab();assert win.preview.last_error is None
 win.set_values(replace(p,StrapCount='2 straps'));win.refresh();assert not win.controls['StrapSingleY'].isEnabled() and win.controls['StrapOffsetY'].isEnabled()
 win.set_values(replace(p,StrapSlotsEnabled=False));win.refresh();assert not win.controls['StrapCount'].isEnabled()
 win.close();checks.append('dropdown, one/two controls and preview')
 doc=App.newDocument();frame=d.create_frame(Parameters(),doc)
 frame.StrapOpeningStyle=['Slots','Outline cutouts','None'];frame.StrapOpeningStyle='None'
 restored=d.read_parameters(frame);assert not restored.StrapSlotsEnabled and restored.StrapOpeningStyle=='Slots'
 d.update_frame(frame,restored);assert str(frame.StrapOpeningStyle)=='Slots' and not frame.StrapSlotsEnabled
 assert frame.getEnumerationsOfProperty('StrapOpeningStyle')==['Slots','Outline cutouts']
 doc.saveAs(str(out/'LegacyNoneMigrated.FCStd'));App.closeDocument(doc.Name);checks.append('native legacy None migration')
except Exception:fail.append(traceback.format_exc())
(out/'gui_checks.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(fail,flush=True);os._exit(1 if fail else 0)
