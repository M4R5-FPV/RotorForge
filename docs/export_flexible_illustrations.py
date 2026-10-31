"""Native figures for side guards, USB access, linked screw openings and arm fillets."""
import sys,os,json
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters,save_parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.flex_options import FLEX_OPTIONS
root=Path(__file__).resolve().parents[1];out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True)
p=Parameters(FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardUSBEnabled=True,StandoffCount='6 (3 pairs)',StandoffPair3Y=-94,StandoffPair3Width=28,MidReachMode='Custom',MidRearReach=102,TopReachMode='Custom',TopRearReach=102)
def mesh(s,role):
 v,f=s.tessellate(.18);return dict(vertices=[list(a) for a in v],faces=f,role=role)
def loops(s,role,title):
 cap=max((f for f in s.Faces if f.BoundBox.ZLength<1e-5),key=lambda f:f.Area);wires=[cap.OuterWire]+[w for w in cap.Wires if not w.isSame(cap.OuterWire)]
 return dict(title=title,parts=[dict(role=role)],loops=[[[v.x,v.y] for v in w.discretize(Deflection=.04)] for w in wires])
def write(n,d):(out/(n+'.json')).write_text(json.dumps(d))
s=build_shapes(p);parts=[]
for role in ('MidPlate','TopPlate','ElectronicsGuardLeft','ElectronicsGuardRight'):
 shape=s[role].copy()
 if role=='TopPlate':shape.translate(App.Vector(0,0,12))
 parts.append(mesh(shape,role))
write('guards',[dict(title='Full-height foremost grips / top plate lifted',parts=parts)])
scenes=[]
for shape in FLEX_OPTIONS['FlexGuardVentShape'][3]:
 q=replace(p,FlexGuardVentShape=shape,FlexGuardUSBEnabled=False);s=build_shapes(q)
 scenes.append(dict(title=shape,parts=[mesh(s['ElectronicsGuardLeft'],'ElectronicsGuardLeft')]))
write('vent_shapes',scenes)
s=build_shapes(p)['ElectronicsGuardLeft'];s=s.common(Part.makeBox(200,64,100,App.Vector(-100,-32,-20)))
write('usb',[dict(title='USB plug opening / centre section',parts=[mesh(s,'ElectronicsGuardLeft')])])
scenes=[]
for access in ('Motor screws','Linked screw access'):
 q=replace(p,FlexSideGuards=False,FlexMotorProtectors=True,FlexProtectorRetention=access,MotorPadShape='Scalloped shield');s=build_shapes(q)['MotorProtectorFrontRight']
 # Underside face shows the screw-head service paths and intact perimeter.
 cap=min((f for f in s.Faces if f.BoundBox.ZLength<1e-5),key=lambda f:f.BoundBox.ZMin)
 thin=Part.Face(cap.Wires).extrude(App.Vector(0,0,.1)) if False else s
 scenes.append(dict(title=access,parts=[mesh(s,'MotorProtectorFrontRight')]))
write('service',scenes)
scenes=[]
for radius in (0.,3.):
 q=replace(p,FlexSideGuards=False,StandoffLength=120.,ArmRootFit='Fitted miters',ArmRootWidth=22.,ArmBeamShape='Stepped beam',ArmEdgeFillet=radius)
 scenes.append(loops(build_shapes(q)['ArmFrontRight'],'Carbon side plate','Unchanged mounting root' if radius==0 else '3 mm fillets beyond root'))
write('arms',scenes)
write('features',[json.loads((out/'guards.json').read_text())[0],json.loads((out/'usb.json').read_text())[0],json.loads((out/'service.json').read_text())[-1],scenes[-1]])
save_parameters(root/'examples/Example_ForwardGuards_USB.json',p)
save_parameters(root/'examples/Example_LinkedMotorGuards.json',replace(p,FlexSideGuards=False,FlexMotorProtectors=True,FlexProtectorRetention='Linked screw access'))
save_parameters(root/'examples/Example_ArmFillets.json',q)
print('FIGURES DONE',flush=True)
