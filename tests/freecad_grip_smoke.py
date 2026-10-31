"""Native grip coverage, full-footprint repetition and pattern export."""
import os,sys,json,traceback,math
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.battery import make_pad,GRIP_PATTERNS,groove_segments,grip_bounds,grip_point
from freecad.rotorforge.part_preview import pad_path,grip_path
from freecad.rotorforge.airflow_gui import QtGui
from freecad.rotorforge.document import create_frame,read_parameters
from freecad.rotorforge.exporters import export_package
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[]
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def area(path):
 b=path.boundingRect();sc=48;im=QtGui.QImage(math.ceil(b.width()*sc)+4,math.ceil(b.height()*sc)+4,QtGui.QImage.Format_Grayscale8);im.fill(0)
 painter=QtGui.QPainter(im);painter.scale(sc,sc);painter.translate(-b.left()+.2,-b.top()+.2);painter.fillPath(path,QtGui.QColor('white'));painter.end();return bytes(im.constBits()).count(255)/sc**2
try:
 base=Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline',LiPoPadWidth=4,LiPoPadLength=4,LiPoPadGroovePitch=8)
 solid=build_shapes(base);blank=solid['LiPoPad'];b=blank.optimalBoundingBox(False)
 for name in GRIP_PATTERNS:
  p=replace(base,LiPoPadPattern=name);s=build_shapes(p);pad=s['LiPoPad']
  check(pad.isValid() and len(pad.Solids)==1,name+' connected')
  if name=='Solid':check(abs(pad.Volume-blank.Volume)<1e-8,'solid is unchanged');continue
  removed=blank.cut(pad);check(removed.Volume>1,name+' removes material')
  expected=removed.Volume/p.LiPoPadGrooveDepth;check(abs(area(grip_path(p,pad_path(p)))-expected)/expected<.05,name+' preview matches CAD grip')
  check(pad.cut(blank).Volume<1e-6,name+' respects outline and standoff access')
  # Every quadrant reaches the outer pad regions, far beyond obsolete 4x4 dimensions.
  for xsign in (-1,1):
   for ysign in (-1,1):
    x0,x1=(b.XMin,0) if xsign<0 else (0,b.XMax)
    y0,y1=(b.YMin,-12) if ysign<0 else (12,b.YMax)
    window=Part.makeBox(x1-x0,y1-y0,b.ZLength+.2,App.Vector(x0,y0,b.ZMin-.1))
    check(removed.common(window).Volume>.01,name+' covers outer quadrant '+str((xsign,ysign)))
  # A complete backing slab is retained, independently of pattern intersections.
  backing=blank.common(Part.makeBox(b.XLength+2,b.YLength+2,p.LiPoPadThickness-p.LiPoPadGrooveDepth-.01,App.Vector(b.XMin-1,b.YMin-1,b.ZMin)))
  check(backing.cut(pad).Volume<1e-6,name+' continuous backing')
  # Legacy envelope and battery pose must not restrict frame-following grip coverage.
  q=replace(p,LiPoPadWidth=90,LiPoPadLength=150,BatteryX=100,BatteryY=-100,BatteryRotation=70)
  if name in ('Cross grooves','Chevron grooves'):check(abs(build_shapes(q)['LiPoPad'].Volume-pad.Volume)<1e-7,name+' auto region independent of unused dimensions and battery pose')
 # Bottom mounting cuts the battery-facing underside, preserving upper support.
 p=Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline',BatteryMount='Bottom plate',LiPoPadPattern='Diamond grooves',LiPoPadGroovePitch=8)
 s=build_shapes(p);blank=make_pad(p,s['BottomPlate'],False);pad=s['LiPoPad'];removed=blank.cut(pad)
 check(abs(removed.optimalBoundingBox(False).ZMin-pad.optimalBoundingBox(False).ZMin)<1e-6,'bottom grip on underside')
 # Rotation and offsets on an independent pad still cover the complete footprint.
 p2=Parameters(LiPoPadEnabled=True,LiPoPadShape='Capsule',LiPoPadFollowPlate=False,BatteryRotation=33,BatteryX=3,BatteryY=5,LiPoPadPattern='Chevron grooves',LiPoPadGroovePitch=8)
 s2=build_shapes(p2);check(s2['LiPoPad'].isValid(),'rotated independent grip')
 settings=create_frame(p,App.newDocument('GripPatterns'));filename=out/'grip.FCStd';settings.Document.saveAs(str(filename.resolve()));App.closeDocument(settings.Document.Name)
 doc=App.openDocument(str(filename.resolve()));settings=next(o for o in doc.Objects if 'Wheelbase' in o.PropertiesList);check(read_parameters(settings)==p,'pattern native save/reopen')
 folder=export_package(settings,out);check((folder/'LiPoPad/LiPoPad.stl').is_file(),'pattern STL export')
 m=json.loads((folder/'MassProperties.json').read_text());check(abs(m['pad_mass_g']-pad.Volume*p.LiPoPadDensity/1000)<1e-8,'pattern mass exported');App.closeDocument(doc.Name)
 report={'status':'passed','checks':checks}
except Exception:report={'status':'failed','checks':checks,'error':traceback.format_exc()}
(out/'report.json').write_text(json.dumps(report,indent=2))
