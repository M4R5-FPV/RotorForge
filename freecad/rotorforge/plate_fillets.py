"""Exact 2D corner fillets plus the selected CNC inside-corner rule."""

# A 1 mm end mill cannot enter a re-entrant radius smaller than 0.5 mm.
# Convex outside corners can be sharp; they do not need a mandatory roundover.
MIN_CNC_RADIUS_MM = 0.5
CNC_CORNER_ANGLE_RAD = 0.017453292519943295  # 1 degree; ignore tangent/CAD seam noise

import math
FIELDS={'BottomPlate':'BottomEdgeFillet','MidPlate':'MidEdgeFillet','TopPlate':'TopEdgeFillet','ArmClampPlate':'ClampEdgeFillet','ArmLowerClampPlate':'ClampEdgeFillet'}
FIELDS.update({name:'ArmEdgeFillet' for name in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight')})
def fillet_radius(p,role):
 if role in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight'):
  return max(p.ArmEdgeFillet,p.ArmRootFillet)
 return getattr(p,FIELDS[role]) if role in FIELDS else 0.


def _arm_corner_radius(p,arm,xy,root_limit):
    """Root corners and beam corners use independent user-selected radii."""
    along=((xy[0]-arm['root'][0])*arm['unit'][0]
           +(xy[1]-arm['root'][1])*arm['unit'][1])
    return p.ArmRootFillet if along<=root_limit+1e-6 else p.ArmEdgeFillet

def fillet_openings(p,role):
 if role in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight'):return p.ArmFilletOpenings
 field={'BottomPlate':'BottomFilletOpenings','MidPlate':'MidFilletOpenings','TopPlate':'TopFilletOpenings','ArmClampPlate':'ClampFilletOpenings','ArmLowerClampPlate':'ClampFilletOpenings'}.get(role)
 return bool(field and getattr(p,field))

def _away(edge,point):
 if (edge.valueAt(edge.FirstParameter)-point).Length<1e-6:return edge.tangentAt(edge.FirstParameter)
 return -edge.tangentAt(edge.LastParameter)

def _corners(wire):
 points=[]
 # Cache native edge/vertex wrappers once per immutable wire. Preserve the
 # existing point tolerance and ordering (including closed analytic edges).
 edges=[(e,tuple(v.Point for v in e.Vertexes)) for e in wire.Edges]
 for vertex in wire.Vertexes:
  point=vertex.Point;adj=[e for e,ends in edges if any((v-point).Length<1e-6 for v in ends)]
  if len(adj)!=2:continue
  turn=math.acos(max(-1.,min(1.,-_away(adj[0],point).dot(_away(adj[1],point)))))
  if 1e-4<turn<math.pi-1e-4:points.append((point,.45*min(e.Length for e in adj)/max(1e-6,math.tan(turn/2))))
 return points

def _is_air_wedge(face,point,first,second):
    """True when the wedge between edges lies in air rather than carbon.

    Works for an outside notch AND for the inner contour of a cutout. Checking
    actual face occupancy avoids reliance on OCCT wire ordering/orientation.
    """
    import FreeCAD as App
    a=_away(first,point);b=_away(second,point)
    bisector=a+b
    if bisector.Length<1e-8:return False
    bisector.normalize()
    reach=min(first.Length,second.Length)
    offset=min(0.025,reach*0.12)
    if offset<1e-6:return False
    # Keep the actual Z plane of the face. The working sketch is at Z=0,
    # but final cap faces are at Z=arm thickness / plate top. Sampling Z=0
    # incorrectly classified every outside corner as a concave milling
    # corner and made perfectly cuttable profiles fail the final check.
    sample=point+bisector*offset
    return not face.isInside(sample,1e-7,True)


def _is_machining_corner(face,point,first,second):
    """Detect a genuine sharp concave corner, not a tangent arc seam."""
    a=_away(first,point);b=_away(second,point)
    turn=math.acos(max(-1.,min(1.,-a.dot(b))))
    return CNC_CORNER_ANGLE_RAD<turn<math.pi-CNC_CORNER_ANGLE_RAD and _is_air_wedge(face,point,first,second)


def _unmachinable_corners(face):
    """Return sharp re-entrant vertices still needing a milling fillet."""
    bad=[]
    for wire in face.Wires:
        for point,_ in _corners(wire):
            edges=[e for e in wire.Edges if any((v.Point-point).Length<1e-6 for v in e.Vertexes)]
            if len(edges)==2 and _is_machining_corner(face,point,*edges):
                bad.append((point.x,point.y))
    return bad


def _unmachinable_arcs(face, minimum=MIN_CNC_RADIUS_MM):
    """Find pre-existing concave analytic arcs too tight for a 1 mm cutter."""
    import FreeCAD as App
    import Part
    bad=[]
    for wire in face.Wires:
        for edge in wire.Edges:
            curve=edge.Curve
            if not isinstance(curve,Part.Circle) or curve.Radius>=minimum-1e-5:
                continue
            # Full circular bores are separate drill operations; never resize them.
            if minimum>MIN_CNC_RADIUS_MM and abs(edge.Length-2*math.pi*curve.Radius)<1e-5 and curve.Radius>=MIN_CNC_RADIUS_MM-1e-5:continue
            halfway=edge.valueAt((edge.FirstParameter+edge.LastParameter)/2)
            direction=curve.Center-halfway
            if direction.Length<1e-7:continue
            direction.normalize()
            # Material on the OUTSIDE of this circle means the cutter needs
            # to fit into the circular pocket, scallop or interior relief.
            point=halfway+direction*min(0.02,curve.Radius*0.1)
            if not face.isInside(point,1e-7,True):
                bad.append((halfway.x,halfway.y,curve.Radius))
    return bad


def _validate_cnc_inside_radii(face,role,minimum=MIN_CNC_RADIUS_MM):
    corners=_unmachinable_corners(face)
    arcs=_unmachinable_arcs(face,minimum)
    if corners or arcs:
        x,y=(corners[0] if corners else arcs[0][:2])
        raise ValueError(f'{role}: {2*minimum:g} mm CNC cutter cannot reach an internal corner at '
                         f'X {x:.2f} / Y {y:.2f} mm (minimum R{minimum:g} mm). '
                         'Automatic CNC smoothing cannot safely reach this location without changing a protected mounting or fitted joint. '
                         'Review the final outline near the reported coordinates.')


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

def _linear_fillet_bounds(point, adj, arc, first, second):
 """Conservative local edit bounds for verified straight-edge fillets only.
 The changed region is enclosed by the two old corner-to-contact segments
 and the replacement arc. Other curve types retain the old full-face tests.
 """
 import Part
 from .geometry_bounds import EnclosingBox
 if not all(isinstance(e.Curve,Part.Line) for e in adj):return None
 try:
  contacts=[v.Point for v in arc.Vertexes]
  if len(contacts)!=2:return None
  for old,new in zip(adj,(first,second)):
   ends=[v.Point for v in old.Vertexes];trim=[v.Point for v in new.Vertexes]
   if len(ends)!=2 or len(trim)!=2:return None
   if min((v-point).Length for v in ends)>1e-7:return None
   far=max(ends,key=lambda v:(v-point).Length);direction=far-point
   if direction.Length<1e-7:return None
   if min((v-far).Length for v in trim)>1e-7:return None
   contact=max(trim,key=lambda v:(v-far).Length)
   if min((v-contact).Length for v in contacts)>1e-7:return None
   t=(contact-point).dot(direction)/direction.dot(direction)
   if not 0.<t<1. or (contact-point-direction*t).Length>1e-7:return None
  return EnclosingBox((arc.BoundBox,),[point,*contacts])
 except (ValueError,TypeError,AttributeError,RuntimeError,ZeroDivisionError):return None


def _face(wires):
 import Part
 return Part.makeFace(wires,'Part::FaceMakerBullseye')

def _arm_root_corner_can_fillet(p, arm, point, root_limit):
    """Fitted-miter roots may be rounded; independent roots stay protected.

    Previously the entire mounting root was excluded, even its exposed outer
    corners between adjacent arms. CAD's bolt-stock and joint-cell checks
    provide the finer protection needed on fitted joints.
    """
    from .arm_roots import fitted_roots
    if fitted_roots(p):
        return True
    if p.ArmRootFillet>0:
        return True
    along=((point.x-arm['root'][0])*arm['unit'][0]
           +(point.y-arm['root'][1])*arm['unit'][1])
    return along > root_limit+1e-6


def _arm_root_corner_can_fillet_xy(p, arm, xy, root_limit):
    """Same eligibility for the Qt preview without importing FreeCAD."""
    from .arm_roots import fitted_roots
    if fitted_roots(p):
        return True
    if p.ArmRootFillet>0:
        return True
    along=((xy[0]-arm['root'][0])*arm['unit'][0]
           +(xy[1]-arm['root'][1])*arm['unit'][1])
    return along > root_limit+1e-6


def apply_plate_fillet(p,role,shape):
 # Camera side plates lie vertically in YZ and have a separate machining
 # workflow. The planar XY cutter rule applies to horizontal frame carbon.
 if role not in FIELDS:return shape
 minimum=p.CNCToolRadius
 requested=fillet_radius(p,role)
 # Even zero aesthetic fillet settings must protect concave cutter corners.
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
  from .arm_roots import fillet_root_limit,arm_local_point,fitted_roots,root_cell_polygon
  root_limit=fillet_root_limit(p,arm)
  if fitted_roots(p):
   # The exposed central arm-root corners can be rounded, but any added
   # stock must stay inside this arm's miter cell. Otherwise two neighboring
   # arms would overlap after filleting their shared joint.
   cell_points=root_cell_polygon(p,arm,arm_layouts(p))
   poly=[App.Vector(x,y,0) for x,y in cell_points]
   joint_cell=Part.Face(Part.makePolygon(poly+[poly[0]]))
  elif p.ArmRootFillet<=0:
   # With no separate root fillet, preserve independent roots exactly.
   vertices=[App.Vector(*arm_local_point(arm,t,a),0) for t,a in ((-10000,-10000),(root_limit,-10000),(root_limit,10000),(-10000,10000))]
   protected=Part.Face(Part.makePolygon(vertices+[vertices[0]]))
  holes=[(pt,p.RootHoleDiameter/2,'root') for pt in arm['bolts']]+[(pt,p.MotorHoleDiameter/2,'motor') for pt in arm['motor_holes']]+[(arm['motor'],p.MotorCenterDiameter/2,'shaft')]
 disks=[Part.Face(Part.Wire(Part.makeCircle(r+p.MinimumWeb,App.Vector(*pt,0)))) for pt,r,_ in holes]
 if arm:
  # Preserve the *user-selected additional arm-bolt stock*, not just the
  # minimum M3 web. This does not add material, only protects existing stock.
  from .mount_support import arm_bolt_stock_radius
  from .parameters import standoff_holes,three_plate,arms_above_bottom,upper_clamp_active
  arm_top_bearing=(not three_plate(p) and arms_above_bottom(p) and not upper_clamp_active(p))
  for pt in arm['bolts']:
   shared=arm_top_bearing and any(math.dist(pt,stand)<1e-6 for stand in standoff_holes(p))
   radius=arm_bolt_stock_radius(p,shared)
   disks.append(Part.Face(Part.Wire(Part.makeCircle(radius,App.Vector(*pt,0)))))
 # Preserve complete press-in flange / counterbore bearing footprints even
 # when a user also enables general outside-edge fillets.
 from .nut_seats import seats
 for seat in seats(p,role):
  if seat['mode']=='M3 press nut':
   from .mount_support import press_nut_stock_radius
   radius=press_nut_stock_radius(p,seat['depth'])
   disks.append(Part.Face(Part.Wire(Part.makeCircle(radius,App.Vector(*seat['point'],0)))))
 # TPU cage M3 openings are cut by camera_slots(), not plate_holes().
 # Protect their required carbon rim from later outside-edge fillets as well.
 from .tpu_mount_layout import carbon_rim_centres
 for point,radius in carbon_rim_centres(p,role):
  disks.append(Part.Face(Part.Wire(Part.makeCircle(radius,App.Vector(*point,0)))))
 # The old pre-fillet patch workaround is retired: first apply only valid
 # local corner fillets, then repair unresolved joints on the FINAL profile.
 # This prevents the two independent repair stages from overbuilding bumps.
 # The original gap is measured on the initial wires, never an already
 # modified contour. A conservative bounding-box lower bound can prove
 # a pair meets the capped gap without calling OCC's exact distance solver.
 from .geometry_bounds import box_distance
 initial_wires=tuple(wires);initial_boxes=tuple(w.BoundBox for w in wires)
 current_boxes=list(initial_boxes);gaps={}
 def original_gap(i,j):
  key=(min(i,j),max(i,j))
  if key not in gaps:
   a,b=key
   gaps[key]=(p.MinimumWeb if box_distance(initial_boxes[a],initial_boxes[b])>=p.MinimumWeb+1e-6
              else min(p.MinimumWeb,initial_wires[a].distToShape(initial_wires[b])[0]))
  return gaps[key]
 disk_boxes=[(disk,disk.BoundBox) for disk in disks]
 adapted=[];retained=0;done=0
 for index in range(len(wires)):
  for point,limit in _corners(wires[index]):
   edges=list(wires[index].Edges);adj=[e for e in edges if any((v.Point-point).Length<1e-6 for v in e.Vertexes)]
   if len(adj)!=2:continue
   compulsory=_is_machining_corner(working,point,*adj)
   normal_allowed=(index==0 or fillet_openings(p,role))
   root_allowed=(not arm or _arm_root_corner_can_fillet(p,arm,point,root_limit))
   # The separate aesthetic controls can still be zero; on those parts only
   # the cutter-driven concave corners get rounded.
   optional=normal_allowed and root_allowed
   user_radius=(_arm_corner_radius(p,arm,(point.x,point.y),root_limit)
                if arm else requested)
   if not compulsory and (not optional or user_radius<=1e-9):continue
   floor_radius=minimum if compulsory else MIN_CNC_RADIUS_MM
   corner_requested=max(floor_radius,user_radius) if (compulsory or optional) else 0.
   if corner_requested<=0:continue
   if compulsory and limit<minimum-1e-5:
    # Do not abort a whole frame over a short segment. The final rolling
    # cutter resolves the complete neighboring chain as one rounded notch.
    continue
   radius=min(corner_requested,limit);accepted=False
   for attempt in range(14):
    if radius<floor_radius-1e-5:break
    try:
     arc,first,second=_blend(adj[0],adj[1],point,radius)
     rest=[e for e in edges if not any(e.isSame(a) for a in adj)]
     candidate=Part.Wire(Part.__sortEdges__(rest+[first,arc,second]))
     if not candidate.isClosed() or not candidate.isValid():raise ValueError('wire closure')
     trial=wires[:];trial[index]=candidate;face=_face(trial)
     if len(face.Faces)!=1 or len(face.Wires)!=len(wires) or not face.isValid():raise ValueError('face connectivity')
     candidate_box=candidate.BoundBox
     local_box=_linear_fillet_bounds(point,adj,arc,first,second)
     for j,other in enumerate(wires):
      if j==index or box_distance(candidate_box,current_boxes[j])>=p.MinimumWeb+1e-6:continue
      # All unchanged edges already met the original capped gap; a new
      # linear fillet remote from the other wire cannot reduce that gap.
      if local_box is not None and box_distance(local_box,current_boxes[j])>=p.MinimumWeb+1e-5:continue
      if candidate.distToShape(other)[0]<original_gap(index,j)-1e-5:raise ValueError('minimum web')
     if protected is not None and (working.cut(face).common(protected).Area>1e-7 or (not compulsory and face.cut(working).common(protected).Area>1e-7)):raise ValueError('Root mounting stock must remain unchanged')
     if arm and fitted_roots(p):
      added=face.cut(working)
      if added.Area>1e-8 and added.cut(joint_cell).Area>1e-7:raise ValueError('Arm fillet must remain in its own fitted joint cell')
     # For an inner wire only, any stock removal is contained within its
     # old/new enclosed regions. If BOTH enclosing boxes have a strict gap
     # to every bearing disk, the stock-support test is vacuous. Outer
     # contours and uncertain pairs still run the original exact Boolean.
     need_support_check=(index==0 or any(min(box_distance(current_boxes[index],disk_box),
                                            box_distance(candidate_box,disk_box))<=1e-6
                                        for disk,disk_box in disk_boxes))
     if need_support_check and local_box is not None:
      need_support_check=any(box_distance(local_box,disk_box)<=1e-5 for disk,disk_box in disk_boxes)
     if need_support_check:
      removed=working.cut(face)
      if removed.Area>1e-8:
       removed_box=removed.BoundBox
       for disk,disk_box in disk_boxes:
        if removed_box.intersect(disk_box) and removed.common(disk).Area>1e-7:raise ValueError('fastener support')
     wires=trial;current_boxes[index]=candidate_box;working=face;accepted=True;done+=1
     if radius<corner_requested-1e-4:adapted.append(radius)
     break
    except Exception:
     # Retry an oversized requested fillet down to the selected tool floor;
     # the cutter-required feature is not allowed to vanish or go smaller.
     if compulsory:
      if radius<=minimum+1e-6:break
      radius=max(minimum,radius*.70)
     else:
      radius*=.5
   if not accepted:
    retained+=1
 # The per-vertex fillet cannot handle every line/arc chain. A rolling
 # selected cutter in the actual finished contour removes remaining concave
 # under-radii without weakening bolt support or changing mating positions.
 from .cnc_autorepair import finish_cnc_face
 working=finish_cnc_face(working,role,arm,
                         joint_cell if arm and fitted_roots(p) else None,minimum)
 if minimum>MIN_CNC_RADIUS_MM:
  # A larger cutter must never fill pre-existing hardware clearance. Circular
  # bores may be drilled separately; constrained slots require a smaller tool.
  added=working.cut(original)
  if not added.isNull() and added.Area>1e-8:
   for pt,r,_ in holes:
    bore=Part.Face(Part.Wire(Part.makeCircle(r,App.Vector(*pt,0))))
    if added.BoundBox.intersect(bore.BoundBox) and added.common(bore).Area>1e-7:
     raise ValueError(f'{role}: R{minimum:g} cutter repair would change a mounting bore. Use an appropriate smaller cutter.')
 result=shape
 for change,adding in ((original.cut(working),False),(working.cut(original),True)):
  if change.isNull() or change.Area<1e-8:continue
  change.translate(App.Vector(0,0,shape.BoundBox.ZMin));stock=change.extrude(App.Vector(0,0,shape.BoundBox.ZLength))
  result=result.fuse(stock) if adding else result.cut(stock)
 result=result.removeSplitter()
 if not result.isValid() or len(result.Solids)!=1:raise ValueError(role+': local fillets could not preserve a connected plate; review the source outline.')
 # Mandatory inside-corner check runs on the FINAL carbon outline, never on a
 # cosmetic preview, so DXF/SVG/STEP inherit the same cutter-sized geometry.
 top=max((f for f in result.Faces if f.BoundBox.ZLength<1e-5 and
          abs(f.BoundBox.ZMin-result.BoundBox.ZMax)<1e-5),key=lambda f:f.Area)
 _validate_cnc_inside_radii(top,role,minimum)
 if adapted or retained:
  detail=(f'; minimum local radius {min(adapted):.3g} mm' if adapted else '')+(f'; {retained} constrained corners retained' if retained else '')
  App.Console.PrintMessage(f'{role}: {done} corners filleted; requested {requested:g} mm'+detail+'\n')
 return result

def preview_fillet(p,role,path):
 minimum=p.CNCToolRadius
 """Lightweight target-radius preview on outside and internal cutout loops."""
 if role not in FIELDS:return path
 radius=fillet_radius(p,role)
 arm=None
 if role in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight'):
  from .parameters import arm_layouts
  from .arm_roots import fillet_root_limit
  arm=next(a for a in arm_layouts(p) if 'Arm'+a['name']==role);root_limit=fillet_root_limit(p,arm)
 from .airflow_gui import QtCore,QtGui
 transform=QtGui.QTransform();transform.scale(100,100)
 result=QtGui.QPainterPath();result.setFillRule(QtCore.Qt.OddEvenFill)
 loops=path.toSubpathPolygons(transform)
 from .preview_acceleration import LocalPathContains
 contains=LocalPathContains(path,QtGui).contains
 def area(poly):return abs(sum(a.x()*b.y()-b.x()*a.y() for a,b in zip(poly,list(poly)[1:]+[poly[0]])))
 outer_index=max(range(len(loops)),key=lambda index:area(loops[index])) if loops else -1
 round_openings=fillet_openings(p,role)
 for loop_index,loop in enumerate(loops):
  optional_loop=loop_index==outer_index or round_openings
  points=[(v.x()/100,v.y()/100) for v in loop]
  if len(points)>1 and math.dist(points[0],points[-1])<1e-8:points.pop()
  if len(points)<3:continue
  corners=[]
  def _turn(a,b,c):
   a1=math.atan2(b[1]-a[1],b[0]-a[0]);a2=math.atan2(c[1]-b[1],c[0]-b[0])
   return abs((a2-a1+math.pi)%(2*math.pi)-math.pi)
  count=len(points)
  lengths=[math.dist(points[i-1],b) for i,b in enumerate(points)]
  turns=[_turn(points[i-1],b,points[(i+1)%count]) for i,b in enumerate(points)]
  for i,b in enumerate(points):
   a,c=points[i-1],points[(i+1)%count]
   la=lengths[i];lb=lengths[(i+1)%count]
   if min(la,lb)<1e-8:corners.append((b,b,b,b));continue
   toward1=((a[0]-b[0])/la,(a[1]-b[1])/la)
   toward2=((c[0]-b[0])/lb,(c[1]-b[1])/lb)
   sx,sy=toward1[0]+toward2[0],toward1[1]+toward2[1]
   sl=math.hypot(sx,sy)
   corner_turn=math.acos(max(-1.,min(1.,-(toward1[0]*toward2[0]+toward1[1]*toward2[1]))))
   probe=min(.025,.12*min(la,lb))
   # Qt tessellates smooth circles and arcs into small segments. Do not
   # mistake the regular turning between those segments for sharp notches.
   prev_turn=turns[i-1]
   next_turn=turns[(i+1)%count]
   sampled_arc=(corner_turn>1e-6 and prev_turn>1e-6 and next_turn>1e-6
                and abs(corner_turn-prev_turn)<.07 and abs(corner_turn-next_turn)<.07)
   compulsory=(not sampled_arc and sl>1e-6 and CNC_CORNER_ANGLE_RAD<corner_turn<math.pi-CNC_CORNER_ANGLE_RAD
               and probe>1e-6 and not contains(QtCore.QPointF(b[0]+sx/sl*probe,b[1]+sy/sl*probe)))
   # Smooth sampled arcs cannot receive another corner fillet. Skip the
   # optional root and radius computations for those vertices entirely.
   if sampled_arc:
    corners.append((b,b,b,b));continue
   optional=optional_loop and (not arm or _arm_root_corner_can_fillet_xy(p,arm,b,root_limit))
   user_radius=(_arm_corner_radius(p,arm,b,root_limit) if arm else radius)
   if not compulsory and (not optional or user_radius<=1e-9):
    corners.append((b,b,b,b));continue
   floor_radius=minimum if compulsory else MIN_CNC_RADIUS_MM
   corner_radius=max(floor_radius,user_radius)
   u=(-toward1[0],-toward1[1]);v=toward2
   angle=corner_turn
   threshold=CNC_CORNER_ANGLE_RAD if compulsory else .25
   distance=min(corner_radius*math.tan(angle/2),la*.45,lb*.45) if threshold<angle<math.pi-.01 else 0.
   if distance<floor_radius*max(0.,math.tan(angle/2))-1e-5:
    # Native FreeCAD will flag this constrained corner rather than create
    # a false undersized radius; keep the preview corner unmodified.
    corners.append((b,b,b,b));continue
   if arm and not compulsory:
    from .arm_roots import fitted_roots
    if not fitted_roots(p) and p.ArmRootFillet<=0:
     along=(b[0]-arm['root'][0])*arm['unit'][0]+(b[1]-arm['root'][1])*arm['unit'][1]
     for dx,dy in ((-u[0],-u[1]),v):
      rate=dx*arm['unit'][0]+dy*arm['unit'][1]
      if rate<0:distance=min(distance,max(0.,(along-root_limit)/-rate))
   r=distance/max(1e-12,math.tan(angle/2));k=4/3*math.tan(angle/4)*r
   start=(b[0]-u[0]*distance,b[1]-u[1]*distance);end=(b[0]+v[0]*distance,b[1]+v[1]*distance)
   corners.append((start,(start[0]+u[0]*k,start[1]+u[1]*k),(end[0]-v[0]*k,end[1]-v[1]*k),end))
  q=QtGui.QPainterPath();q.moveTo(*corners[0][0])
  for start,a,b,end in corners:
   q.lineTo(*start)
   # No degenerate Bezier for ordinary polygon points. It adds three Qt
   # elements for no geometric change and makes later path booleans slower.
   if not (start==a==b==end):q.cubicTo(*a,*b,*end)
  q.closeSubpath();result.addPath(q)
 if arm:
  from .arm_roots import fitted_roots,root_cell_polygon
  if fitted_roots(p):
   # Keep the 2D preview inside the same miter cell used by the OCC solid.
   # Scale before the Qt intersection to retain small-radius curve detail.
   from .airflow_gui import polygon_path
   precision=QtGui.QTransform();precision.scale(100,100)
   clip=polygon_path(root_cell_polygon(p,arm,arm_layouts(p)))
   result=precision.inverted()[0].map(precision.map(result).intersected(precision.map(clip)))
 return result
