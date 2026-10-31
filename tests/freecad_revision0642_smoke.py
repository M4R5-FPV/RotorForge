"""Rear wire exits below actual grip bands, including an open rear end."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.protection_layout import guard_layout,guard_wire_openings
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];failures=[]
p=Parameters(FlexSideGuards=True,FlexGuardWireEnabled=True,FlexGuardWirePairs='Rear',FlexGuardWireRearY=-46.,FlexGuardWireWidth=12.,FlexGuardStyle='Vented')
cases=[(d+'/'+str(gap),replace(p,PlateDesign=d,FlexGuardClearance=gap)) for d in ('2 plates','3 plates') for gap in (0.,1.)]
cases.append(('Under intermediate FC row',replace(p,FlexGuardExtendFront=True,StandoffCount='6 (3 pairs)',StandoffPair3Y=-94.,StandoffPair3Width=28.,MidReachMode='Custom',MidRearReach=102.,TopReachMode='Custom',TopRearReach=102.)))
for name,q in cases:
 try:
  s=build_shapes(q)
  for g in guard_layout(q):
   sh=s[g['role']];assert sh.isValid() and len(sh.Solids)==1
   for o in guard_wire_openings(q,g):
    y,z=o['y'],o['bottom'];probe=Part.makeBox(1000,4.,q.FlexGuardWireHeight*.6,App.Vector(-500,y,z+.1));assert sh.common(probe).Volume<1e-6,'Pocket obstructed below grip'
   rad=(q.StandoffDiameter+q.FlexGuardFit)/2+q.FlexGuardWall*.5
   for st,(lo,hi) in zip(g['stands'],g['bands']):
    sx,sy=st['point']
    for z in (lo+.1,(lo+hi)/2,hi-.1):assert sh.isInside(App.Vector(sx-g['sign']*rad,sy,z),1e-5,True),'Grip material lost'
  assert abs(s['ElectronicsGuardLeft'].Volume-s['ElectronicsGuardRight'].Volume)<.01
  if name=='3 plates/0.0':
   d=App.newDocument('RearExit');o=d.addObject('PartDesign::Feature','Guard');o.Shape=s['ElectronicsGuardRight'];d.recompute();path=out/'RearExit.FCStd';d.saveAs(str(path));App.closeDocument(d.Name);d=App.openDocument(str(path));assert d.Guard.Shape.isValid();d.Guard.Shape.exportStl(str(out/'RearExit.stl'));App.closeDocument(d.Name);checks.append('Native save/reopen and STL export')
  checks.append(name);print('PASS',name,flush=True)
 except Exception:failures.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
(out/'revision0642.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
