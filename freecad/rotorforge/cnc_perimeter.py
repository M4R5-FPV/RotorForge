"""Conservative removal of sub-cutter-sized accidental *outer* plate spurs.

Only Bottom/Mid plate blanks are touched, before through holes are machined.
Uses a 2D morphological OPENING as a source of potential removals, but does
not apply the opening wholesale: only small patches near a non-tangent, short
perimeter segment can be considered. No new material is ever added.

Hardware bearing envelopes, bores, insert stock, and TPU support are protected.
Any offset/boolean/solid validation failure returns the original geometry.
This is manufacturing cleanup, NOT another bolt reinforcement pass.
"""
import math

CLEAN_ROLES = frozenset(('BottomPlate', 'MidPlate'))
# These are conservative removal caps, not a second tooling specification.
# A larger cutter must not authorize removal of an intentional plate feature.
TINY_EDGE_MM = 1.45
KINK_DEGREES = 10.0
MAX_TRIM_AREA_MM2 = 1.8
MAX_TRIM_DIAGONAL_MM = 5.5
JUNCTION_REACH_MM = 1.65


def _distance_bbox(point, bounds):
    """Distance from a 2D point to a rectangular bounding box."""
    x,y=point
    left,bottom,right,top=bounds
    return math.hypot(max(left-x,0.,x-right),max(bottom-y,0.,y-top))


def _cleanup_scale(radius):
    """Tighten accident-detection caps for small cutters; never enlarge them."""
    return min(1., radius)


def _small_patch(area,bounds,junctions,radius):
    scale=_cleanup_scale(radius)
    if area <= 1e-7 or area > MAX_TRIM_AREA_MM2*scale**2:return False
    left,bottom,right,top=bounds
    if math.hypot(right-left,top-bottom) > MAX_TRIM_DIAGONAL_MM*scale:return False
    return any(_distance_bbox(p,bounds) <= JUNCTION_REACH_MM*scale for p in junctions)


def required_bearing_discs(p,role):
    """Protection geometry is independent of extra arm-bolt allowance."""
    from .parameters import plate_holes, standoff_layouts
    from .mount_support import (standoff_stock_radius,
                                bearing_surface_for_standoff,
                                press_nut_stock_radius)
    from .nut_seats import seats
    from .tpu_mount_layout import carbon_rim_centres
    from .hardware_layout import SIZES, metric_size
    discs=[(pt,r+p.MinimumWeb) for pt,r,kind in plate_holes(p,role)]
    for seat in seats(p,role):
        if seat['mode']=='Recessed hex nut':
            radius=(SIZES[metric_size(seat['bore'])][4]+p.NutRecessClearance)/math.sqrt(3)+p.MinimumWeb+.05
        else:radius=press_nut_stock_radius(p,seat['depth'])
        discs.append((seat['point'],radius))
    for stand in standoff_layouts(p):
        if bearing_surface_for_standoff(stand,role):
            discs.append((stand['point'],standoff_stock_radius(p)))
    discs.extend(carbon_rim_centres(p,role))
    unique=[]
    for pt,r in discs:
        if not any(math.dist(pt,q)<1e-7 and abs(r-v)<1e-7 for q,v in unique):
            unique.append((pt,r))
    return unique


def _cad_junctions(outer,radius):
    """Detect a short edge with at least one abrupt tangent junction.

    This leaves normal large corners, smooth fillet arcs and intentional plate
    profiles alone. A short arc that is tangent to its neighbors isn't a nub.
    """
    from .plate_fillets import _away
    edges=list(outer.Edges);result=[]
    max_edge=TINY_EDGE_MM*_cleanup_scale(radius)
    for edge in edges:
        if edge.Length>max_edge or edge.Length<1e-6:continue
        for vertex in edge.Vertexes:
            point=vertex.Point
            others=[e for e in edges if not e.isSame(edge) and
                    any((v.Point-point).Length<1e-5 for v in e.Vertexes)]
            if len(others)!=1:continue
            try:
                a=_away(edge,point);b=_away(others[0],point)
                if a.Length<1e-8 or b.Length<1e-8:continue
                turn=math.degrees(math.acos(max(-1.,min(1.,-a.dot(b)/(a.Length*b.Length)))))
                if turn>=KINK_DEGREES:result.append((point.x,point.y))
            except Exception:continue
    return result


def _as_single_face(shape):
    """FreeCAD versions return either a face or wire from makeOffset2D."""
    import Part
    if shape.isNull():raise ValueError('empty 2D offset')
    if len(shape.Faces)==1:return shape.Faces[0]
    if len(shape.Faces)>1:raise ValueError('offset split plate')
    if len(shape.Wires)!=1:raise ValueError('offset split outline')
    face=Part.Face(shape.Wires[0])
    if not face.isValid() or face.Area<1e-8:raise ValueError('invalid offset face')
    return face


def _cad_opened(face,radius):
    inset=_as_single_face(face.makeOffset2D(-radius,join=0))
    return _as_single_face(inset.makeOffset2D(radius,join=0))


def clean_blank_shape(p,role,shape):
    """Remove only tiny genuine overhangs; never alter hardware or add stock.

    Exact BRep difference is performed on the OUTER face only, so through-hole
    and pocket geometry isn't replaced, reconstructed or displaced. It is run
    before machining holes, to avoid offsetting their internal perimeters.
    """
    if role not in CLEAN_ROLES or shape.isNull():return shape
    radius=p.CNCToolRadius
    try:
        import FreeCAD as App
        import Part
        zmax=shape.BoundBox.ZMax; zmin=shape.BoundBox.ZMin
        horizontal=[f for f in shape.Faces if f.BoundBox.ZLength<1e-6
                    and abs(f.BoundBox.ZMax-zmax)<1e-5]
        if not horizontal:return shape
        cap=max(horizontal,key=lambda f:f.Area)
        outside=Part.Face(cap.OuterWire)
        junctions=_cad_junctions(cap.OuterWire,radius)
        if not junctions:return shape
        opened=_cad_opened(outside,radius)
        candidates=outside.cut(opened)
        if candidates.isNull() or candidates.Area<1e-8:return shape
        protections=required_bearing_discs(p,role)
        # Cache the exact bearing faces only when a candidate is nearby.
        protected_faces={}
        result=shape
        count=0
        for patch in candidates.Faces:
            box=patch.BoundBox
            bounds=(box.XMin,box.YMin,box.XMax,box.YMax)
            if not _small_patch(patch.Area,bounds,junctions,radius):continue
            forbidden=False
            for pt,r in protections:
                if _distance_bbox(pt,bounds)>r+1e-5:continue
                key=(pt,r)
                disk=protected_faces.get(key)
                if disk is None:
                    disk=Part.Face(Part.Wire(Part.makeCircle(r,App.Vector(pt[0],pt[1],zmax))))
                    protected_faces[key]=disk
                if patch.common(disk).Area>1e-7:
                    forbidden=True;break
            if forbidden:continue
            cut=patch.copy()
            cut.translate(App.Vector(0,0,zmin-.05-zmax))
            tool=cut.extrude(App.Vector(0,0,zmax-zmin+.10))
            trial=result.cut(tool).removeSplitter()
            # Individual, reversible validation: no floating faces or disconnected tabs.
            if trial.isNull() or not trial.isValid() or len(trial.Solids)!=1:
                continue
            if result.Volume-trial.Volume > patch.Area*(zmax-zmin+1e-4)+1e-3:
                continue
            result=trial;count+=1
        if count:
            App.Console.PrintMessage('%s: removed %d sub-tool-size perimeter spur(s) using CNC R%.4g (%.4g mm cutter).\n' % (role,count,radius,2*radius))
        return result
    except Exception as err:
        # Cosmetic cleanup may never make a frame unbuildable.
        try:
            import FreeCAD as App
            App.Console.PrintWarning('%s: optional CNC perimeter cleanup at R%.4g could not complete; original blank retained. Normal CNC fillets still run. (%s)\n' % (role,radius,err))
        except Exception:pass
        return shape


def _path_junctions(path,radius):
    """Detect the equivalent non-tangent short runs in Qt's 2D perimeter."""
    points=[]
    max_edge=TINY_EDGE_MM*_cleanup_scale(radius)
    for poly in path.toSubpathPolygons():
        coords=[(pt.x(),pt.y()) for pt in poly]
        if len(coords)>1 and math.dist(coords[0],coords[-1])<1e-6:coords.pop()
        if len(coords)<4:continue
        n=len(coords)
        for i in range(n):
            a=coords[i-1];b=coords[i];c=coords[(i+1)%n];d=coords[(i+2)%n]
            small=math.dist(b,c)
            if not (1e-5<small<=max_edge):continue
            def corner(u,v,w):
                dx1,dy1=v[0]-u[0],v[1]-u[1]
                dx2,dy2=w[0]-v[0],w[1]-v[1]
                if min(math.hypot(dx1,dy1),math.hypot(dx2,dy2))<1e-7:return 0.
                dot=(dx1*dx2+dy1*dy2)/(math.hypot(dx1,dy1)*math.hypot(dx2,dy2))
                return math.degrees(math.acos(max(-1.,min(1.,dot))))
            if corner(a,b,c)>=KINK_DEGREES:points.append(b)
            if corner(b,c,d)>=KINK_DEGREES:points.append(c)
    return points


def clean_blank_path(p,role,path):
    """The 2D editor reflects the same subtractive CNC cleanup (best effort)."""
    if role not in CLEAN_ROLES:return path
    radius=p.CNCToolRadius
    from .airflow_gui import QtGui,QtCore,polygon_path,_path_filled_area,capsule_path
    try:
        junctions=_path_junctions(path,radius)
        if not junctions:return path
        stroke=QtGui.QPainterPathStroker()
        stroke.setWidth(2*radius)
        stroke.setCapStyle(QtCore.Qt.RoundCap)
        stroke.setJoinStyle(QtCore.Qt.RoundJoin)
        shrunk=path.subtracted(stroke.createStroke(path))
        if shrunk.isEmpty():return path
        opened=shrunk.united(stroke.createStroke(shrunk))
        candidates=path.subtracted(opened)
        protection=required_bearing_discs(p,role)
        removal=QtGui.QPainterPath()
        for poly in candidates.toSubpathPolygons():
            pts=[(pt.x(),pt.y()) for pt in poly]
            if len(pts)<3:continue
            patch=polygon_path(pts)
            box=patch.boundingRect()
            bounds=(box.left(),box.top(),box.right(),box.bottom())
            if not _small_patch(_path_filled_area(patch),bounds,junctions,radius):continue
            if any(_distance_bbox(pt,bounds)<=r+1e-5 and
                   _path_filled_area(patch.intersected(capsule_path(pt,pt,r)))>1e-7
                   for pt,r in protection):continue
            removal=removal.united(patch)
        return path.subtracted(removal) if not removal.isEmpty() else path
    except Exception:
        return path
