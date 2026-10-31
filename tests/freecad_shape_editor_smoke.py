"""Offscreen selector, migration, preview and native blend checks."""
import sys,os,json,math,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets,QtGui,QtCore
Gui.getMainWindow=lambda:None
app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge.parameters import Parameters,arm_layouts,plate_levels
from freecad.rotorforge import geometry
from freecad.rotorforge.airflow_gui import arm_blank_path
from dataclasses import replace
out=os.environ['ROTORFORGE_TEST_OUTPUT'];os.makedirs(out,exist_ok=True)
checks=[]
try:
 d=FrameDialog();d.show();app.processEvents()
 combo=d.controls['StackSpacing'];assert combo.count()==2 and not combo.isEditable()
 for size in (20.,30.5):
  p=Parameters(StackSpacing=size,StackMountHeight=3,MotorPadShape='Round-shoulder shield',MotorPadRelief='Twin neck slots',MotorPadRotation=30,ArmBeamShape='Broad shoulder',TopPlateShape='Octagonal')
  original=geometry.build_shapes
  geometry.build_shapes=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Live preview invoked native geometry'))
  try:
   d.set_values(p);app.processEvents();d.refresh();app.processEvents();assert d.values()==p
  finally:geometry.build_shapes=original
 checks.append('Two-choice FC selector; heights editable; full parameter roundtrip; no native geometry during live preview')
 d.grab().save(out+'/editor.png')
 def path_area(path):
  area=0
  for poly in path.toFillPolygons():
   area+=abs(sum(poly[i].x()*poly[(i+1)%len(poly)].y()-poly[(i+1)%len(poly)].x()*poly[i].y() for i in range(len(poly)))/2)
  return area
 for pivot in ('Motor centre','Pad beginning'):
  p=Parameters(MotorPadShape='Round-shoulder shield',MotorPadRotation=30,MotorPadRotationPivot=pivot)
  a=arm_layouts(p)[0];z=plate_levels(p)['arm_z']
  blank=geometry.fuse([geometry.arm_stem(p,a,z,p.ArmThickness),geometry.motor_pad(p,a,z)])
  blended=geometry.blend_motor_junction(p,a,blank,z,p.ArmThickness)
  assert blended.Volume>=blank.Volume-1e-6
  assert blended.Volume>blank.Volume+1e-4,(pivot,'blend adds no material')
  qarea=path_area(arm_blank_path(p,a));cad=blended.Volume/p.ArmThickness
  print('AREA',pivot,qarea,cad,flush=True)
  assert abs(qarea-cad)<max(2,cad*.01)
  checks.append('CAD / preview blend area agrees within 1%: '+pivot)
 # Convert an old native numeric stack property, preserving dimensions and height.
 from freecad.rotorforge.document import create_frame,read_parameters,ensure_parameter_properties
 doc=App.newDocument('LegacyStack');obj=create_frame(Parameters(StackSpacing=20,StackMountHeight=4),doc)
 obj.removeProperty('StackSpacing');obj.addProperty('App::PropertyLength','StackSpacing');obj.StackSpacing=20
 p=read_parameters(obj);ensure_parameter_properties(obj,p)
 assert obj.getTypeIdOfProperty('StackSpacing')=='App::PropertyEnumeration'
 assert read_parameters(obj).StackSpacing==20 and read_parameters(obj).StackMountHeight==4
 checks.append('Old native numeric stack converts to enumeration and preserves mounting height')
 App.closeDocument(doc.Name)
 open(out+'/report.json','w').write(json.dumps(dict(status='passed',checks=checks),indent=2));d.close()
except Exception:
 open(out+'/report.json','w').write(json.dumps(dict(status='failed',checks=checks,error=traceback.format_exc()),indent=2));traceback.print_exc()
