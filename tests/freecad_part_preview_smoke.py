"""Compare inspection paths with finished native clamp/keystone profiles."""
import json,traceback,math,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import FreeCAD as App
from freecad.rotorforge.document import read_parameters
from freecad.rotorforge.geometry import build_shapes,carbon_roles,flat_plate_shape
from freecad.rotorforge.part_preview import part_path
from freecad.rotorforge.airflow_gui import QtGui
checks=[]
def area(path):
 b=path.boundingRect();sc=10;im=QtGui.QImage(math.ceil(b.width()*sc)+4,math.ceil(b.height()*sc)+4,QtGui.QImage.Format_Grayscale8);im.fill(0)
 painter=QtGui.QPainter(im);painter.scale(sc,sc);painter.translate(-b.left()+.2,-b.top()+.2);painter.fillPath(path,QtGui.QColor('white'));painter.end()
 return bytes(im.constBits()).count(255)/sc**2
try:
 for name in ('Example_CompactKeystone_3_plates.FCStd','Example_CompactKeystone_Below_2_plates.FCStd','Example_ClampKeystone_Above_2_plates.FCStd','Example_ClampKeystone_Below_2_plates.FCStd'):
  doc=App.openDocument(str((ROOT/'examples'/name).resolve()));settings=next(o for o in doc.Objects if 'Wheelbase' in o.PropertiesList);p=read_parameters(settings);shapes=build_shapes(p)
  for role in carbon_roles(p):
   flat=flat_plate_shape(shapes[role],role,p);expected=flat.Volume/flat.BoundBox.ZLength;actual=area(part_path(p,role,align=False))
   if abs(actual-expected)/expected>.025:raise AssertionError((name,role,actual,expected))
   checks.append((name,role))
  App.closeDocument(doc.Name)
 report={'status':'passed','checks':len(checks)}
except Exception:report={'status':'failed','checks':len(checks),'error':traceback.format_exc()}
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);(out/'report.json').write_text(json.dumps(report))
