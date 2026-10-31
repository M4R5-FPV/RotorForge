import sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,arm_brace_layouts,arm_layouts
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.airflow_gui import finished_part_path,QtCore
from test_mid_follow import matched_mid
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True);checks=[]
for layout in ('True X','Stretched X','Deadcat'):
 for position in ('Above bottom plate','Below bottom plate'):
  for fitted in (False,True):
   p=(matched_mid(PlateDesign='2 plates',ArmBracesEnabled=True,TwoPlateArmPosition=position,Layout=layout) if fitted else Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,TwoPlateArmPosition=position,Layout=layout))
   parts=g.build_for_update(p);c=arm_brace_layouts(p)[0]
   for role in ('ArmClampPlate','ArmLowerClampPlate'):
    if role not in parts or parts[role].isNull():continue
    s=parts[role];assert s.isValid() and len(s.Solids)==1
    z=s.BoundBox.Center.z
    for y in (c['rear']+1,c['front']-1):assert not s.isInside(App.Vector(0,y,z),1e-6,True),(layout,position,fitted,role)
    # Compare native and preview over a sampled grid away from boundaries.
    path=finished_part_path(p,role)
    for x in range(-30,31,5):
     for y in range(-45,46,5):
      point=App.Vector(x+.13,y+.17,z)
      inside=s.isInside(point,1e-6,True);preview=path.contains(QtCore.QPointF(x+.13,y+.17))
      if inside!=preview:
       distance=min(Part.Vertex(point).distToShape(face)[0] for face in s.Faces)
       assert distance<.15,(layout,position,fitted,role,x,y,inside,preview,distance)
    target=out/(layout.replace(' ','')+position[:5]+str(fitted)+role+'.step');s.exportStep(str(target));assert Part.read(str(target)).isValid()
   checks.append([layout,position,fitted,'connected, arm-matched ends, preview and STEP'])
# Local post bearing pads and incremental rebuild isolation.
p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,StandoffFrontMount='Arm inner hole',StrapSlotsEnabled=False)
parts=g.build_for_update(p);assert parts['ArmLowerClampPlate'].isValid();q=replace(p,UndersideClampThickness=3.)
g.build_for_update(q);assert not any(role.startswith('ArmFront') or role.startswith('ArmRear') for role in g.build_report(q)['rebuilt'])
doc=App.newDocument();frame=d.create_frame(q,doc);doc.saveAs(str(out/'ClampFollow087.FCStd'));App.closeDocument(doc.Name)
doc=App.openDocument(str(out/'ClampFollow087.FCStd'));assert d.read_parameters(doc.getObject('FrameParameters'))==q;App.closeDocument(doc.Name)
checks.append('local post pads, arm reuse and saved frame');(out/'checks.json').write_text(json.dumps(checks,indent=2));print('PASS',len(checks),flush=True)
