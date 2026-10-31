"""Overall preview, old document migration and protection exports."""
import sys,os,json,traceback,time
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters,load_parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.document import create_frame,update_frame,read_parameters
from freecad.rotorforge.exporters import export_package
root=Path(__file__).resolve().parents[1];out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];failures=[]
p=Parameters(FPVEnabled=True,VideoSystem='Digital',CameraForeAftOffset=20.,FlexCameraMode='Captured inserts',FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardUSBEnabled=True,FlexGuardUSBY=-6.,FlexGuardVentShape='Hexagons',FlexMotorProtectors=True,FlexProtectorRetention='Linked screw access',ArmEdgeFillet=3.,StandoffCount='6 (3 pairs)',StandoffPair3Y=-94,StandoffPair3Width=28,MidReachMode='Custom',MidRearReach=102,TopReachMode='Custom',TopRearReach=102)
try:
 d=App.newDocument('RotorForge061');obj=create_frame(p,d)
 for role in ('RearAccessoryMount','RearVTXMount','RearGPSTray','RearELRSMount'):
  old=d.addObject('Part::Feature',role);old.addProperty('App::PropertyLink','Parameters');old.Parameters=obj;old.addProperty('App::PropertyString','FrameRole');old.FrameRole=role
 obj.addProperty('App::PropertyBool','FlexRearEnabled');obj.FlexRearEnabled=True
 update_frame(obj,p);assert not any(o.Name.startswith(('RearAccessoryMount','RearVTXMount','RearGPSTray','RearELRSMount')) for o in d.Objects);assert 'FlexRearEnabled' not in obj.PropertiesList
 path=out/'RotorForge061.FCStd';d.saveAs(str(path));App.closeDocument(d.Name);d=App.openDocument(str(path));obj=d.getObject('FrameParameters');assert read_parameters(obj)==p
 assert obj.Proxy._restored_signature==p.signature()
 update_frame(obj,p);assert obj.Proxy._restored_signature is None;assert str(obj.GeneratorVersion)=='0.61.0'
 exported=Path(export_package(obj,str(out/'export')));assert len(list(exported.rglob('FlexibleParts/*.stl')))==8;assert list(exported.rglob('*.dxf')) and list(exported.rglob('*.svg'));App.closeDocument(d.Name)
 checks.append('Migration removes old rear parts/properties; eight current TPU solids survive save/reopen and export');print('PASS EXPORT',flush=True)
except Exception:failures.append(dict(name='Migration/export',error=traceback.format_exc()));traceback.print_exc()
try:
 import FreeCADGui as Gui
 from PySide import QtWidgets,QtGui
 Gui.getMainWindow=lambda:None
 from freecad.rotorforge.gui import FrameDialog,TopPreview
 from freecad.rotorforge import geometry,flex_geometry,protection_geometry
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
 def reject(*a,**k):raise AssertionError('Solid builder invoked in editor')
 geometry.build_shapes=reject;flex_geometry.make_flex=reject;protection_geometry.side_guards=reject;protection_geometry.motor_protectors=reject
 dialog=FrameDialog();dialog.resize(1400,900);dialog.show();app.processEvents()
 for index,q in enumerate((Parameters(),replace(p,FlexMotorProtectors=False,FlexSideGuards=False),replace(p,FlexSideGuards=False),replace(p,FlexMotorProtectors=False),p,replace(p,FlexGuardVentShape='Diamonds'))):
  dialog.set_values(q);dialog.refresh();assert dialog.values()==q
  for role in ('Overall','AllParts','Arms','ElectronicsGuardLeft','MotorProtectorFrontRight'):
   if role.startswith('Electronics') and not q.FlexSideGuards or role.startswith('MotorProtector') and not q.FlexMotorProtectors:continue
   idx=dialog.preview_mode.findData(role);assert idx>=0,role;dialog.preview_mode.setCurrentIndex(idx);app.processEvents();pix=dialog.preview.grab();assert dialog.preview.last_error is None,(role,dialog.preview.last_error)
   if role=='Overall':
    image=pix.toImage();bg=QtGui.QColor('#f3f6f8').rgb();colored=sum(image.pixel(x,y)!=bg for x in range(0,image.width(),4) for y in range(0,image.height(),4));assert colored>100,'Blank overall preview'
    pix.save(str(out/('Overall'+str(index)+'.png')))
 dialog.close();checks.append('Six editor configurations render the overall frame and part modes with no CAD solid calls');print('PASS EDITOR',flush=True)
except Exception:failures.append(dict(name='Editor',error=traceback.format_exc()));traceback.print_exc()
(out/'integration061.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
