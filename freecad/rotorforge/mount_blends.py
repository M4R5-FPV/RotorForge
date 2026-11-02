"""Additive fillets at automatic mounting-stock junctions only."""
from .mount_support import support_distance


def blend_radius(p):
    return max(2.,p.MinimumWeb)


def blend_shape(p,shape,supports):
    if not supports:return shape
    import FreeCAD as App
    import Part
    from .plate_fillets import _corners,_away,_blend,_face
    cap=max((f for f in shape.Faces if f.BoundBox.ZLength<1e-5 and abs(f.BoundBox.ZMax-shape.BoundBox.ZMax)<1e-5),key=lambda f:f.Area).copy()
    cap.translate(App.Vector(0,0,-cap.CenterOfMass.z))
    wires=[cap.OuterWire]+[w for w in cap.Wires if not w.isSame(cap.OuterWire)]
    original=_face(wires);working=original
    for point,limit in _corners(wires[0]):
        if support_distance((point.x,point.y),supports)<-1e-5:continue
        edges=list(wires[0].Edges)
        adjacent=[e for e in edges if any((v.Point-point).Length<1e-6 for v in e.Vertexes)]
        if len(adjacent)!=2:continue
        direction=_away(adjacent[0],point)+_away(adjacent[1],point)
        if direction.Length<1e-7:continue
        direction.normalize()
        # Only re-entrant corners need a bridge. Convex ends remain round,
        # and no mounting or insert-bearing material may be cut away.
        if working.isInside(point+direction*.001,1e-7,False):continue
        radius=min(blend_radius(p),limit);accepted=False
        for attempt in range(14):
            if radius<.01:break
            try:
                arc,first,second=_blend(*adjacent,point,radius)
                rest=[e for e in edges if not any(e.isSame(a) for a in adjacent)]
                wire=Part.Wire(Part.__sortEdges__(rest+[first,arc,second]))
                if not wire.isClosed() or not wire.isValid():raise ValueError('wire')
                trial=[wire]+wires[1:];face=_face(trial)
                if not face.isValid() or len(face.Faces)!=1 or len(face.Wires)!=len(wires):raise ValueError('face')
                if working.cut(face).Area>1e-7:raise ValueError('would remove bearing stock')
                if face.cut(working).Area<1e-9:raise ValueError('no blend')
                wires=trial;working=face;accepted=True;break
            except Exception:radius*=.5
        if not accepted:raise ValueError('A mounting extension cannot form a rounded junction; move the fixing slightly or increase the main outline.')
    added=working.cut(original)
    if added.Area<1e-8:return shape
    added.translate(App.Vector(0,0,shape.BoundBox.ZMin))
    result=shape.fuse(added.extrude(App.Vector(0,0,shape.BoundBox.ZLength))).removeSplitter()
    if not result.isValid() or len(result.Solids)!=1:raise ValueError('Mounting extension blending must preserve a connected solid.')
    return result


def blend_path(p,path,supports):
    """Portable additive closing, clipped to the mounting junction vicinity."""
    if not supports:return path
    from .airflow_gui import QtGui,QtCore,capsule_path
    radius=blend_radius(p)
    stroke=QtGui.QPainterPathStroker();stroke.setWidth(2*radius)
    stroke.setJoinStyle(QtCore.Qt.RoundJoin);stroke.setCapStyle(QtCore.Qt.RoundCap)
    expanded=path.united(stroke.createStroke(path))
    closed=expanded.subtracted(stroke.createStroke(expanded))
    mask=QtGui.QPainterPath()
    for a,b,r in supports:mask=mask.united(capsule_path(a,b,r+2*radius))
    return path.united(closed.subtracted(path).intersected(mask))
