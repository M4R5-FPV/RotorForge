"""Native pad, battery, mass/CG, flat preview and manufacturing checks."""
import os,json,math,traceback,sys
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes,carbon_roles,physical_roles,flat_plate_shape
from freecad.rotorforge.battery import battery_levels,make_pad,mounting_role,printable_pad
from freecad.rotorforge.mass_properties import mass_properties
from freecad.rotorforge.document import create_frame,update_frame,read_parameters,component_objects
from freecad.rotorforge.exporters import export_package
from freecad.rotorforge.part_preview import part_path,preview_roles
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[]
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def area(path):
 # Raster integration honours Qt fill rules (including rewound hole polygons).
 from freecad.rotorforge.airflow_gui import QtCore,QtGui
 box=path.boundingRect();scale=10
 image=QtGui.QImage(math.ceil(box.width()*scale)+4,math.ceil(box.height()*scale)+4,QtGui.QImage.Format_Grayscale8);image.fill(0)
 painter=QtGui.QPainter(image);painter.scale(scale,scale);painter.translate(-box.left()+.2,-box.top()+.2);painter.fillPath(path,QtGui.QColor('white'));painter.end()
 return bytes(image.constBits()).count(255)/scale**2
cases=[Parameters(LiPoPadEnabled=True),
 Parameters(LiPoPadEnabled=True,LiPoPadPattern='Cross grooves',BatteryRotation=15,BatteryY=10,BatteryMount='Bottom plate'),
 Parameters(PlateDesign='2 plates',LiPoPadEnabled=True,BatteryMount='Bottom plate',LiPoPadWidth=18,LiPoPadLength=24,LiPoPadShape='Rectangle',LiPoPadFollowPlate=False),
 Parameters(PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',ArmBracesEnabled=True,LiPoPadEnabled=True,LiPoPadShape='Capsule',LiPoPadFollowPlate=False,LiPoPadPattern='Transverse grooves',BatteryRotation=-25),
 Parameters(FPVEnabled=True,LiPoPadEnabled=True,LiPoPadPattern='Cross grooves',BatteryY=-5),
 Parameters(LiPoPadEnabled=True,LiPoPadPattern='Cross grooves',CutoutPatterns=json.dumps([{'role':'TopPlate','shape':'Circle','mode':'Interior','width':8.,'length':8.,'x':0.,'y':0.,'rotation':0.,'columns':1,'rows':1,'pitch_x':12.,'pitch_y':12.,'enabled':True}]))]
try:
 for i,p in enumerate(cases):
  s=build_shapes(p);pad=s['LiPoPad'];check(pad.isValid() and len(pad.Solids)==1,f'{i}: pad connected')
  blank=make_pad(p,s[mounting_role(p)],grooves=False)
  check(blank.Volume+1e-6>=pad.Volume,f'{i}: grooves remove material')
  if p.LiPoPadPattern!='Solid':check(blank.Volume-pad.Volume>1,f'{i}: grooves are present')
  printable=printable_pad(p,pad);check(abs(printable.BoundBox.ZMin)<1e-6,f'{i}: STL base at zero')
  z=battery_levels(p);check(abs(s['BatteryEnvelope'].BoundBox.ZMin-z['battery_z'])<1e-6,f'{i}: battery follows support')
  m=mass_properties(p,s);total=0.;moments=[0.,0.,0.]
  for role in physical_roles(p):
   density=p.CarbonDensity if role in carbon_roles(p) else p.StandoffDensity if role=='Standoffs' else p.LiPoPadDensity
   for solid in s[role].Solids:
    mass=solid.Volume*density/1000;total+=mass
    for j,c in enumerate((solid.CenterOfMass.x,solid.CenterOfMass.y,solid.CenterOfMass.z)):moments[j]+=mass*c
  check(abs(total-m['frame_mass_g'])<1e-8,f'{i}: frame mass independent sum')
  check(all(abs(moments[j]/total-m['frame_cg_mm'][j])<1e-8 for j in range(3)),f'{i}: CG independent moments')
  check(abs(m['frame_plus_battery_mass_g']-total-p.BatteryMass)<1e-8,f'{i}: battery mass separate')
  for role in preview_roles(p):
   q=part_path(p,role,align=False)
   flat=blank if role=='LiPoPad' else flat_plate_shape(s[role],role,p)
   expected=flat.Volume/(p.LiPoPadThickness if role=='LiPoPad' else p.CameraBracketThickness if role.startswith('Camera') else flat.BoundBox.ZLength)
   check(abs(area(q)-expected)/expected<.025,f'{i}: {role} preview finished area')
  settings=create_frame(p,App.newDocument('Battery'+str(i)))
  check(abs(settings.FrameMassGrams-total)<1e-6,f'{i}: native mass result')
  check(settings.FrameCG.distanceToPoint(App.Vector(*m['frame_cg_mm']))<1e-6,f'{i}: native CG result')
  if i in (0,1,4,5):
   folder=export_package(settings,out)
   for filename in ['LiPoPad/LiPoPad.stl','LiPoPad/LiPoPad_flat.step','LiPoPad/LiPoPad_assembled.step','LiPoPad/LiPoPad_outline.svg','LiPoPad/LiPoPad_outline.dxf','MassProperties.json']:
    check((folder/filename).is_file(),f'{i}: export {filename}')
   import csv
   rows=list(csv.DictReader((folder/'PartsList.csv').open()))
   known_mass=sum(float(row['Estimated_mass_g'] or 0)*int(row['Quantity']) for row in rows)
   check(abs(known_mass-total)<.02,f'{i}: parts-list quantities and unit masses')
   info=json.loads((folder/'ExportInfo.json').read_text());check(abs(info['mass_properties']['frame_mass_g']-total)<1e-6,f'{i}: exported mass')
   roles=[item['role'] for sheet in info['cutting_layout']['sheets'] for item in sheet['parts']]
   check('LiPoPad' not in roles and 'BatteryEnvelope' not in roles,f'{i}: pad/battery excluded from carbon nesting')
  filename=out/f'battery-{i}.FCStd';settings.Document.saveAs(str(filename.resolve()));App.closeDocument(settings.Document.Name)
  doc=App.openDocument(str(filename.resolve()));settings=next(o for o in doc.Objects if 'Wheelbase' in o.PropertiesList);check(read_parameters(settings)==p,f'{i}: native parameter round trip');App.closeDocument(doc.Name)
 report={'status':'passed','checks':checks}
except Exception:report={'status':'failed','checks':checks,'error':traceback.format_exc()};print(report['error'],flush=True)
(out/'report.json').write_text(json.dumps(report,indent=2))
