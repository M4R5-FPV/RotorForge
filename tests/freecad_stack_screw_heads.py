"""Native geometry regression: stack screw heads remain outside the carrier."""
import sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,plate_levels,stack_mounting_role,stack_reference_z
from freecad.rotorforge.hardware_layout import hardware_layout,SIZES
from freecad.rotorforge.hardware_refs import screw
import Part,FreeCAD as App
checks=[]
for d in SIZES:
 shape=screw(d,20.,False,0.)
 assert shape.isValid() and len(shape.Solids)==1,(d,shape.check())
 assert shape.BoundBox.ZMin<-.4*d
 assert shape.common(Part.makeCylinder(.95*d,.55*d,App.Vector(0,0,-.55*d))).Volume>0
 checks.append('valid connected button head '+str(d))
for mode in ['2 plates','3 plates']:
 for clamp in [False,True]:
  for press in [False,True]:
   p=Parameters(PlateDesign=mode,ArmBracesEnabled=clamp,StackPressNuts=press)
   deck=plate_levels(p)['stack_deck_z'];role=stack_mounting_role(p)
   thickness=p.ClampThickness if role=='MidPlate' else p.ArmBraceThickness if role=='ArmClampPlate' else p.BottomThickness
   for s in hardware_layout(p):
    if s['group']!='Stack hardware':continue
    assert abs(s['point'][2]-(deck-thickness))<1e-8
    assert not s.get('stud')
    sh=screw(s['diameter'],s['length'],s['nut'],s['nut_distance'])
    assert sh.isValid() and len(sh.Solids)==2
    assert abs(s['point'][2]+s['nut_distance']-(stack_reference_z(p)+p.StackHeight))<1e-8
   checks.append((mode,clamp,press))
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True)
(out/'screw_heads.json').write_text(json.dumps({'checks':checks,'failures':[]},indent=2))
print('PASS',checks,flush=True)
