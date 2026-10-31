"""Export native full-height guard sleeves and their circular inboard sections."""
import sys,os,json
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import load_parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.protection_layout import guard_layout
root=Path(__file__).resolve().parents[1];out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True)
p=load_parameters(root/'examples/Example_ForwardGuards_USB.json');shapes=build_shapes(p)
def mesh(s,role):
 v,f=s.tessellate(.12);return dict(role=role,vertices=[list(a) for a in v],faces=f)
def write(n,d):(out/(n+'.json')).write_text(json.dumps(d))
parts=[]
for role in ('BottomPlate','MidPlate','TopPlate','ElectronicsGuardLeft','ElectronicsGuardRight'):
 s=shapes[role].copy()
 if role=='TopPlate':s.translate(App.Vector(0,0,12))
 parts.append(mesh(s,role))
write('guards',[dict(title='Full-height foremost grips / top plate lifted',parts=parts)])
g=guard_layout(p)[1];post=g['stands'][0];sx,sy=post['point'];lo,hi=g['bands'][0];r=(p.StandoffDiameter+p.FlexGuardFit)/2+p.FlexGuardWall
crop=Part.makeBox(2*r+20,2*r+4,hi-lo+2,App.Vector(sx-r-1,sy-r-2,lo-1));detail=shapes[g['role']].common(crop)
metal=Part.makeCylinder(p.StandoffDiameter/2,post['length'],App.Vector(sx,sy,post['base']))
write('grip_height',[dict(title='Foremost post enclosed over its exposed height',parts=[mesh(detail,g['role']),mesh(metal,'Metal posts')])])
scenes=[]
for z,title in ((hi-1,'Upper sleeve / electronics on the left'),(lo+1,'Lower sleeve / local arm clearance')):
 section=detail.common(Part.makeBox(2*r+20,2*r+4,.15,App.Vector(sx-r-1,sy-r-2,z)))
 cap=max((f for f in section.Faces if f.BoundBox.ZLength<1e-5),key=lambda f:f.Area);wires=[cap.OuterWire]+[w for w in cap.Wires if not w.isSame(cap.OuterWire)]
 scenes.append(dict(title=title,parts=[dict(role=g['role'])],loops=[[[v.x,v.y] for v in w.discretize(Deflection=.001)] for w in wires]))
write('grip_sections',scenes)
# Current overview keeps unaffected USB/service/root illustrations available.
old=Path(os.environ.get('ROTORFORGE_BASE_FIGURES',str(out)))
if (old/'usb.json').exists() and (old/'service.json').exists() and (old/'arms.json').exists():
 write('features',[json.loads((out/'guards.json').read_text())[0],scenes[0],json.loads((old/'service.json').read_text())[-1],json.loads((old/'arms.json').read_text())[-1]])
print('GRIP FIGURES DONE',flush=True)
