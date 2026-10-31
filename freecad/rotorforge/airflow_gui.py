"""Per-part pattern editor and local-coordinate cutting preview."""
import math,json
try:
    from PySide import QtCore, QtGui, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
    except ImportError:
        from PySide6 import QtCore, QtGui, QtWidgets
from .cutouts import CUTOUT_ROLES, CUTOUT_TYPES, CUTOUT_MODES, MAX_PATTERNS, MAX_ENABLED_CUTOUTS, PATTERN_DEFAULTS, parse_patterns, encode_patterns, pattern_instances, cutout_polygon
from .parameters import bottom_bounds, mid_bounds, top_bounds, plate_holes, arm_brace_layouts, arm_layouts, strap_slots, stack_holes, upper_clamp_active, underside_clamp_active, keystone_active, mid_tabs
from .parameters import bottom_body_bounds, bottom_tabs
from .fpv import CAMERA_ROLES, camera_mounts, camera_slots, camera_position_y, camera_pivot_height
from .motor_pads import motor_pad_primitives, motor_tip_slots, motor_pad_unit
from .stack_reliefs import stack_escape_segment
from .plate_profiles import plate_base_polygon, centre_polygon
from .arm_roots import fitted_roots, root_cell_polygon, compact_key_outline, beam_profile_polygon, widened_roots, stem_stations

ROLE_LABELS={'FrontBumper':'Front bumper','CameraPadLeft':'Camera pad left','CameraPadRight':'Camera pad right','BottomPlate':'Bottom plate','MidPlate':'Mid plate','TopPlate':'Top plate',
             'ArmClampPlate':'Upper arm clamp / FC plate','ArmKeystone':'Arm keystone',
             'ArmLowerClampPlate':'Lower arm clamp plate',
             'CameraMountLeft':'Camera side plate — left','CameraMountRight':'Camera side plate — right',
             'ArmFrontRight':'Front right arm','ArmFrontLeft':'Front left arm',
             'ArmRearLeft':'Rear left arm','ArmRearRight':'Rear right arm'}


def capsule_path(a,b,r):
    line=QtGui.QPainterPath(QtCore.QPointF(*a));line.lineTo(QtCore.QPointF(*b))
    if math.dist(a,b)<1e-8:
        path=QtGui.QPainterPath();path.addEllipse(QtCore.QPointF(*a),r,r);return path
    stroke=QtGui.QPainterPathStroker();stroke.setWidth(2*r);stroke.setCapStyle(QtCore.Qt.RoundCap)
    return stroke.createStroke(line)


def polygon_path(points):
    path=QtGui.QPainterPath(QtCore.QPointF(*points[0]))
    for point in points[1:]:path.lineTo(*point)
    path.closeSubpath()
    return path


def _straight_arm_stem_path(p,arm,clearance=0.):
    if not widened_roots(p):return capsule_path(arm['start'],arm.get('beam_end',arm['motor']),p.ArmWidth/2+clearance)
    start,reach,end,motor,rr,rb=stem_stations(p,arm)
    path=QtGui.QPainterPath(QtCore.QPointF(start,rr))
    for point in ((reach,rr),(end,rb),(motor,rb)):path.lineTo(*point)
    path.arcTo(QtCore.QRectF(motor-rb,-rb,2*rb,2*rb),270,180)
    for point in ((end,-rb),(reach,-rr),(start,-rr)):path.lineTo(*point)
    path.arcTo(QtCore.QRectF(start-rr,-rr,2*rr,2*rr),90,180)
    path.closeSubpath()
    transform=QtGui.QTransform();transform.translate(*arm['root'])
    transform.rotate(math.degrees(math.atan2(arm['unit'][1],arm['unit'][0])))
    path=transform.map(path)
    if clearance:
        stroke=QtGui.QPainterPathStroker();stroke.setWidth(2*clearance);stroke.setJoinStyle(QtCore.Qt.RoundJoin)
        path=path.united(stroke.createStroke(path))
    return path


def arm_stem_path(p,arm,clearance=0.):
    path=_straight_arm_stem_path(p,arm,clearance)
    outline=beam_profile_polygon(p,arm)
    if outline:
        extra=polygon_path(outline)
        if clearance:
            stroke=QtGui.QPainterPathStroker();stroke.setWidth(2*clearance);stroke.setJoinStyle(QtCore.Qt.RoundJoin)
            extra=extra.united(stroke.createStroke(extra))
        path=path.united(extra)
    if p.MotorPadRotationPivot=='Pad beginning':
        path=path.united(capsule_path(arm['beam_end'],arm['motor'],p.ArmWidth/2+clearance))
    return path


def arm_blank_path(p,arm,arms=None):
    arms=arm_layouts(p) if arms is None else arms
    transform=QtGui.QTransform();transform.translate(*arm['motor'])
    ux,uy=motor_pad_unit(p,arm)
    transform.rotate(math.degrees(math.atan2(uy,ux)))
    path=arm_stem_path(p,arm).united(transform.map(motor_pad_path(p)))
    path=blend_motor_junction_path(p,arm,path)
    for a,b,r in motor_tip_slots(p,arm):path=path.subtracted(capsule_path(a,b,r))
    if fitted_roots(p):
        path=path.intersected(polygon_path(root_cell_polygon(p,arm,arms)))
        if keystone_active(p):path=path.subtracted(polygon_path(compact_key_outline(p,arms,True)))
    return path


def arm_stack_access_path(p,blank):
    """Match the round relief or open slot used by the CAD arm builder."""
    if not p.ArmRootReliefsEnabled:return blank
    box=blank.boundingRect();tools=QtGui.QPainterPath()
    for pt in stack_holes(p):
        circle=QtGui.QPainterPath();circle.addEllipse(QtCore.QPointF(*pt),p.StackAccessDiameter/2,p.StackAccessDiameter/2)
        if p.ArmRootReliefShape=='Slot toward stack centre':
            if blank.intersected(circle).isEmpty():continue
            tool=capsule_path(*stack_escape_segment(p,pt,(box.left(),box.top(),box.right(),box.bottom())))
        else:tool=circle
        tools=tools.united(tool)
    return blank.subtracted(tools)


def keystone_path(p,arms=None):
    arms=arm_layouts(p) if arms is None else arms
    if fitted_roots(p):return polygon_path(compact_key_outline(p,arms))
    path=profile_path(p,'BottomPlate',p.BodyWidth-2*p.MinimumWeb,-p.ArmRootY,p.ArmRootY,p.CornerRadius,
                      p.BottomCentreWidth-2*p.MinimumWeb if p.BottomCentreWidth else None,trim_ends=False)
    for arm in arms:path=path.subtracted(arm_stem_path(p,arm,p.KeystoneClearance))
    return path


def profile_path(p,role,width,rear,front,radius,wide_override=None,trim_ends=True):
    path=QtGui.QPainterPath();path.addRoundedRect(QtCore.QRectF(-width/2,rear,width,front-rear),radius,radius)
    outline=plate_base_polygon(p,role,width,rear,front,radius)
    if outline:path=polygon_path(outline)
    points=centre_polygon(p,role,width,rear,front,wide_override)
    if points:
        extra=QtGui.QPainterPath();extra.moveTo(*points[0])
        for point in points[1:]:extra.lineTo(*point)
        extra.closeSubpath();path=path.united(extra)
    from .bottom_nose import edge_commands
    for end in ('Front','Rear') if trim_ends else ():
        commands=edge_commands(p,role,end,width,rear,front)
        if not commands:continue
        mask=QtGui.QPainterPath()
        for item in commands:
            if item[0]=='M':mask.moveTo(*item[1])
            elif item[0]=='L':mask.lineTo(*item[1])
            else:mask.cubicTo(*(value for point in item[1:] for value in point))
        mask.closeSubpath();path=path.intersected(mask)
    return path


def mid_tab_paths(p,arms=None):
    arms=arm_layouts(p) if arms is None else arms
    boundary=profile_path(p,'BottomPlate',p.BodyWidth,*bottom_bounds(p),p.CornerRadius)
    paths=[]
    for arm,(a,b,r) in zip((a for a in arms if a['root'][1]>0),mid_tabs(p)):
        root=arm_stem_path(p,arm)
        if fitted_roots(p):
            root=root.intersected(polygon_path(root_cell_polygon(p,arm,arms)))
            if keystone_active(p):root=root.subtracted(polygon_path(compact_key_outline(p,arms,True)))
        paths.append(capsule_path(a,b,r).intersected(root).intersected(boundary))
    return tuple(paths)


def mid_plate_path(p,arms=None):
    path=profile_path(p,'MidPlate',p.BodyWidth,*mid_bounds(p),p.CornerRadius)
    for tab in mid_tab_paths(p,arms):path=path.united(tab)
    return path


def bottom_plate_path(p,arms=None):
    arms=arm_layouts(p) if arms is None else arms
    path=profile_path(p,'BottomPlate',p.BodyWidth,*bottom_body_bounds(p),p.CornerRadius)
    boundary=profile_path(p,'BottomPlate',p.BodyWidth,*bottom_bounds(p),p.CornerRadius)
    upper=profile_path(p,'MidPlate',p.BodyWidth,*mid_bounds(p),p.CornerRadius)
    for arm,(a,b,r) in zip((a for a in arms if a['root'][1]<0),bottom_tabs(p)):
        root=arm_stem_path(p,arm)
        if fitted_roots(p):
            root=root.intersected(polygon_path(root_cell_polygon(p,arm,arms)))
            if keystone_active(p):root=root.subtracted(polygon_path(compact_key_outline(p,arms,True)))
        path=path.united(capsule_path(a,b,r).intersected(root).intersected(boundary).intersected(upper))
    return path


def clamp_plate_path(p,role='ArmClampPlate'):
    from .clamp_outline import clamp_outline_layout
    from .arm_roots import root_width
    c=arm_brace_layouts(p)[0];rear,front,pads=clamp_outline_layout(p);arms=arm_layouts(p)
    boundary=profile_path(p,role,c['width'],c['rear'],c['front'],c['radius'])
    path=profile_path(p,role,c['width'],rear,front,c['radius'])
    for arm in arms:
        root=arm_stem_path(p,arm)
        if fitted_roots(p):
            root=root.intersected(polygon_path(root_cell_polygon(p,arm,arms)))
            if keystone_active(p):root=root.subtracted(polygon_path(compact_key_outline(p,arms,True)))
        path=path.united(capsule_path(*arm['bolts'],root_width(p)/2).intersected(root))
    for a,b,r in pads:path=path.united(capsule_path(a,b,r))
    return path.intersected(boundary)


def motor_pad_path(p):
    path=QtGui.QPainterPath();cuts=[]
    for d in motor_pad_primitives(p):
        part=QtGui.QPainterPath()
        if d['kind']=='circle':part.addEllipse(QtCore.QPointF(*d['centre']),d['radius'],d['radius'])
        elif d['kind']=='rounded':part.addRoundedRect(QtCore.QRectF(-d['width']/2,-d['width']/2,d['width'],d['width']),d['radius'],d['radius'])
        else:
            part.moveTo(*d['points'][0])
            for point in d['points'][1:]:part.lineTo(*point)
            part.closeSubpath()
        if d.get('operation')=='cut':cuts.append(part)
        else:path=path.united(part)
    if cuts:
        # Qt flattens curves during boolean operations. Work at a larger scale
        # so small concave reliefs keep their dimensions in the preview.
        scale=QtGui.QTransform();scale.scale(100,100)
        path=scale.map(path)
        for part in cuts:path=path.subtracted(scale.map(part))
        path=scale.inverted()[0].map(path)
    for a,b,radius in motor_tip_slots(p):path=path.subtracted(capsule_path(a,b,radius))
    return path


def cutout_path(pattern):
    w,l=pattern['width'],pattern['length'];path=QtGui.QPainterPath()
    if pattern['shape']=='Circle':path.addEllipse(QtCore.QPointF(),w/2,w/2)
    elif pattern['shape']=='Ellipse':path.addEllipse(QtCore.QPointF(),w/2,l/2)
    elif pattern['shape']=='Slot':
        path=(capsule_path((0,-(l-w)/2),(0,(l-w)/2),w/2) if l>=w else
              capsule_path((-(w-l)/2,0),((w-l)/2,0),l/2))
    elif pattern['shape']=='Rounded rectangle':path.addRoundedRect(QtCore.QRectF(-w/2,-l/2,w,l),min(w,l)/4,min(w,l)/4)
    else:
        points=cutout_polygon(pattern);path.moveTo(*points[0])
        for point in points[1:]:path.lineTo(*point)
        path.closeSubpath()
    transform=QtGui.QTransform();transform.translate(pattern['x'],pattern['y']);transform.rotate(pattern['rotation'])
    return transform.map(path)


def combined_cutout_path(patterns,role):
    scale=QtGui.QTransform();scale.scale(100,100);path=QtGui.QPainterPath()
    for pattern in patterns:
        if pattern['enabled'] and pattern['role']==role:
            for instance in pattern_instances(pattern):path=path.united(scale.map(cutout_path(instance)))
    return scale.inverted()[0].map(path)



from functools import lru_cache

@lru_cache(maxsize=32)
def _profile_parameters(p):
    # Protection/vent settings do not change any carbon profile. Keep planar
    # caches warm while tuning those controls on an existing complex frame.
    from dataclasses import replace
    from .parameters import Parameters
    defaults=Parameters()
    return replace(p,**{name:getattr(defaults,name) for name in p.__dataclass_fields__
                       if name.startswith(('FlexGuard','FlexProtector')) or name in ('FlexSideGuards','FlexMotorProtectors','PrintedPartColour')})

@lru_cache(maxsize=96)
def _finished_part_path_cached(p,role,pattern_json,include_strap_notches=True):
    return _make_finished_part_path(p,role,parse_patterns(pattern_json),include_strap_notches)

def finished_part_path(p,role,patterns=None,include_strap_notches=True):
    import json
    encoded=p.CutoutPatterns if patterns is None else json.dumps(patterns,sort_keys=True,separators=(',',':'))
    return QtGui.QPainterPath(_finished_part_path_cached(_profile_parameters(p),role,encoded,include_strap_notches))

def _make_finished_part_path(p,role,patterns=None,include_strap_notches=True):
    """Shared complete 2D part profile: joints, holes, slots and applied cuts."""
    path=QtGui.QPainterPath();holes=[];slots=[]
    def rect(width,rear,front,radius):
        q=QtGui.QPainterPath();q.addRoundedRect(QtCore.QRectF(-width/2,rear,width,front-rear),radius,radius);return q
    if role in CAMERA_ROLES:
        if not p.FPVEnabled:return path
        mount=camera_mounts(p)[0];height=mount['z1']-mount['z0']
        cy=camera_position_y(p);points=[(y-cy,z-p.BottomThickness) for y,z in mount['wall_profile']]
        path.moveTo(*points[0])
        for point in points[1:]:path.lineTo(*point)
        path.closeSubpath()
        for y in mount['tabs_y']:
            path.addRect(QtCore.QRectF(y-cy-p.CameraTabLength/2,-p.BottomThickness,p.CameraTabLength,p.BottomThickness))
        for y in mount['top_tabs_y']:
            path.addRect(QtCore.QRectF(y-cy-p.CameraTabLength/2,height,p.CameraTabLength,p.TopThickness))
        from .fpv import camera_tab_reliefs
        reliefs=camera_tab_reliefs(p,mount)
        if reliefs:
            # Qt booleans flatten curves in coordinate units; work at 100x
            # so small cutter arcs remain round in the millimetre preview.
            precision=QtGui.QTransform();precision.scale(100,100)
            path=precision.map(path)
            for y,z,r in reliefs:
                relief=QtGui.QPainterPath();relief.addEllipse(QtCore.QPointF(y-cy,z-p.BottomThickness),r,r)
                path=path.subtracted(precision.map(relief))
            path=precision.inverted()[0].map(path)
        holes=[((y-cy,z-p.BottomThickness),p.CameraSideHoleDiameter/2) for y,z in mount['side_holes']] if p.FlexCameraMode!='Captured inserts' else []
        if p.FlexCameraMode=='Captured inserts':
            from .flex_preview import camera_interface_path
            opening=camera_interface_path(p,p.FlexInsertWidth,p.FlexInsertHeight)
            precision=QtGui.QTransform();precision.scale(100,100)
            path=precision.inverted()[0].map(precision.map(path).subtracted(precision.map(opening)))
        for arc in (mount['side_arcs'] if p.FlexCameraMode!='Captured inserts' else ()):
            points=[(arc['centre'][0]-cy+arc['radius']*math.cos(math.radians(a)),arc['centre'][1]-p.BottomThickness+arc['radius']*math.sin(math.radians(a)))
                    for a in (arc['start']+(arc['end']-arc['start'])*i/40 for i in range(41))]
            for a,b in zip(points,points[1:]):path=path.subtracted(capsule_path(a,b,arc['width']/2))
    elif role in ('BottomPlate','MidPlate','TopPlate'):
        rear,front={'BottomPlate':bottom_bounds,'MidPlate':mid_bounds,'TopPlate':top_bounds}[role](p)
        path=profile_path(p,role,p.TopWidth if role=='TopPlate' else p.BodyWidth,rear,front,p.CornerRadius)
        if role=='MidPlate':
            path=mid_plate_path(p)
        elif role=='BottomPlate':
            path=bottom_plate_path(p)
        holes=[(pt,r) for pt,r,_ in plate_holes(p,role)]
        if role in ('BottomPlate','TopPlate'):slots=list(camera_slots(p,role))
        if role=='TopPlate':
            slots+=list(strap_slots(p))
    elif role in ('ArmClampPlate','ArmLowerClampPlate'):
        clamps=arm_brace_layouts(p)
        if not clamps or role=='ArmLowerClampPlate' and not underside_clamp_active(p) or role=='ArmClampPlate' and not upper_clamp_active(p):return path
        c=clamps[0];path=clamp_plate_path(p,role)
        holes=[(pt,r) for pt,r,_ in plate_holes(p,role)]
    elif role=='ArmKeystone':
        path=keystone_path(p)
        holes=[(pt,p.StackAccessDiameter/2) for pt in stack_holes(p)]
    else:
        arm=next(a for a in arm_layouts(p) if 'Arm'+a['name']==role)
        path=arm_stack_access_path(p,arm_blank_path(p,arm))
        slots=list(motor_tip_slots(p,arm))
        holes=[(pt,p.RootHoleDiameter/2) for pt in arm['bolts']]+[(pt,p.MotorHoleDiameter/2) for pt in arm['motor_holes']]+[(arm['motor'],p.MotorCenterDiameter/2)]
    if role=='TopPlate':
        from .strap_openings import notch_polygons
        for poly in notch_polygons(p) if include_strap_notches else ():
            cut=QtGui.QPainterPath();cut.addPolygon(QtGui.QPolygonF([QtCore.QPointF(*pt) for pt in poly]));cut.closeSubpath();path=path.subtracted(cut)
    for pt,r in holes:
        hole=QtGui.QPainterPath();hole.addEllipse(QtCore.QPointF(*pt),r,r);path=path.subtracted(hole)
    for a,b,r in slots:path=path.subtracted(capsule_path(a,b,r))
    from .plate_fillets import preview_fillet
    return preview_fillet(p,role,path.subtracted(combined_cutout_path(parse_patterns(p.CutoutPatterns) if patterns is None else patterns,role)))

class AirflowPreview(QtWidgets.QWidget):
    """Saved-pattern locator; all picking stays in Qt, without CAD work."""
    def __init__(self,editor):
        super().__init__();self.editor=editor;self.setMinimumHeight(280)
        self.setMouseTracking(True);self.setCursor(QtCore.Qt.PointingHandCursor)
        self._records_key=None;self._records=();self._focus=False;self._last_pick=None;self.last_error=None
        self.setToolTip('Click a saved cutout to edit it. Click again in the same place to cycle overlapping patterns. Arrays select the whole saved pattern.')

    def records(self):
        e=self.editor;role=e.role.currentData();selected=e._selected_index
        # Enabled cuts are bounded by MAX_ENABLED_CUTOUTS. Only the selected
        # disabled array is expanded, avoiding 80,000 inactive copies in a view.
        indices=tuple(i for i,p in enumerate(e.patterns) if p['role']==role and not e.pattern_list.item(i).isHidden() and (p['enabled'] or i==selected))
        key=(role,json.dumps(e.patterns,sort_keys=True),indices)
        if key!=self._records_key:
            records=[]
            for i in indices:
                paths=tuple(cutout_path(v) for v in pattern_instances(e.patterns[i]))
                box=QtCore.QRectF()
                for path in paths:box=box.united(path.boundingRect())
                records.append((i,paths,box))
            self._records_key=key;self._records=tuple(records)
        return self._records

    def view(self):
        e=self.editor;p=e.get_parameters();role=e.role.currentData()
        path=finished_part_path(p,role,e.patterns);box=finished_part_path(p,role,[]).boundingRect()
        if box.isEmpty():
            for i,paths,extent in self.records():box=box.united(extent)
        if self._focus:
            record=next((r for r in self.records() if r[0]==e._selected_index),None)
            if record:box=record[2].adjusted(-4,-4,4,4)
        scale=max(.001,min(max(1,self.width()-32)/max(1,box.width()),max(1,self.height()-32)/max(1,box.height())))
        transform=QtGui.QTransform();transform.translate(self.width()/2,self.height()/2);transform.scale(scale,-scale);transform.translate(-box.center().x(),-box.center().y())
        return path,transform,scale

    def fit_plate(self):self._focus=False;self.update()
    def zoom_selected(self):
        if self.editor._selected_index<0:return
        self._focus=True;self.update()

    def number_label(self,index,box,transform):
        point=transform.map(box.center());font=QtGui.QFont(self.font());font.setPixelSize(11);font.setBold(index==self.editor._selected_index)
        width=QtGui.QFontMetrics(font).horizontalAdvance('#'+str(index+1))+8
        return QtCore.QRectF(point.x()-width/2,point.y()-9,width,18),font

    def hit_indices(self,position):
        path,transform,scale=self.view();point=transform.inverted()[0].map(position)
        stroke=QtGui.QPainterPathStroker();stroke.setWidth(8/scale)
        hits=[]
        for i,paths,box in reversed(self.records()):
            if not box.adjusted(-4/scale,-4/scale,4/scale,4/scale).contains(point):continue
            tag_visible=self.editor.show_numbers.isChecked() or i==self.editor._selected_index
            if (tag_visible and self.number_label(i,box,transform)[0].contains(position)) or any(v.contains(point) or stroke.createStroke(v).contains(point) for v in paths):hits.append(i)
        return hits

    def mousePressEvent(self,event):
        if event.button()!=QtCore.Qt.LeftButton:return super().mousePressEvent(event)
        try:
            pos=event.position() if hasattr(event,'position') else QtCore.QPointF(event.pos())
            hits=self.hit_indices(pos)
            if not hits:return
            previous=self._last_pick
            repeat=previous and (pos-previous[0]).manhattanLength()<=6 and hits==previous[1]
            index=hits[(hits.index(previous[2])+1)%len(hits)] if repeat and previous[2] in hits else hits[0]
            if self.editor.choose_pattern(index):
                self._last_pick=(pos,hits,index)
                if len(hits)>1:self.editor.status.setText('Selected #'+str(index+1)+'. '+str(len(hits))+' overlapping patterns here; click again to cycle. Edit and press Apply to pattern.')
        except (ValueError,RuntimeError):return

    def mouseMoveEvent(self,event):
        try:
            pos=event.position() if hasattr(event,'position') else QtCore.QPointF(event.pos())
            hits=self.hit_indices(pos)
            text='\n'.join(self.editor.pattern_text(i) for i in hits)
            self.setToolTip(text+'\nClick to select; click again to cycle overlaps.' if hits else 'Click a saved cutout to select it. Disabled patterns can be found in the list.')
        except (ValueError,RuntimeError):pass

    def paintEvent(self,event):
        painter=QtGui.QPainter(self);painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(),QtGui.QColor('#f3f6f8'));self.last_error=None
        try:
            path,transform,scale=self.view();painter.setTransform(transform)
            painter.setPen(QtGui.QPen(QtGui.QColor('#111315'),.8/scale));painter.setBrush(QtGui.QColor('#2e3033'));painter.drawPath(path)
            for i,paths,box in sorted(self.records(),key=lambda r:r[0]==self.editor._selected_index):
                selected=i==self.editor._selected_index
                if not selected and not self.editor.show_numbers.isChecked():continue
                if selected:
                    pen=QtGui.QPen(QtGui.QColor('#d87809'),2.5/scale)
                    if not self.editor.patterns[i]['enabled']:pen.setStyle(QtCore.Qt.DashLine)
                    painter.setPen(pen);painter.setBrush(QtGui.QColor(255,178,65,65))
                    for cut in paths:painter.drawPath(cut)
                if self.editor.show_numbers.isChecked() or selected:
                    rect,font=self.number_label(i,box,transform);painter.save();painter.resetTransform()
                    text='#'+str(i+1);painter.setFont(font)
                    painter.setPen(QtGui.QColor('#9a4d00') if selected else QtGui.QColor('#08798a'));painter.setBrush(QtGui.QColor(255,255,255,230));painter.drawRoundedRect(rect,3,3);painter.drawText(rect,QtCore.Qt.AlignCenter,text);painter.restore()
        except Exception as exc:self.last_error=str(exc)
        finally:painter.end()


class AirflowEditor(QtWidgets.QWidget):
    changed=QtCore.Signal(str)
    def __init__(self,get_parameters):
        super().__init__();self.get_parameters=get_parameters;self.patterns=[];self.inputs={};self._selected_index=-1
        layout=QtWidgets.QVBoxLayout(self)
        note=QtWidgets.QLabel('Add a pattern, then select it to edit and press Apply to pattern. Overlapping cutouts on the same part merge into one opening. Leave material between separate openings, or overlap them rather than merely touching. Inactive parts retain their patterns. Choose Interior for airflow openings or Outline notch to shape a main or clamp plate edge. CAD checks protect fasteners, holes and captured tab sockets.');note.setWordWrap(True);layout.addWidget(note)
        self.capacity=QtWidgets.QLabel();layout.addWidget(self.capacity)
        self.pattern_list=QtWidgets.QListWidget();self.pattern_list.setMinimumHeight(105);self.pattern_list.setMaximumHeight(160)
        filters=QtWidgets.QHBoxLayout();layout.addLayout(filters)
        self.find_pattern=QtWidgets.QLineEdit();self.find_pattern.setPlaceholderText('Find cutout: #number, shape, mode, coordinates...');self.find_pattern.setClearButtonEnabled(True);filters.addWidget(self.find_pattern,2)
        self.filter_role=QtWidgets.QComboBox();self.filter_role.addItem('All parts',None)
        for part in CUTOUT_ROLES:self.filter_role.addItem(ROLE_LABELS[part],part)
        self.filter_role.setToolTip('Filter the saved-pattern list. Selecting a result opens its part in the preview.');filters.addWidget(self.filter_role,1)
        self.filter_count=QtWidgets.QLabel();layout.addWidget(self.filter_count)
        layout.addWidget(self.pattern_list)
        form=QtWidgets.QFormLayout();layout.addLayout(form)
        self.role=QtWidgets.QComboBox()
        for role in CUTOUT_ROLES:self.role.addItem(ROLE_LABELS[role],role)
        self.role.setCurrentIndex(2);form.addRow('Part',self.role)
        self.shape=QtWidgets.QComboBox();self.shape.addItems(CUTOUT_TYPES);self.shape.setCurrentText('Slot');form.addRow('Cutout type',self.shape)
        self.shape.setToolTip('Keep the original four types or choose Ellipse, Rectangle, Triangle, Diamond, Trapezoid, Pentagon, Octagon or Chevron. Width and length set the overall local size; Circle uses width only. Overlap patterns on the same part to combine their openings.')
        self.mode=QtWidgets.QComboBox();self.mode.addItems(CUTOUT_MODES);form.addRow('Cutting mode',self.mode)
        self.mode.setToolTip('Interior protects the entire boundary. Outline notch must cross an outside edge of a main or clamp plate; existing holes, slots and fasteners remain protected. Patterns can overlap to combine.')
        self.enabled=QtWidgets.QCheckBox('Enabled');self.enabled.setChecked(True);form.addRow(self.enabled)
        for keys,title in ((('width','length'),'Width / length'),(('x','y'),'Centre U / V'),(('columns','rows'),'Columns / rows'),(('pitch_x','pitch_y'),'Pitch U / V'),(('rotation',),'Rotation')):
            row=QtWidgets.QWidget();line=QtWidgets.QHBoxLayout(row);line.setContentsMargins(0,0,0,0)
            for key in keys:
                integer=key in ('columns','rows');control=QtWidgets.QSpinBox() if integer else QtWidgets.QDoubleSpinBox()
                if integer:control.setRange(1,20)
                else:
                    control.setDecimals(2);control.setRange(-700 if key in ('x','y') else -360 if key=='rotation' else .5,700 if key in ('x','y') else 360 if key=='rotation' else 500)
                    control.setSuffix('°' if key=='rotation' else ' mm')
                control.setValue(PATTERN_DEFAULTS[key]);line.addWidget(control);self.inputs[key]=control
            form.addRow(title,row)
        self.coordinates=QtWidgets.QLabel();self.coordinates.setWordWrap(True);layout.addWidget(self.coordinates)
        buttons=QtWidgets.QHBoxLayout();layout.addLayout(buttons)
        self.add_button=QtWidgets.QPushButton('Add pattern');self.apply_button=QtWidgets.QPushButton('Apply to pattern');self.remove_button=QtWidgets.QPushButton('Remove')
        for b in (self.add_button,self.apply_button,self.remove_button):buttons.addWidget(b)
        self.discard_button=QtWidgets.QPushButton('Discard unapplied changes');layout.addWidget(self.discard_button)
        self.discard_button.clicked.connect(self.discard_changes)
        self.copy_button=QtWidgets.QPushButton('Copy to other camera side');layout.addWidget(self.copy_button)
        locator=QtWidgets.QHBoxLayout();layout.addLayout(locator)
        self.show_numbers=QtWidgets.QCheckBox('Show pattern numbers');self.show_numbers.setChecked(True);locator.addWidget(self.show_numbers)
        self.zoom_button=QtWidgets.QPushButton('Zoom to selected');locator.addWidget(self.zoom_button)
        self.fit_button=QtWidgets.QPushButton('Fit plate');locator.addWidget(self.fit_button)
        self.preview=AirflowPreview(self);layout.addWidget(self.preview)
        self.find_pattern.textChanged.connect(self.filter_patterns);self.filter_role.currentIndexChanged.connect(self.filter_patterns)
        self.show_numbers.toggled.connect(self.preview.update);self.zoom_button.clicked.connect(self.preview.zoom_selected);self.fit_button.clicked.connect(self.preview.fit_plate)
        # Keep locating and visual selection together, ahead of the edit form.
        layout.removeItem(locator);layout.removeWidget(self.preview)
        index=layout.indexOf(self.pattern_list)+1;layout.insertLayout(index,locator);layout.insertWidget(index+1,self.preview)
        self.status=QtWidgets.QLabel('Click a saved opening to select it; click again to cycle overlaps. Orange highlights the selected pattern. CAD checks run on Create / Update.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.check_button=QtWidgets.QPushButton('Check plate cuts in CAD');layout.addWidget(self.check_button)
        self.add_button.clicked.connect(self.add_pattern);self.apply_button.clicked.connect(self.apply_pattern);self.remove_button.clicked.connect(self.remove_pattern);self.copy_button.clicked.connect(self.copy_camera)
        self.pattern_list.currentRowChanged.connect(self.select_pattern);self.role.currentIndexChanged.connect(self.update_coordinates)
        self.check_button.clicked.connect(self.check_cad);self.update_coordinates()
        self._draft_baseline=self.draft()
        for control in (self.role,self.shape,self.mode):control.currentIndexChanged.connect(self.update_pending_status)
        self.enabled.toggled.connect(self.update_pending_status)
        for control in self.inputs.values():control.valueChanged.connect(self.update_pending_status)
        self.update_capacity();self.filter_patterns()

    def update_coordinates(self,*args):
        camera=self.role.currentData() in CAMERA_ROLES
        self.coordinates.setText('U = Y offset from nominal camera centre. V = height above bottom plate upper face. Width is along U; length is along V.' if camera else
                                 'U = frame X (right). V = frame Y (front). The grid is centred here; rotation turns both cuts and grid. Circle uses width as diameter.')
        self.copy_button.setEnabled(camera);self.preview.fit_plate()

    def draft(self):
        return dict(mode=self.mode.currentText(),role=self.role.currentData(),shape=self.shape.currentText(),enabled=self.enabled.isChecked(),**{k:c.value() for k,c in self.inputs.items()})

    def update_capacity(self):
        enabled=sum(p['columns']*p['rows'] for p in self.patterns if p['enabled'])
        self.capacity.setText(f'Saved patterns: {len(self.patterns)} / {MAX_PATTERNS}   |   Enabled cuts: {enabled} / {MAX_ENABLED_CUTOUTS}')

    def has_pending_changes(self):
        return self.draft()!=getattr(self,'_draft_baseline',self.draft())

    def update_pending_status(self,*args):
        if hasattr(self,'status') and self.has_pending_changes():
            self.status.setStyleSheet('color: #a45b00; font-weight: bold;')
            self.status.setText('Unapplied pattern changes. Press Add pattern to add a new cut, or Apply to pattern to replace the selected cut. Then check or update the frame.')

    def show_error(self,message):
        self.status.setStyleSheet('color: #b43737; font-weight: bold;')
        self.status.setText(message)
        QtWidgets.QMessageBox.warning(self,'Cutout pattern not saved',message)

    def discard_changes(self):
        p=dict(self._draft_baseline)
        self.mode.setCurrentText(p['mode']);self.role.setCurrentIndex(CUTOUT_ROLES.index(p['role']))
        self.shape.setCurrentText(p['shape']);self.enabled.setChecked(p['enabled'])
        for k,c in self.inputs.items():c.setValue(p[k])
        self._draft_baseline=self.draft();self.status.setStyleSheet('')
        self.status.setText('Unapplied edits discarded. Saved patterns are unchanged.');self.preview.update()

    def require_applied(self):
        if self.has_pending_changes():
            self.show_error('The pattern controls have unapplied changes. Press Add pattern for a new cut, or Apply to pattern for the selected cut, before checking, saving or building the frame. Use Discard unapplied changes to keep the saved patterns.')
            return False
        return True

    def publish(self,select=-1):
        try:value=encode_patterns(self.patterns)
        except ValueError as exc:self.show_error(str(exc));return False
        self.patterns=parse_patterns(value);self.pattern_list.blockSignals(True);self.pattern_list.clear()
        for i,p in enumerate(self.patterns):
            item=QtWidgets.QListWidgetItem(self.pattern_text(i));item.setToolTip(self.pattern_text(i)+'\nRotation '+str(p['rotation'])+' degrees; grid '+str(p['columns'])+' x '+str(p['rows'])+'; pitch '+str(p['pitch_x'])+' / '+str(p['pitch_y'])+' mm')
            self.pattern_list.addItem(item)
        self._selected_index=-1
        self.pattern_list.setCurrentRow(select);self.pattern_list.blockSignals(False)
        if select>=0:self.select_pattern(select,force=True)
        self.filter_patterns()
        self._draft_baseline=self.draft();self.update_capacity();self.status.setStyleSheet('')
        self.changed.emit(value);self.preview.update();self.status.setText('Pattern saved. Full CAD checks run on Create / Update, or use Check plate cuts in CAD.');return True

    def set_json(self,value):
        self.patterns=parse_patterns(value);self.publish()

    def pattern_text(self,index):
        p=self.patterns[index]
        size=f"Ø{p['width']:g} mm" if p['shape']=='Circle' else f"{p['width']:g} × {p['length']:g} mm"
        return f"#{index+1} · {ROLE_LABELS[p['role']]} · {p['mode']} · {p['columns']*p['rows']} × {p['shape']} · {size} · ({p['x']:g}, {p['y']:g})"+(' [off]' if not p['enabled'] else '')

    def filter_patterns(self,*args):
        tokens=self.find_pattern.text().casefold().split();role=self.filter_role.currentData();shown=0
        for i,p in enumerate(self.patterns):
            match=(not role or p['role']==role) and all((token=='#'+str(i+1)) if token.startswith('#') and token[1:].isdigit() else (token in self.pattern_text(i).casefold() or token.replace('×','x') in self.pattern_text(i).casefold().replace('×','x').replace(' ','')) for token in tokens)
            self.pattern_list.item(i).setHidden(not match);shown+=int(match)
        selected=self._selected_index
        suffix=(' · Selected #'+str(selected+1)+(' (hidden by filter)' if self.pattern_list.item(selected).isHidden() else '')) if 0<=selected<len(self.patterns) else ''
        self.filter_count.setText(str(shown)+' of '+str(len(self.patterns))+' patterns shown'+suffix)
        self.zoom_button.setEnabled(selected>=0 and not self.pattern_list.item(selected).isHidden())
        self.apply_button.setText('Apply to #'+str(selected+1) if selected>=0 else 'Apply to pattern')
        self.remove_button.setText('Remove #'+str(selected+1) if selected>=0 else 'Remove')
        self.preview.update()

    def choose_pattern(self,index):
        if index<0 or index>=len(self.patterns):return False
        if index!=self._selected_index and self.has_pending_changes():
            self.status.setText('Apply or discard your unapplied changes before selecting another pattern.');return False
        self.pattern_list.setCurrentRow(index);self.pattern_list.scrollToItem(self.pattern_list.item(index))
        return self._selected_index==index

    def select_pattern(self,index,force=False):
        if index<0 or index>=len(self.patterns):return False
        if not force and index==self._selected_index:return True
        if not force and self.has_pending_changes():
            self.pattern_list.blockSignals(True);self.pattern_list.setCurrentRow(self._selected_index);self.pattern_list.blockSignals(False)
            self.status.setText('Apply or discard your unapplied changes before selecting another pattern.');return False
        self._selected_index=index
        p=self.patterns[index];self.mode.setCurrentText(p['mode']);self.role.setCurrentIndex(CUTOUT_ROLES.index(p['role']));self.shape.setCurrentText(p['shape']);self.enabled.setChecked(p['enabled'])
        for k,c in self.inputs.items():c.setValue(p[k])
        self._draft_baseline=self.draft();self.status.setStyleSheet('');self.status.setText('Selected #'+str(index+1)+'. Edit and press Apply to pattern, or Add pattern for a new cut.')
        self.filter_patterns();self.preview.update();return True

    def add_pattern(self,*args):
        old=list(self.patterns);self.patterns.append(self.draft())
        if not self.publish(len(self.patterns)-1):self.patterns=old

    def apply_pattern(self,*args):
        index=self._selected_index
        if index<0:self.status.setText('Select a saved pattern first, or press Add pattern.');return
        old=list(self.patterns);self.patterns[index]=self.draft()
        if not self.publish(index):self.patterns=old

    def remove_pattern(self,*args):
        index=self._selected_index
        if index>=0:self.patterns.pop(index);self.publish(min(index,len(self.patterns)-1))

    def copy_camera(self,*args):
        pattern=self.draft();pattern['role']='CameraMountRight' if pattern['role']=='CameraMountLeft' else 'CameraMountLeft'
        old=list(self.patterns);self.patterns.append(pattern)
        if not self.publish(len(self.patterns)-1):self.patterns=old

    def check_cad(self,*args):
        if not self.require_applied():return
        from .geometry import build_shapes,invalidate_failed_build
        invalidate_failed_build(self.get_parameters())
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            build_shapes(self.get_parameters());self.status.setText('CAD passed: each active part is connected; interior cuts preserve edge clearance and all cuts preserve fasteners and existing holes.')
        except Exception as exc:self.status.setText(str(exc))
        finally:QtWidgets.QApplication.restoreOverrideCursor()


_BLEND_PATH_CACHE={}

def blend_motor_junction_path(p,arm,path):
    if p.MotorPadBlendRadius<=1e-8 or abs(p.MotorPadRotation)<1e-8:return path
    key=(p.signature(),arm.get('name'),arm['root'],arm['motor'])
    if key in _BLEND_PATH_CACHE:return QtGui.QPainterPath(_BLEND_PATH_CACHE[key])
    # Flatten only the outer contour at 1/4 mm drawing tolerance; round inward
    # polygon junctions directly rather than stroking a large complementary area.
    transform=QtGui.QTransform();transform.scale(4,4)
    polygons=path.toSubpathPolygons(transform)
    def signed_area(poly):return sum(poly[i].x()*poly[(i+1)%len(poly)].y()-poly[(i+1)%len(poly)].x()*poly[i].y() for i in range(len(poly)))/2
    polygon=max(polygons,key=lambda poly:abs(signed_area(poly)))
    points=[(pt.x()/4,pt.y()/4) for pt in polygon]
    if math.dist(points[0],points[-1])<1e-8:points.pop()
    orientation=1 if signed_area(polygon)>0 else -1
    result=QtGui.QPainterPath();corners=[]
    ux,uy=motor_pad_unit(p,arm);mx,my=arm['motor']
    for i,b in enumerate(points):
        a,c=points[i-1],points[(i+1)%len(points)]
        l1,l2=math.dist(a,b),math.dist(b,c)
        if min(l1,l2)<1e-8:corners.append((b,b,None));continue
        u=((b[0]-a[0])/l1,(b[1]-a[1])/l1);v=((c[0]-b[0])/l2,(c[1]-b[1])/l2)
        cross=u[0]*v[1]-u[1]*v[0];angle=math.acos(max(-1.,min(1.,u[0]*v[0]+u[1]*v[1])))
        localx=(b[0]-mx)*ux+(b[1]-my)*uy
        if orientation*cross>=-1e-5 or angle<.12 or localx>p.ArmWidth or math.dist(b,arm['motor'])>p.MotorPadDiameter+p.ArmWidth:
            corners.append((b,b,None));continue
        d=min(p.MotorPadBlendRadius*math.tan(angle/2),.45*l1,.45*l2)
        radius=d/max(1e-10,math.tan(angle/2))
        first=(b[0]-d*u[0],b[1]-d*u[1]);last=(b[0]+d*v[0],b[1]+d*v[1])
        centre=(first[0]+orientation*u[1]*radius,first[1]-orientation*u[0]*radius)
        corners.append((first,last,(centre,radius)))
    result.moveTo(*corners[0][0])
    for first,last,arc in corners:
        result.lineTo(*first)
        if arc:
            centre,radius=arc;a=math.atan2(first[1]-centre[1],first[0]-centre[0]);b=math.atan2(last[1]-centre[1],last[0]-centre[0]);sweep=(b-a)%(2*math.pi)
            if orientation>0:sweep-=2*math.pi
            for j in range(1,9):
                t=a+sweep*j/8;result.lineTo(centre[0]+radius*math.cos(t),centre[1]+radius*math.sin(t))
        else:result.lineTo(*last)
    result.closeSubpath();result=path.united(result)
    if len(_BLEND_PATH_CACHE)>=32:_BLEND_PATH_CACHE.clear()
    _BLEND_PATH_CACHE[key]=QtGui.QPainterPath(result)
    return result

ROLE_LABELS.update({**{'MotorProtector'+name:'Motor protector '+name for name in ('FrontRight','FrontLeft','RearLeft','RearRight')},'ElectronicsGuardLeft':'Electronics guard left','ElectronicsGuardRight':'Electronics guard right'})
