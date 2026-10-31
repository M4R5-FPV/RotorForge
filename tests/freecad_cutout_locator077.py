"""Actual FreeCAD editor locator stays kernel-free and preserves saved pattern order."""
import sys,os,json,traceback,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets,QtCore,QtGui
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.cutouts import PATTERN_DEFAULTS,encode_patterns
from freecad.rotorforge import geometry as g
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];fail=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([]);Gui.getMainWindow=lambda:None
 def reject(*a,**k):raise AssertionError('Native frame construction invoked by locator')
 g.build_shapes=reject;g.build_for_update=reject
 win=FrameDialog();win.resize(1400,1000)
 patterns=[dict(PATTERN_DEFAULTS,shape='Circle',width=6.,x=-8.,y=5.),dict(PATTERN_DEFAULTS,shape='Rectangle',width=5.,length=8.,x=-8.,y=5.),dict(PATTERN_DEFAULTS,role='BottomPlate',shape='Diamond',x=8.,y=6.)]
 p=Parameters(CutoutPatterns=encode_patterns(patterns));win.set_values(p);win.refresh()
 # Find editor through its type without relying on a page attribute name.
 from freecad.rotorforge.airflow_gui import AirflowEditor
 editor=win.findChild(AirflowEditor);assert editor is not None
 original=editor.patterns.copy();editor.preview.resize(680,320)
 editor.find_pattern.setText('rectangle');assert editor.pattern_list.item(0).isHidden() and not editor.pattern_list.item(1).isHidden()
 editor.find_pattern.clear()
 point=editor.preview.view()[1].map(QtCore.QPointF(-8.,5.)).toPoint()
 event=QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress,QtCore.QPointF(point),QtCore.Qt.LeftButton,QtCore.Qt.LeftButton,QtCore.Qt.NoModifier)
 QtWidgets.QApplication.sendEvent(editor.preview,event);assert editor._selected_index==1
 event=QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress,QtCore.QPointF(point),QtCore.Qt.LeftButton,QtCore.Qt.LeftButton,QtCore.Qt.NoModifier)
 QtWidgets.QApplication.sendEvent(editor.preview,event);assert editor._selected_index==0
 editor.preview.grab().save(str(out/'LocatorPreview.png'));assert editor.preview.last_error is None
 editor.preview.zoom_selected();editor.preview.grab();assert editor.preview.last_error is None
 editor.inputs['width'].setValue(7.);assert not editor.choose_pattern(1);assert editor._selected_index==0
 editor.discard_changes();editor.choose_pattern(1)
 assert editor.patterns==original and win.values()==p
 checks.append('Frame editor: search, overlap cycling, highlight, zoom and pending-edit guard without CAD or settings changes')
 # 200 saved patterns: cache is reused for repeated pointer hit tests.
 values=[dict(PATTERN_DEFAULTS,shape='Circle',width=2.,x=-15.+(i%10)*3.,y=-30.+(i//10)*3.) for i in range(200)]
 editor.set_json(encode_patterns(values));assert win.values().CutoutPatterns==encode_patterns(values);editor.preview.records();editor.preview.view()
 start=time.perf_counter()
 for _ in range(50):editor.preview.hit_indices(QtCore.QPointF(300,150))
 elapsed=time.perf_counter()-start
 assert elapsed<8.,elapsed
 checks.append('200 patterns: 50 cached hit tests in '+str(round(elapsed,3))+' s')
 editor.preview.grab().save(str(out/'LocatorMany.png'));assert editor.preview.last_error is None
 win.set_values(p);win.show();win.jump_to_control('Finishing > Airflow / outlines > Find saved cutout');app.processEvents()
 assert 'Finishing > Airflow / outlines > Zoom to selected cutout' in win.search_locations
 win.grab().save(str(out/'AirflowControls.png'));checks.append('New locator commands are reachable through the main editor search')
 win.close()
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'locator.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));os._exit(1 if fail else 0)
