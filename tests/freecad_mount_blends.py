"""Exact checks for additive junction blends and press-in nut bearing stock."""
import FreeCAD as App
import Part
import sys,json,os,math
from pathlib import Path
from dataclasses import replace
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
from freecad.rotorforge.parameters import Parameters,arm_layouts
from freecad.rotorforge.mount_support import arm_supports,plate_supports,support_distance
from freecad.rotorforge.mount_blends import blend_shape
from freecad.rotorforge.plate_fillets import _corners,_away
from freecad.rotorforge.geometry import _straight_arm_stem,_base_bottom_plate_blank,fuse,capsule,build_shapes
p=Parameters(RootBoltLayout='Custom coordinates',RootBolt1X=20,RootBolt1Y=0,RootBolt2X=35,RootBolt2Y=10)
a=arm_layouts(p)[0];pads=arm_supports(p,a)
raw=fuse([_straight_arm_stem(p,a,0,5)]+[capsule(x,y,r,0,5) for x,y,r in pads])
q=Parameters(StandoffWidth=85,StandoffLength=170)
pads2=plate_supports(q,'BottomPlate')
raw2=fuse([_base_bottom_plate_blank(q,0,2)]+[capsule(x,y,r,0,2) for x,y,r in pads2])
checks=[]
for label,params,before,supports in [('Arm root',p,raw,pads),('Plate standoff',q,raw2,pads2)]:
 after=blend_shape(params,before,supports)
 assert before.cut(after).Volume<1e-6,label+' lost material'
 assert after.Volume>before.Volume+.01,label+' has no rounding'
 cap=max((f for f in after.Faces if f.BoundBox.ZLength<1e-5),key=lambda f:f.CenterOfMass.z)
 for point,limit in _corners(cap.OuterWire):
  if support_distance((point.x,point.y),supports)<-1e-5:continue
  adj=[e for e in cap.OuterWire.Edges if any((v.Point-point).Length<1e-6 for v in e.Vertexes)]
  d=_away(adj[0],point)+_away(adj[1],point)
  if d.Length<1e-7:continue
  d.normalize();assert cap.isInside(point+d*.001,1e-7,False),label+' retains a sharp mounting junction'
 checks.append(label+' tangent additive blends');print('PASS',checks[-1],flush=True)
for label,params in [('Flange margin',replace(p,ArmNutMount='M3 press nut',MinimumWeb=2.5,MotorCenterDiameter=5)),('Large recessed insert',replace(p,ArmNutMount='M3 press nut',PressNutFlangeDiameter=8.,PressNutFlangeRecess=.3,NutRecessClearance=.4)),('Stack press nuts',Parameters(StackPressNuts=True,BodyWidth=40,RootInset=5,PressNutFlangeDiameter=10)),('Insert edge fillets',replace(p,ArmNutMount='M3 press nut',MidEdgeFillet=3))]:
 shapes=build_shapes(params)
 from freecad.rotorforge.nut_seats import seats
 for seat in seats(params):
  if seat['mode']!='M3 press nut':continue
  shape=shapes[seat['role']];x,y=seat['point'];z=seat['z']-seat['axis']*.04
  inner=(params.PressNutFlangeDiameter+(params.NutRecessClearance if seat['depth'] else 0))/2
  ring=Part.makeCylinder(inner+max(1.,params.MinimumWeb),.02,App.Vector(x,y,z-.01)).cut(Part.makeCylinder(inner+.001,.04,App.Vector(x,y,z-.02)))
  assert ring.cut(shape).Volume<1e-5,(label,seat['role'],'incomplete flange margin')
 checks.append(label);print('PASS',label,flush=True)
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
(out/'blend_checks.json').write_text(json.dumps(dict(checks=checks,failures=[]),indent=2))
