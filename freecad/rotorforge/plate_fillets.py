"""Adaptive exact 2D corner fillets, including final cutout boundaries."""
import math
FIELDS={'BottomPlate':'BottomEdgeFillet','MidPlate':'MidEdgeFillet','TopPlate':'TopEdgeFillet','ArmClampPlate':'ClampEdgeFillet','ArmLowerClampPlate':'ClampEdgeFillet'}
FIELDS.update({name:'ArmEdgeFillet' for name in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight')})
def fillet_radius(p,role):return getattr(p,FIELDS[role]) if role in FIELDS else 0.

def fillet_openings(p,role):
 if role in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight'):return p.ArmFilletOpenings
 field={'BottomPlate':'BottomFilletOpenings','MidPlate':'MidFilletOpenings','TopPlate':'TopFilletOpenings','ArmClampPlate':'ClampFilletOpenings','ArmLowerClampPlate':'ClampFilletOpenings'}.get(role)
 return bool(field and getattr(p,field))

def _away(edge,point):
 if (edge.valueAt(edge.FirstParameter)-point).Length<1e-6:return edge.tangentAt(edge.FirstParameter)
 return -edge.tangentAt(edge.LastParameter)

def _corners(wire):
 points=[]
 for vertex in wire.Vertexes:
  point=vertex.Point;adj=[e for e in wire.Edges if any((v.Point-point).Length<1e-6 for v in e.Vertexes)]
  if len(adj)!=2:continue
  turn=math.acos(max(-1.,min(1.,-_away(adj[0],point).dot(_away(adj[1],point)))))
  if 1e-4<turn<math.pi-1e-4:points.append((point,.45*min(e.Length for e in adj)/max(1e-6,math.tan(turn/2))))
 return points

def _blend(first,second,point,radius):
 import FreeCAD as App
 import Part
 if isinstance(first.Curve,Part.Line) and isinstance(second.Curve,Part.Line):
  a=_away(first,point);b=_away(second,point);alpha=math.acos(max(-1.,min(1.,a.dot(b))))
  distance=radius/max(1e-12,math.tan(alpha/2));pa=point+a*distance;pb=point+b*distance
  bisector=a+b;bisector.normalize();centre=point+bisector*(radius/math.sin(alpha/2))
  toward=point-centre;toward.normalize();mid=centre+toward*radius
  oa=max([v.Point for v in first.Vertexes],key=lambda p:(p-point).Length)
  ob=max([v.Point for v in second.Vertexes],key=lambda p:(p-point).Length)
  return Part.Arc(pa,mid,pb).toShape(),Part.makeLine(oa,pa),Part.makeLine(pb,ob)
 # Analytic tangent-circle intersections also cover sharp junctions where
 # outline notches or overlapping cutouts meet existing circular edges.
 if all(isinstance(e.Curve,(Part.Line,Part.Circle)) for e in (first,second)):
  return _circular_blend(first,second,point,radius)
 api=Part.ChFi2d.FilletAlgo();api.init(first,second,Part.Plane())
 if not api.perform(radius):raise ValueError('radius does not fit')
 return api.result(point)

def _trim(edge,point,tangent):
 import Part
 if isinstance(edge.Curve,Part.Line):
  ends=[v.Point for v in edge.Vertexes];other=max(ends,key=lambda v:(v-point).Length)
  if (tangent-point).dot(other-point)<=1e-10 or (tangent-other).dot(point-other)<=1e-10:raise ValueError('outside line segment')
  return Part.makeLine(other,tangent)
 curve=edge.Curve;param=curve.parameter(tangent)
 candidates=[param+2*math.pi*k for k in range(-3,4)]
 valid=[v for v in candidates if edge.FirstParameter+1e-8<v<edge.LastParameter-1e-8]
 if not valid:raise ValueError('outside circular segment')
 param=min(valid,key=lambda v:(edge.valueAt(v)-tangent).Length)
 if (edge.valueAt(edge.FirstParameter)-point).Length<1e-5:return curve.toShape(param,edge.LastParameter)
 return curve.toShape(edge.FirstParameter,param)

def _circular_blend(first,second,point,r):
 import FreeCAD as App
 import Part
 def intersection_line_circle(origin,direction,centre,radius):
  delta=origin-centre;b=delta.dot(direction);q=b*b-delta.dot(delta)+radius*radius
  if q<-1e-9:return []
  return [origin+direction*(-b+sign*math.sqrt(max(0,q))) for sign in (-1,1)]
 def intersection_circles(a,ra,b,rb):
  delta=b-a;d=delta.Length
  if d<1e-9 or d>ra+rb+1e-8 or d<abs(ra-rb)-1e-8:return []
  unit=delta/d;along=(ra*ra-rb*rb+d*d)/(2*d);height=math.sqrt(max(0.,ra*ra-along*along));normal=App.Vector(-unit.y,unit.x,0)
  return [a+unit*along+normal*(sign*height) for sign in (-1,1)]
 edges=(first,second);centres=[]
 if any(isinstance(e.Curve,Part.Line) for e in edges):
  line=next(e for e in edges if isinstance(e.Curve,Part.Line));circle=next(e for e in edges if isinstance(e.Curve,Part.Circle));direction=_away(line,point);normal=App.Vector(-direction.y,direction.x,0)
  for side in (-1,1):
   for rad in (circle.Curve.Radius+r,abs(circle.Curve.Radius-r)):
    centres+=intersection_line_circle(point+normal*(side*r),direction,circle.Curve.Center,rad)
 else:
  for ra in (first.Curve.Radius+r,abs(first.Curve.Radius-r)):
   for rb in (second.Curve.Radius+r,abs(second.Curve.Radius-r)):
    centres+=intersection_circles(first.Curve.Center,ra,second.Curve.Center,rb)
 candidates=[]
 for centre in centres:
  try:
   contacts=[]
   for edge in edges:
    if isinstance(edge.Curve,Part.Line):
     direction=_away(edge,point);contact=point+direction*((centre-point).dot(direction))
    else:
     direction=centre-edge.Curve.Center;direction.normalize();contact=edge.Curve.Center+direction*edge.Curve.Radius
    contacts.append(contact)
   a,b=contacts;va=a-centre;vb=b-centre;middle=va+vb
   if middle.Length<1e-8:continue
   middle.normalize();mid=centre+middle*r
   arc=Part.Arc(a,mid,b).toShape();ea=_trim(first,point,a);eb=_trim(second,point,b)
   score=(a-point).Length+(b-point).Length
   candidates.append((score,arc,ea,eb))
  except Exception:continue
 if not candidates:raise ValueError('no local tangent solution')
 return min(candidates,key=lambda i:i[0])[1:]

def _face(wires):
 import Part
 return Part.makeFace(wires,'Part::FaceMakerBullseye')

def apply_plate_fillet(p,role,shape):
 requested=fillet_radius(p,role)
 if not requested:return shape
 import FreeCAD as App
 import Part
 from .parameters import plate_holes
 cap=max((f for f in shape.Faces if f.BoundBox.ZLength<1e-5 and abs(f.BoundBox.ZMin-shape.BoundBox.ZMax)<1e-5),key=lambda f:f.Area).copy()
 cap_z=cap.CenterOfMass.z;cap.translate(App.Vector(0,0,-cap_z))
 wires=[cap.OuterWire]+[w for w in cap.Wires if not w.isSame(cap.OuterWire)]
 original=_face(wires);working=original;protected=None;arm=None;root_limit=None
 holes=plate_holes(p,role)
 if role in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight'):
  from .parameters import arm_layouts
  arm=next(a for a in arm_layouts(p) if 'Arm'+a['name']==role)
  from .arm_roots import fillet_root_limit,arm_local_point
  root_limit=fillet_root_limit(p,arm)
  vertices=[App.Vector(*arm_local_point(arm,t,a),0) for t,a in ((-10000,-10000),(root_limit,-10000),(root_limit,10000),(-10000,10000))]
  protected=Part.Face(Part.makePolygon(vertices+[vertices[0]]))
  holes=[(pt,p.RootHoleDiameter/2,'root') for pt in arm['bolts']]+[(pt,p.MotorHoleDiameter/2,'motor') for pt in arm['motor_holes']]+[(arm['motor'],p.MotorCenterDiameter/2,'shaft')]
 disks=[Part.Face(Part.Wire(Part.makeCircle(r+p.MinimumWeb,App.Vector(*pt,0)))) for pt,r,_ in holes]
 gaps={(a,b):min(p.MinimumWeb,wires[a].distToShape(wires[b])[0]) for a in range(len(wires)) for b in range(a+1,len(wires))}
 adapted=[];retained=0;done=0
 for index in (range(len(wires)) if fillet_openings(p,role) else (0,)):
  for point,limit in _corners(wires[index]):
   if arm and (point.x-arm['root'][0])*arm['unit'][0]+(point.y-arm['root'][1])*arm['unit'][1]<=root_limit+1e-6:continue
   edges=list(wires[index].Edges);adj=[e for e in edges if any((v.Point-point).Length<1e-6 for v in e.Vertexes)]
   if len(adj)!=2:continue
   radius=min(requested,limit);accepted=False
   for attempt in range(14):
    if radius<1e-4:break
    try:
     arc,first,second=_blend(adj[0],adj[1],point,radius)
     rest=[e for e in edges if not any(e.isSame(a) for a in adj)]
     candidate=Part.Wire(Part.__sortEdges__(rest+[first,arc,second]))
     if not candidate.isClosed() or not candidate.isValid():raise ValueError('wire closure')
     trial=wires[:];trial[index]=candidate;face=_face(trial)
     if len(face.Faces)!=1 or len(face.Wires)!=len(wires) or not face.isValid():raise ValueError('face connectivity')
     for j,other in enumerate(wires):
      if j!=index and candidate.distToShape(other)[0]<gaps[min(index,j),max(index,j)]-1e-5:raise ValueError('minimum web')
     if protected is not None and (working.cut(face).common(protected).Area>1e-7 or face.cut(working).common(protected).Area>1e-7):raise ValueError('Root mounting stock must remain unchanged')
     removed=working.cut(face)
     if removed.Area>1e-8:
      for disk in disks:
       if removed.BoundBox.intersect(disk.BoundBox) and removed.common(disk).Area>1e-7:raise ValueError('fastener support')
     wires=trial;working=face;accepted=True;done+=1
     if radius<requested-1e-4:adapted.append(radius)
     break
    except Exception:
     radius*=.5
   if not accepted:retained+=1
 result=shape
 for change,adding in ((original.cut(working),False),(working.cut(original),True)):
  if change.isNull() or change.Area<1e-8:continue
  change.translate(App.Vector(0,0,shape.BoundBox.ZMin));stock=change.extrude(App.Vector(0,0,shape.BoundBox.ZLength))
  result=result.fuse(stock) if adding else result.cut(stock)
 result=result.removeSplitter()
 if not result.isValid() or len(result.Solids)!=1:raise ValueError(role+': local fillets could not preserve a connected plate; review the source outline.')
 if adapted or retained:
  detail=(f'; minimum local radius {min(adapted):.3g} mm' if adapted else '')+(f'; {retained} constrained corners retained' if retained else '')
  App.Console.PrintMessage(f'{role}: {done} corners filleted; requested {requested:g} mm'+detail+'\n')
 return result

def preview_fillet(p,role,path):
 """Lightweight target-radius preview on outside and internal cutout loops."""
 radius=fillet_radius(p,role)
 if not radius:return path
 arm=None
 if role in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight'):
  from .parameters import arm_layouts
  from .arm_roots import fillet_root_limit
  arm=next(a for a in arm_layouts(p) if 'Arm'+a['name']==role);root_limit=fillet_root_limit(p,arm)
 from .airflow_gui import QtCore,QtGui
 transform=QtGui.QTransform();transform.scale(100,100)
 result=QtGui.QPainterPath();result.setFillRule(QtCore.Qt.OddEvenFill)
 loops=path.toSubpathPolygons(transform)
 def area(poly):return abs(sum(a.x()*b.y()-b.x()*a.y() for a,b in zip(poly,list(poly)[1:]+[poly[0]])))
 outer=max(loops,key=area) if loops else None
 for loop in loops:
  if not fillet_openings(p,role) and loop!=outer:
   q=QtGui.QPainterPath();q.addPolygon(loop);q.closeSubpath();result.addPath(transform.inverted()[0].map(q));continue
  points=[(v.x()/100,v.y()/100) for v in loop]
  if len(points)>1 and math.dist(points[0],points[-1])<1e-8:points.pop()
  if len(points)<3:continue
  corners=[]
  for a,b,c in zip(points[-1:]+points[:-1],points,points[1:]+points[:1]):
   if arm and (b[0]-arm['root'][0])*arm['unit'][0]+(b[1]-arm['root'][1])*arm['unit'][1]<=root_limit+1e-6:corners.append((b,b,b,b));continue
   la=math.dist(a,b);lb=math.dist(b,c)
   if min(la,lb)<1e-8:corners.append((b,b,b,b));continue
   u=((b[0]-a[0])/la,(b[1]-a[1])/la);v=((c[0]-b[0])/lb,(c[1]-b[1])/lb)
   angle=math.acos(max(-1,min(1,u[0]*v[0]+u[1]*v[1])))
   distance=min(radius*math.tan(angle/2),la*.45,lb*.45) if .25<angle<math.pi-.01 else 0.
   if arm:
    along=(b[0]-arm['root'][0])*arm['unit'][0]+(b[1]-arm['root'][1])*arm['unit'][1]
    for dx,dy in ((-u[0],-u[1]),v):
     rate=dx*arm['unit'][0]+dy*arm['unit'][1]
     if rate<0:distance=min(distance,max(0.,(along-root_limit)/-rate))
   r=distance/max(1e-12,math.tan(angle/2));k=4/3*math.tan(angle/4)*r
   start=(b[0]-u[0]*distance,b[1]-u[1]*distance);end=(b[0]+v[0]*distance,b[1]+v[1]*distance)
   corners.append((start,(start[0]+u[0]*k,start[1]+u[1]*k),(end[0]-v[0]*k,end[1]-v[1]*k),end))
  q=QtGui.QPainterPath();q.moveTo(*corners[0][0])
  for start,a,b,end in corners:q.lineTo(*start);q.cubicTo(*a,*b,*end)
  q.closeSubpath();result.addPath(q)
 return result
