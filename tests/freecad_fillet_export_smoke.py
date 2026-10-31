import sys,json,traceback,os,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.cutouts import encode_patterns
from freecad.rotorforge.plate_fillets import apply_plate_fillet
from freecad.rotorforge.document import create_frame,update_frame,read_parameters
from freecad.rotorforge.exporters import export_package
from dataclasses import replace
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True);checks=[]
try:
 p=Parameters(CutoutPatterns=encode_patterns([dict(role='TopPlate',shape='Rectangle',width=10,length=16)]));a=build_shapes(p)['TopPlate'];b=build_shapes(replace(p,TopEdgeFillet=3,TopFilletOpenings=True))['TopPlate']
 expected=4*3**2*(1-math.pi/4)*p.TopThickness;assert abs((b.Volume-a.Volume)-expected)<1e-5,(b.Volume-a.Volume,expected)
 checks.append('Four exact 3 mm internal arcs match the analytic rounded-rectangle volume')
 stock=Part.makeBox(100,100,3,App.Vector(-50,-50,0));bore=Part.makeCylinder(2,5,App.Vector(0,0,-1));cone=Part.makeCone(2,4,2,App.Vector(0,0,1))
 opening=Part.makeBox(10,16,5,App.Vector(15,-8,-1));source=stock.cut(bore.fuse(cone).fuse(opening));finished=apply_plate_fillet(replace(p,TopEdgeFillet=3,TopFilletOpenings=True),'TopPlate',source)
 assert finished.isValid() and len(finished.Solids)==1;assert finished.common(bore.fuse(cone)).Volume<1e-6
 checks.append('Through-drill and countersink volumes remain empty and unchanged')
 p=Parameters(FPVEnabled=True,StandoffHeight=30,BottomEdgeFillet=3,MidEdgeFillet=3,TopEdgeFillet=3,LiPoPadEnabled=True,CutoutPatterns=encode_patterns([dict(role='TopPlate',shape='Cross',width=10,length=16)]))
 d=App.newDocument('Fillet056');obj=create_frame(replace(p,BottomEdgeFillet=0,MidEdgeFillet=0,TopEdgeFillet=0),d);update_frame(obj,p)
 assert read_parameters(obj).TopEdgeFillet==3;export_package(obj,str(out));d.saveAs(str(out/'Fillet056.FCStd'));App.closeDocument(d.Name)
 assert list(out.rglob('*.dxf')) and list(out.rglob('*.svg'))
 checks.append('Loaded frame update, native save, LiPo pad, STEP and DXF/SVG profile export')
 report=dict(status='passed',checks=checks)
except Exception:report=dict(status='failed',checks=checks,error=traceback.format_exc());traceback.print_exc()
(out/'report.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
