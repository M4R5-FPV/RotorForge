"""Native wire-exit clearance, connected solids, save/reopen and export checks."""
import sys,os,json,traceback
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.protection_layout import guard_layout,guard_wire_openings
from freecad.rotorforge.flex import validate_flex
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];failures=[]
p=Parameters(FlexSideGuards=True,FlexGuardWireEnabled=True)
cases=[(design+'/'+style,replace(p,PlateDesign=design,FlexGuardStyle=style)) for design in ('2 plates','3 plates') for style in ('Solid','Vented')]
cases += [('Extended/USB/rounded vents',replace(p,FlexGuardExtendFront=True,FlexGuardUSBEnabled=True,FlexGuardVentShape='Rounded slots')),('Left/rear/custom',replace(p,FlexGuardWireSide='Left',FlexGuardWirePairs='Rear',FlexGuardWireWidth=12.,FlexGuardWireHeight=4.,FlexGuardWireRearY=-23.)),('Upper strip',replace(p,FlexGuardExtendFront=True,MidReachMode='Custom',MidFrontReach=24.,FlexGuardWireFrontY=32.,FlexGuardWireWidth=8.)),('Disabled preserves stock',replace(p,FlexGuardWireEnabled=False))]
for name,q in cases:
 try:
  assert not validate_flex(q)[0],validate_flex(q)[0]
  shapes=build_shapes(q)
  for g in guard_layout(q):
   shape=shapes[g['role']];assert shape.isValid() and len(shape.Solids)==1
   for o in guard_wire_openings(q,g):
    y,w,h,z=o['y'],o['width'],o['height'],o['bottom']
    probe=Part.makeBox(1000,w*.5,h*.7,App.Vector(-500,y-w*.25,z-.1))
    assert shape.common(probe).Volume<1e-6,'Wire exit blocked'
   for st,(lo,hi) in zip(g['stands'],g['bands']):
    sx,sy=st['point'];rad=(q.StandoffDiameter+q.FlexGuardFit)/2+q.FlexGuardWall*.5
    assert shape.isInside(App.Vector(sx-g['sign']*rad,sy,(lo+hi)/2),1e-5,True),'Grip lost'
  checks.append(name);print('PASS',name,flush=True)
  if name=='3 plates/Solid':
   for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
    shape=shapes[role];shape.exportStep(str(out/(role+'.step')));shape.exportStl(str(out/(role+'.stl')))
   doc=App.newDocument('WireOpenings');obj=doc.addObject('PartDesign::Feature','Guard');obj.Shape=shapes['ElectronicsGuardLeft'];doc.recompute();doc.saveAs(str(out/'WireOpenings.FCStd'));App.closeDocument(doc.Name);doc=App.openDocument(str(out/'WireOpenings.FCStd'));assert doc.Guard.Shape.isValid();App.closeDocument(doc.Name);checks.append('Native save/reopen and STEP/STL exports')
 except Exception:failures.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
(out/'revision063.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
