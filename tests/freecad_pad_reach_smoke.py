"""Native stack-anchored pad reaches, straight ends and standoff access."""
import sys,os,json,traceback,math
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,standoff_layouts
from freecad.rotorforge.geometry import build_shapes,cylinder
from freecad.rotorforge.battery import pad_standoff_clearance
from freecad.rotorforge.part_preview import pad_path
from freecad.rotorforge.airflow_gui import QtGui
from freecad.rotorforge.document import create_frame,read_parameters
from freecad.rotorforge.exporters import export_package
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[]
def check(ok,msg):
 if not ok:raise AssertionError(msg)
 checks.append(msg)
def area(path):
 b=path.boundingRect();sc=12;im=QtGui.QImage(math.ceil(b.width()*sc)+4,math.ceil(b.height()*sc)+4,QtGui.QImage.Format_Grayscale8);im.fill(0)
 painter=QtGui.QPainter(im);painter.scale(sc,sc);painter.translate(-b.left()+.2,-b.top()+.2);painter.fillPath(path,QtGui.QColor('white'));painter.end();return bytes(im.constBits()).count(255)/sc**2
try:
 cases=[Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline',PlateDesign='2 plates',StackOffsetY=7,LiPoPadFrontReach=25,LiPoPadRearReach=35),
 Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline',PlateDesign='2 plates',StackOffsetY=7,LiPoPadFrontReach=18,LiPoPadRearReach=35,LiPoPadOutlineWidthScale=75),
 Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline',LiPoPadFrontReach=30,LiPoPadRearReach=25,BatteryMount='Bottom plate'),
 Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline',StandoffCount='6 (3 pairs)'),
 Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline',StandoffCount='8 (4 pairs)'),
 Parameters(LiPoPadEnabled=True,LiPoPadShape='Capsule',LiPoPadFollowPlate=False),
 Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline',LiPoPadRearReach=24)]
 results=[]
 for i,p in enumerate(cases):
  shapes=build_shapes(p);pad=shapes['LiPoPad'];b=pad.optimalBoundingBox(False);tag=str(i)
  check(pad.isValid() and len(pad.Solids)==1,tag+' connected')
  for stand in standoff_layouts(p):
   tool=cylinder(*stand['point'],6-1e-5,b.ZMin-1,b.ZLength+2)
   check(pad.common(tool).Volume<1e-6,tag+' 6mm standoff centre clearance '+str(stand['point']))
  q=pad_path(p);check(abs(area(q)-pad.Volume/p.LiPoPadThickness)/(pad.Volume/p.LiPoPadThickness)<.025,tag+' Qt/CAD area')
  if i in (0,1,2):
   for y,name in ((p.StackOffsetY+p.LiPoPadFrontReach,'front'),(p.StackOffsetY-p.LiPoPadRearReach,'rear')):
    check(abs((b.YMax if name=='front' else b.YMin)-y)<1e-6,tag+' stack-anchored '+name)
    check(any(e.Length>5 and abs(e.BoundBox.YMin-y)<1e-6 and abs(e.BoundBox.YMax-y)<1e-6 and e.Curve.__class__.__name__ in ('Line','LineSegment') for e in pad.Edges),tag+' straight '+name+' cut')
  results.append((b.XLength,b.YMin,b.YMax))
 check(abs(results[0][1]-results[1][1])<1e-6,'front adjustment leaves rear fixed')
 check(results[1][0]<results[0][0],'width adjustment changes width')
 settings=create_frame(cases[1],App.newDocument('PadReach'));filename=out/'reach.FCStd';settings.Document.saveAs(str(filename.resolve()));App.closeDocument(settings.Document.Name)
 doc=App.openDocument(str(filename.resolve()));settings=next(o for o in doc.Objects if 'Wheelbase' in o.PropertiesList);check(read_parameters(settings)==cases[1],'native save/reopen')
 folder=export_package(settings,out);check((folder/'LiPoPad/LiPoPad.stl').is_file(),'STL export');check((folder/'LiPoPad/LiPoPad_outline.svg').is_file(),'SVG export')
 metrics=json.loads((folder/'MassProperties.json').read_text());check(abs(metrics['pad_mass_g']-build_shapes(cases[1])['LiPoPad'].Volume*cases[1].LiPoPadDensity/1000)<1e-8,'export mass uses clearance and reaches');App.closeDocument(doc.Name)
 report={'status':'passed','checks':checks}
except Exception:report={'status':'failed','checks':checks,'error':traceback.format_exc()}
(out/'report.json').write_text(json.dumps(report,indent=2))
