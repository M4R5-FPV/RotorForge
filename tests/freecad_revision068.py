"""Appearance is shared by every soft part and excluded from geometry work."""
import sys,os,json,traceback,time
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.appearance import PRINTED_COLOURS
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];failures=[]
try:
 p=Parameters(FPVEnabled=True,FlexCameraMode='Captured inserts',CameraForeAftOffset=20.,FlexMotorProtectors=True,FlexSideGuards=True,FlexGuardCloseFront=True,FlexGuardClearance=0.,LiPoPadEnabled=True)
 g.clear_build_caches();doc=App.newDocument('PrintedColours068');settings=d.create_frame(p,doc);parts=d.component_objects(settings)
 writes={r:getattr(o.Proxy,'_shape_writes',0) for r,o in parts.items()};misses=g._build.cache_info().misses;times=[]
 for colour in PRINTED_COLOURS:
  q=replace(p,PrintedPartColour=colour);t=time.perf_counter();d.update_frame(settings,q);times.append(time.perf_counter()-t)
  assert not settings.RebuiltComponents;assert g._build.cache_info().misses==misses
  assert all(getattr(o.Proxy,'_shape_writes',0)==writes[r] for r,o in parts.items())
 assert all(not parts[r].Shape.isNull() for r in ('CameraPadLeft','CameraPadRight','LiPoPad','ElectronicsGuardLeft','MotorProtectorFrontRight'))
 path=out/'PrintedColours.FCStd';doc.saveAs(str(path));App.closeDocument(doc.Name);g.clear_build_caches();doc=App.openDocument(str(path));settings=doc.getObject('FrameParameters');assert d.read_parameters(settings).PrintedPartColour=='Grey'
 d.update_frame(settings,replace(p,PrintedPartColour='Orange'));assert not settings.RebuiltComponents;App.closeDocument(doc.Name)
 checks.append(dict(name='All ten colour selections and save/reopen reuse every generated Shape without native geometry builds',update_seconds=times));print('PASS COLOURS',flush=True)
except Exception:failures.append(dict(name='Colour geometry',error=traceback.format_exc()));traceback.print_exc()
try:
 import FreeCADGui as Gui
 from PySide import QtWidgets,QtCore
 Gui.getMainWindow=lambda:None
 from freecad.rotorforge.gui import FrameDialog
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
 def reject(*a,**kw):raise AssertionError('A preview recolour invoked a CAD builder')
 g.build_shapes=reject;g.build_shape=reject
 dialog=FrameDialog();dialog.resize(1400,900);dialog.show();app.processEvents()
 for colour in PRINTED_COLOURS:
  q=replace(p,PrintedPartColour=colour);dialog.set_values(q);dialog.refresh();assert dialog.values()==q
  for role in ('Overall','CameraPadLeft','MotorProtectorFrontRight','ElectronicsGuardLeft','LiPoPad'):
   dialog.preview_mode.setCurrentIndex(dialog.preview_mode.findData(role));app.processEvents();assert dialog.preview.last_error is None,dialog.preview.last_error
  if colour=='Orange':dialog.preview.grab().save(str(out/'OrangePreview.png'))
 assert dialog.controls['PrintedPartColour'].count()==10
 dialog.close();checks.append(dict(name='Colour swatches and all printed-part editor modes render without CAD construction'));print('PASS EDITOR',flush=True)
except Exception:failures.append(dict(name='Editor colours',error=traceback.format_exc()));traceback.print_exc()
(out/'revision068.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
