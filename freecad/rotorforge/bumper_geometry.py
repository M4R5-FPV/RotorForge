"""Bottom-plate shoe built from the finished carbon silhouette."""
import FreeCAD as App,Part
from .front_bumper import toe_commands,shoulder_hull
from .shape_cleanup import guard_refine

def front_bumper(p,parts):
 if not p.FlexFrontBumper:return Part.Shape()
 from .protection_geometry import outer_face,offset_face
 from .parameters import plate_holes
 plate=parts['BottomPlate'];face=outer_face(plate)
 front=face.BoundBox.YMax;rear=front-p.FlexBumperReach;fit=p.FlexBumperFit;wall=p.FlexBumperWall
 outer=offset_face(face,fit+wall)
 outer=outer.common(Part.Face(Part.makePolygon([App.Vector(-1000,rear,0),App.Vector(1000,rear,0),App.Vector(1000,front+wall+p.FlexBumperProjection+fit+10,0),App.Vector(-1000,front+wall+p.FlexBumperProjection+fit+10,0),App.Vector(-1000,rear,0)])))
 half=max(abs(outer.BoundBox.XMin),abs(outer.BoundBox.XMax))
 if p.FlexBumperShape!='Follow bottom plate':
  half=p.FlexBumperWidth/2 if p.FlexBumperWidth else half
  points=[(v.x,v.y) for edge in outer.Edges for v in edge.discretize(Deflection=.025)]
  hull=shoulder_hull(points,half,front+fit+wall,front-wall)
  outer=Part.Face(Part.makePolygon([App.Vector(x,y,0) for x,y in hull+(hull[0],)]))
 commands=toe_commands(p.FlexBumperShape,half,front,fit+wall,p.FlexBumperProjection,p.FlexBumperTipWidth,p.FlexBumperRecess)
 if commands:
  edges=[];current=None
  for item in commands:
   if item[0]=='M':current=App.Vector(*item[1],0)
   elif item[0]=='L':
    end=App.Vector(*item[1],0)
    if (end-current).Length>1e-8:edges.append(Part.makeLine(current,end))
    current=end
   else:
    curve=Part.BezierCurve();curve.setPoles([current]+[App.Vector(*v,0) for v in item[1:]]);edges.append(curve.toShape());current=App.Vector(*item[-1],0)
  outer=guard_refine(outer.fuse(Part.Face(Part.Wire(edges))))
 low=-fit-p.FlexBumperSole;upper=p.BottomThickness+fit+p.FlexBumperLip
 body=outer.extrude(App.Vector(0,0,upper-low));body.translate(App.Vector(0,0,low))
 if len(body.Solids)>1:body=guard_refine(body.Solids[0].multiFuse(body.Solids[1:]))
 pocket=offset_face(face,fit).extrude(App.Vector(0,0,p.BottomThickness+2*fit));pocket.translate(App.Vector(0,0,-fit))
 opening=offset_face(face,-p.FlexBumperOverlap).extrude(App.Vector(0,0,p.FlexBumperLip+1));opening.translate(App.Vector(0,0,p.BottomThickness+fit))
 body=body.cut(pocket).cut(opening)
 if p.FlexBumperLipReach:
  limit=front-p.FlexBumperLipReach
  if limit>rear:
   body=body.cut(Part.makeBox(2000,limit-rear+1,p.FlexBumperLip+1,App.Vector(-1000,rear-1,p.BottomThickness+fit)))
 # Keep bolt-head access through the sole/lip; holes never change the carbon.
 tools=[Part.makeCylinder(max(3.,r)+fit,upper-low+2,App.Vector(*pt,low-1)) for pt,r,label in plate_holes(p,'BottomPlate')]
 if tools:body=body.cut(Part.makeCompound(tools))
 for role,shape in parts.items():
  if role=='BottomPlate' or shape.isNull():continue
  if role.startswith('CameraMount'):
   b=shape.BoundBox;tool=Part.makeBox(b.XLength+2*fit,b.YLength+2*fit,b.ZLength+2*fit,App.Vector(b.XMin-fit,b.YMin-fit,b.ZMin-fit))
  else:tool=shape
  if body.BoundBox.intersect(tool.BoundBox):body=body.cut(tool)
 body=guard_refine(body)
 if not body.isValid() or len(body.Solids)!=1 or body.Volume<=0:raise ValueError('Front bumper must remain one connected shoe. Adjust its reach/overlap or increase its wall and sole thickness.')
 return body
