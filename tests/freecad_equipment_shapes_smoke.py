"""Native checks for nominal equipment moments, pad outlines and fitted keys."""
import os,sys,json,traceback,math
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,ENUMERATIONS,plate_levels
from freecad.rotorforge.geometry import build_shapes,carbon_roles
from freecad.rotorforge.mass_properties import mass_properties
from freecad.rotorforge.battery import make_pad
from freecad.rotorforge.document import create_frame,read_parameters
from freecad.rotorforge.part_preview import pad_path
checks=[]
def check(ok,msg):
 if not ok:raise AssertionError(msg)
 checks.append(msg)
try:
 p=Parameters();s=build_shapes(p);m=mass_properties(p,s)
 check(abs(m['equipment_mass_g']-sum(i['mass_g'] for i in m['equipment_items']))<1e-9,'equipment sum')
 check(abs(m['loaded_mass_g']-m['equipped_mass_g']-p.BatteryMass)<1e-9,'loaded sum')
 for j in range(3):
  moment=m['frame_mass_g']*m['frame_cg_mm'][j]+sum(i['mass_g']*i['centre_mm'][j] for i in m['equipment_items'])
  check(abs(moment/m['equipped_mass_g']-m['equipped_cg_mm'][j])<1e-9,'equipment moments '+str(j))
 check(abs(m['equipped_cg_mm'][0])<1e-8,'symmetric mass')
 check(len([i for i in m['equipment_items'] if i['part']=='Motor'])==4,'four motors')
 check(not any(i['part'] in ('Camera','VTX') for i in m['equipment_items']),'FPV disabled excludes video')
 p2=replace(p,FPVEnabled=True,ShowReferences=False);m2=mass_properties(p2,build_shapes(p2))
 check(any(i['part']=='Camera' for i in m2['equipment_items']),'hidden references still contribute')
 p3=replace(p,MotorMass=p.MotorMass+10);m3=mass_properties(p3,build_shapes(p3));check(abs(m3['equipped_mass_g']-m['equipped_mass_g']-40)<1e-8,'per motor override')
 m4=mass_properties(replace(p,StandoffHeight=40),build_shapes(replace(p,StandoffHeight=40)))
 check(m4['standoff_mass_g']>m['standoff_mass_g'],'taller standoffs heavier')
 check('equipped_mass_g' not in mass_properties(replace(p,EstimateComponents=False),s),'optional estimates')
 for shape in ENUMERATIONS['LiPoPadShape']:
  for mount in ('Top plate','Bottom plate'):
   a=replace(p,LiPoPadEnabled=True,LiPoPadShape=shape,BatteryMount=mount);ss=build_shapes(a)
   check(ss['LiPoPad'].isValid() and len(ss['LiPoPad'].Solids)==1,shape+' '+mount+' connected')
   blank=make_pad(a,ss['TopPlate' if mount=='Top plate' else 'BottomPlate'],False)
   if shape=='Mounting plate outline':
    carrier=ss['TopPlate' if mount=='Top plate' else 'BottomPlate'];area=max(f.Area for f in carrier.Faces if f.normalAt(0,0).z>.999)
    check(0<blank.Volume/a.LiPoPadThickness<=area+1e-6,mount+' carrier-supported outline after standoff access')
   q=pad_path(a);check(not q.isEmpty(),shape+' preview')
   from freecad.rotorforge.airflow_gui import QtGui
   box=q.boundingRect();scale=10;im=QtGui.QImage(math.ceil(box.width()*scale)+4,math.ceil(box.height()*scale)+4,QtGui.QImage.Format_Grayscale8);im.fill(0)
   painter=QtGui.QPainter(im);painter.scale(scale,scale);painter.translate(-box.left()+.2,-box.top()+.2);painter.fillPath(q,QtGui.QColor('white'));painter.end()
   qtarea=bytes(im.constBits()).count(255)/scale**2;cadarea=blank.Volume/a.LiPoPadThickness
   check(abs(qtarea-cadarea)/cadarea<.025,shape+' '+mount+' Qt/CAD outline match')
 for mode,position in (('3 plates','Below bottom plate'),('2 plates','Below bottom plate'),('2 plates','Above bottom plate')):
  for shape in ENUMERATIONS['KeystoneShape']:
   a=replace(p,PlateDesign=mode,TwoPlateArmPosition=position,ArmBracesEnabled=mode=='2 plates',ArmRootFit='Fitted miters',ArmRootY=8,RootInset=17,RootExtension=20,RootBoltSpacing=8,StandoffHeight=35,Wheelbase=270,KeystoneEnabled=True,KeystoneShape=shape,KeystoneWidth=7,KeystoneLength=7)
   ss=build_shapes(a);key=ss['ArmKeystone'];check(key.isValid() and len(key.Solids)==1,mode+' '+shape+' connected')
   for arm in ('FrontRight','FrontLeft','RearLeft','RearRight'):
    check(key.common(ss['Arm'+arm]).Volume<1e-6,shape+' no overlap '+arm)
    check(key.distToShape(ss['Arm'+arm])[0]<.25,shape+' seats '+arm)
 settings=create_frame(replace(p,LiPoPadEnabled=True,LiPoPadShape='Hourglass'),App.newDocument('NewFeatures'))
 check(settings.LoadedMassGrams>settings.EquippedMassGrams>settings.FrameMassGrams,'native result outputs')
 savepath=Path(os.environ['ROTORFORGE_TEST_OUTPUT'])/'equipment.FCStd';savepath.parent.mkdir(parents=True,exist_ok=True)
 settings.Document.saveAs(str(savepath.resolve()))
 check(read_parameters(settings).LiPoPadShape=='Hourglass','native parameters')
 App.closeDocument(settings.Document.Name)
 reopened=App.openDocument(str(savepath.resolve()));restored=next(o for o in reopened.Objects if 'Wheelbase' in o.PropertiesList)
 check(read_parameters(restored).LiPoPadShape=='Hourglass','native reopen settings')
 check(restored.LoadedMassGrams>restored.EquippedMassGrams>restored.FrameMassGrams,'native reopen results')
 App.closeDocument(reopened.Name)
 from freecad.rotorforge.exporters import export_package
 from freecad.rotorforge.document import create_frame
 settings=create_frame(Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline'),App.newDocument('EquipmentExport'))
 folder=export_package(settings,Path(os.environ['ROTORFORGE_TEST_OUTPUT']))
 import csv
 rows=list(csv.DictReader((folder/'EquipmentMass.csv').open()))
 mm=json.loads((folder/'MassProperties.json').read_text())
 check(abs(sum(float(row['Mass_g']) for row in rows)-mm['equipment_mass_g'])<1e-8,'export equipment sum')
 check(abs(mm['loaded_mass_g']-mm['equipped_mass_g']-Parameters().BatteryMass)<1e-8,'export loaded sum')
 check((folder/'LiPoPad/LiPoPad.stl').is_file(),'full-outline pad export')
 App.closeDocument(settings.Document.Name)
 report={'status':'passed','checks':checks}
except Exception:report={'status':'failed','checks':checks,'error':traceback.format_exc()}
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);(out/'report.json').write_text(json.dumps(report,indent=2))
