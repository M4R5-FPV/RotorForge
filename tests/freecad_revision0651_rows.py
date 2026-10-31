"""Unitless count widgets and non-destructive legacy property migration."""
import os,sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,VENT_ROW_COUNTS
from freecad.rotorforge.document import ensure_parameter_properties,read_parameters
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];failures=[]
try:
 d=App.newDocument('VentCounts');o=d.addObject('App::FeaturePython','Settings');ensure_parameter_properties(o,Parameters())
 for name in VENT_ROW_COUNTS:
  assert o.getTypeIdOfProperty(name)=='App::PropertyIntegerConstraint';assert type(getattr(o,name)) is int
  o.removeProperty(name);o.addProperty('App::PropertyLength',name,'Legacy');setattr(o,name,3.6 if name=='FlexGuardSlotCount' else 2.5)
 path=out/'LegacyRows.FCStd';d.saveAs(str(path));App.closeDocument(d.Name);d=App.openDocument(str(path));o=d.Settings;p=read_parameters(o)
 assert (p.FlexGuardSlotCount,p.FlexGuardFCSlotCount)==(4,2)
 assert all(o.getTypeIdOfProperty(n)=='App::PropertyLength' for n in VENT_ROW_COUNTS),'Read mutated the saved object'
 ensure_parameter_properties(o,p)
 for name in VENT_ROW_COUNTS:
  assert o.getTypeIdOfProperty(name)=='App::PropertyIntegerConstraint';assert getattr(o,name)==getattr(p,name)
  setattr(o,name,99);assert getattr(o,name)==6;setattr(o,name,0);assert getattr(o,name)==1;setattr(o,name,getattr(p,name))
 path=out/'IntegerRows.FCStd';d.saveAs(str(path));App.closeDocument(d.Name);d=App.openDocument(str(path));assert read_parameters(d.Settings)==p;App.closeDocument(d.Name)
 checks.append('Legacy lengths read without mutation; explicit migration and save/reopen preserve bounded integers');print('PASS PROPERTIES',flush=True)
except Exception:failures.append(dict(name='Properties',error=traceback.format_exc()));traceback.print_exc()
try:
 import FreeCADGui as Gui
 from PySide import QtWidgets,QtGui
 Gui.getMainWindow=lambda:None
 from freecad.rotorforge.gui import FrameDialog
 from freecad.rotorforge import geometry
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
 def reject(*a,**k):raise AssertionError('Native builder called during editing')
 geometry.build_shapes=reject
 dialog=FrameDialog();dialog.set_values(Parameters(FlexSideGuards=True));dialog.refresh()
 for name in VENT_ROW_COUNTS:
  control=dialog.controls[name];assert isinstance(control,QtWidgets.QSpinBox) and not isinstance(control,QtWidgets.QDoubleSpinBox)
  assert control.minimum()==1 and control.maximum()==6 and control.singleStep()==1 and control.suffix()==''
  assert control.validate('2.5',3)[0]!=QtGui.QValidator.Acceptable
  control.setValue(3);control.stepUp();assert control.value()==4;assert type(getattr(dialog.values(),name)) is int
 dialog.refresh();assert dialog.preview.last_error is None;dialog.close()
 checks.append('VTX/FC controls are unitless whole-number spin boxes; preview edits invoke no CAD builder');print('PASS EDITOR',flush=True)
except Exception:failures.append(dict(name='Editor',error=traceback.format_exc()));traceback.print_exc()
(out/'rows0651.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
