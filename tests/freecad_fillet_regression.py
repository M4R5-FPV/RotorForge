import sys,json,traceback,os,time,itertools
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes,carbon_roles
from freecad.rotorforge.cutouts import encode_patterns,CUTOUT_TYPES
from freecad.rotorforge.plate_fillets import _corners
checks=[];fail=[]
def run(p,label,check_holes=False):
 t=time.perf_counter()
 try:
  s=build_shapes(p)
  for role in carbon_roles(p):assert s[role].isValid() and len(s[role].Solids)==1,role
  if check_holes:
   cap=max((f for f in s['TopPlate'].Faces if f.BoundBox.ZLength<1e-5),key=lambda f:f.Area)
   sharp=sum(len(_corners(w)) for w in cap.Wires)
   assert sharp==0,('sharp cutout junctions',sharp)
  checks.append(dict(name=label,seconds=round(time.perf_counter()-t,3)));print('PASS',label,flush=True)
 except Exception:fail.append(dict(name=label,error=traceback.format_exc()));print('FAIL',label,fail[-1]['error'],flush=True)
for name,radius in itertools.product(('Rounded rectangle','Chamfered rectangle','Tapered front','Tapered rear','Hexagonal','Faceted shield','Octagonal'),(1.,3.,5.)):
 run(Parameters(BottomPlateShape=name,MidPlateShape=name,TopPlateShape=name,BottomEdgeFillet=radius,MidEdgeFillet=radius,TopEdgeFillet=radius),name+' / '+str(radius))
for name in CUTOUT_TYPES:
 run(Parameters(TopEdgeFillet=3,TopFilletOpenings=True,CutoutPatterns=encode_patterns([dict(role='TopPlate',shape=name,width=10,length=16)])),'Internal '+name,True)
for name in ('Rectangle','Triangle','Circle','Ellipse'):
 run(Parameters(TopEdgeFillet=3,TopFilletOpenings=True,CutoutPatterns=encode_patterns([dict(role='TopPlate',mode='Outline notch',shape=name,width=8,length=12,x=21,y=0)])),'Edge notch '+name,True)
for name in ('Rectangle','Circle'):
 pats=[dict(role='TopPlate',shape='Rectangle',width=10,length=16,x=-2),dict(role='TopPlate',shape=name,width=10,length=12,x=4)]
 run(Parameters(TopEdgeFillet=3,TopFilletOpenings=True,CutoutPatterns=encode_patterns(pats)),'Combined rectangle + '+name,True)
for pos in ('Below bottom plate','Above bottom plate'):
 run(Parameters(PlateDesign='2 plates',TwoPlateArmPosition=pos,ArmBracesEnabled=True,KeystoneEnabled=True,BottomEdgeFillet=3,TopEdgeFillet=3,ClampEdgeFillet=3),'Two plate clamps / '+pos)
run(Parameters(BottomCentreWidth=70,MidCentreWidth=70,TopCentreWidth=70,BottomEdgeFillet=3,MidEdgeFillet=3,TopEdgeFillet=3),'Widened centres / 3 mm')
(Path(os.environ['ROTORFORGE_TEST_OUTPUT'])/'fillet_report.json').write_text(json.dumps(dict(status='failed' if fail else 'passed',checks=checks,failures=fail),indent=2));print('DONE',len(checks),len(fail),flush=True)
