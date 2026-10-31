"""Exact trimmed Bezier curves survive individual CNC DXF/SVG export."""
import sys,os,json,traceback,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,plate_holes
from freecad.rotorforge.geometry import bottom_plate_blank,cut_holes
from freecad.rotorforge.bottom_nose import NOSE_SHAPES
from freecad.rotorforge.exporters import profile_entities,write_dxf,write_svg
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);folder=out/'nose_exports';folder.mkdir(parents=True,exist_ok=True);checks=[];failures=[];expected=[]
for name in NOSE_SHAPES:
 try:
  p=Parameters(BottomNoseShape=name);sh=bottom_plate_blank(p,0,p.BottomThickness);entities=profile_entities(sh)
  face=max((f for f in sh.Faces if abs(f.normalAt(0,0).z)>.999999),key=lambda f:f.CenterOfMass.z)
  curves=[e for w in face.Wires for e in w.Edges if e.Curve.__class__.__name__=='BezierCurve'];splines=[e for e in entities if e[0]=='SPLINE'];assert len(curves)==len(splines)
  samples=[]
  for edge,entry in zip(curves,splines):
   pts=list(zip(entry[1::2],entry[2::2]));reference=[]
   for t in (0.,.25,.5,.75,1.):
    point=edge.valueAt(edge.FirstParameter+t*(edge.LastParameter-edge.FirstParameter));u=1-t
    x,y=(u**3*pts[0][j]+3*u*u*t*pts[1][j]+3*u*t*t*pts[2][j]+t**3*pts[3][j] for j in (0,1))
    assert math.hypot(x-point.x,y-point.y)<1e-6;reference.append((point.x,point.y))
   samples.append(reference)
  token=name.replace(' ','_');write_dxf(folder/(token+'.dxf'),[('BottomPlate',entities)]);write_svg(folder/(token+'.svg'),[('BottomPlate',entities)],100,150,margin=0.)
  expected.append(dict(token=token,samples=samples));checks.append(name);print('PASS',name,flush=True)
 except Exception:failures.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
(out/'exports065.json').write_text(json.dumps(dict(checks=checks,failures=failures,expected=expected),indent=2));print('DONE',len(checks),len(failures),flush=True)
