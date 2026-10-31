"""Bottom-only nose shapes in both layouts, camera fits, masks and exports."""
import sys,os,json,traceback
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters,bottom_bounds,save_parameters
from freecad.rotorforge.bottom_nose import NOSE_SHAPES
from freecad.rotorforge.geometry import build_shapes
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];failures=[];scenes=[]
p=Parameters();baseline=build_shapes(p)
cases=[(design+'/'+name,replace(p,PlateDesign=design,BottomNoseShape=name)) for design in ('2 plates','3 plates') for name in NOSE_SHAPES]
cases += [('FPV/'+name,replace(p,FPVEnabled=True,BottomNoseShape=name)) for name in NOSE_SHAPES if name!='Straight']
cases += [('Wide centre / round',replace(p,BottomNoseShape='Rounded nose',BottomCentreWidth=80.,MidCentreWidth=80.,CentreSectionLength=180.)),('Custom reach / swept',replace(p,BottomNoseShape='Swept shoulders',BottomReachMode='Custom',BottomFrontReach=95.)),('End fillet',replace(p,BottomNoseShape='Flat-tip nose',BottomEdgeFillet=2.))]
for title,q in cases:
 try:
  s=build_shapes(q);bottom=s['BottomPlate'];assert bottom.isValid() and len(bottom.Solids)==1
  br,bf=bottom_bounds(q);assert bottom.BoundBox.YMax<=bf+1e-5
  if q.PlateDesign==p.PlateDesign and not q.FPVEnabled and title.startswith('3 plates/'):
   for role in ('TopPlate','MidPlate','ArmFrontRight','ArmFrontLeft','ArmRearRight','ArmRearLeft'):
    assert abs(s[role].Volume-baseline[role].Volume)<1e-5,(role,'unexpected change')
   if q.BottomNoseShape!='Straight':assert bottom.Volume<baseline['BottomPlate'].Volume-1e-3
   v,f=bottom.tessellate(.08);scenes.append(dict(title=q.BottomNoseShape,vertices=[list(a) for a in v],faces=f,front=bf,depth=q.BottomNoseDepth))
  if title=='3 plates/Rounded nose':
   bottom.exportStep(str(out/'RoundedNose.step'));bottom.exportStl(str(out/'RoundedNose.stl'));save_parameters(Path(__file__).resolve().parents[1]/'examples/Example_RoundedBottomNose.json',q)
  checks.append(title);print('PASS',title,flush=True)
 except Exception:failures.append(dict(name=title,error=traceback.format_exc()));traceback.print_exc()
(out/'nose_shapes.json').write_text(json.dumps(scenes));(out/'revision065.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
