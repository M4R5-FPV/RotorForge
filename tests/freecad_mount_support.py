"""Native end-to-end regression for automatic mounting stock."""
import FreeCAD as App
import os,sys,json,traceback
from pathlib import Path
from dataclasses import replace
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters,plate_holes,arm_layouts
from freecad.rotorforge.geometry import build_shapes,carbon_roles,cylinder
from freecad.rotorforge import document as doc
from freecad.rotorforge.exporters import export_package
from freecad.rotorforge.mount_support import plate_supports
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
p=Parameters()
roots=replace(p,RootBoltLayout='Custom coordinates',RootBolt1X=20,RootBolt1Y=0,RootBolt2X=35,RootBolt2Y=10)
posts=replace(p,StandoffFrontMount='Custom position',StandoffRearMount='Custom position',StandoffWidth=85,StandoffLength=170)
cases=[('Default',p),('Displaced roots',roots),('Displaced posts',posts),('Two plates posts',replace(posts,PlateDesign='2 plates')),('Upper clamp roots',replace(roots,PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',ArmBracesEnabled=True)),('Lower clamp roots',replace(roots,PlateDesign='2 plates',TwoPlateArmPosition='Below bottom plate',ArmBracesEnabled=True)),('Fitted roots',replace(roots,ArmRootFit='Fitted miters')),('Press nut roots',replace(roots,ArmNutMount='M3 press nut')),('Short rear mid',replace(p,MidRearReach=35))]
shared=replace(roots,PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',StackMountHeight=8,StackHeight=15,StandoffFrontMount='Arm outer hole',StandoffRearMount='Arm outer hole')
cases += [('Shared posts on arms',shared),('Shared posts on upper clamp',replace(shared,ArmBracesEnabled=True))]
checks=[];failures=[]
for name,q in cases:
 try:
  shapes=build_shapes(q)
  for role in carbon_roles(q):
   shape=shapes[role];assert shape.isValid() and len(shape.Solids)==1,(name,role,'invalid or disconnected')
   if role in ('BottomPlate','MidPlate','TopPlate','ArmClampPlate','ArmLowerClampPlate'):
    for pt,hole,kind in plate_holes(q,role):
     if kind not in ('arm root','standoff'):continue
     b=shape.BoundBox
     r=max(hole,q.StandoffDiameter/2 if kind=='standoff' else 0)+q.MinimumWeb
     ring=cylinder(*pt,r,b.ZMin,b.ZLength).cut(cylinder(*pt,hole,b.ZMin-1,b.ZLength+2))
     assert ring.cut(shape).Volume<1e-5,(name,role,pt,'lost bearing stock')
  checks.append(name);print('PASS',name,flush=True)
 except Exception:failures.append((name,traceback.format_exc()));print('FAIL',name,failures[-1][1],flush=True)
try:
 f=doc.create_frame(posts,App.newDocument('MountGrowth'));f.Document.saveAs(str(out/'growth.FCStd'));App.closeDocument(f.Document.Name)
 d=App.openDocument(str(out/'growth.FCStd'));f=d.getObject('FrameParameters');assert doc.read_parameters(f)==posts
 folder=export_package(f,out/'export');assert (folder/'ExportInfo.json').is_file()
 doc.update_frame(f,p);restored=doc.component_objects(f);original=build_shapes(p)
 for role in carbon_roles(p):assert abs(restored[role].Shape.Volume-original[role].Volume)<1e-6
 App.closeDocument(d.Name);checks.append('Native save/reopen, exports and reversible growth')
except Exception:failures.append(('Persistence',traceback.format_exc()));print(failures[-1],flush=True)
(out/'checks.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2))
raise SystemExit(bool(failures))
