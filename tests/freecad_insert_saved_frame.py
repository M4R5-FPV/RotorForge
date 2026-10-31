"""Check all insert lip faces against a saved frame's actual carbon plates."""
import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,MeshPart
from freecad.rotorforge.document import read_parameters,component_objects
from freecad.rotorforge.flex_geometry import camera_pads,printable_flex
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT'])
doc=App.openDocument(os.environ['ROTORFORGE_SAVED_FRAME']);frame=doc.getObject('FrameParameters');p=read_parameters(frame);carbon=component_objects(frame);checks=[]
for mode in ('Both sides','Outside only','Inside only'):
 q=replace(p,FlexInsertLipSide=mode);shapes=camera_pads(q)
 for role,shape in shapes.items():
  assert shape.isValid() and len(shape.Solids)==1
  counterpart='CameraMountLeft' if role.endswith('Left') else 'CameraMountRight'
  assert shape.common(carbon[counterpart].Shape).Volume<1e-6
  mesh=MeshPart.meshFromShape(Shape=printable_flex(shape,role),LinearDeflection=.08,AngularDeflection=.2,Relative=False)
  assert mesh.isSolid(),mode+' '+role+' print mesh is not closed'
 checks.append(mode+' fits sloped carbon window and prints as closed meshes')
(out/'saved_insert_faces.json').write_text(json.dumps(dict(checks=checks),indent=2))
App.closeDocument(doc.Name)
