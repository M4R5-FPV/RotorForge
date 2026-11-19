"""Independent flush-head machining for plate standoffs and TPU cage fasteners.

Coordinates always describe the real exposed bearing surface, not an
intermediate layer through which the screw merely passes. Geometry and
hardware references share the same head dimensions and datums.
"""
import math

HEAD_FIELDS = {'TopPlate':'StandoffTopHead', 'MidPlate':'StandoffMidHead',
               'BottomPlate':'StandoffBottomHead'}
MIN_REMAINING = .5


def standoff_head(p, role):
    field = HEAD_FIELDS.get(role)
    if role=='ArmClampPlate':field=HEAD_FIELDS['MidPlate']
    elif role=='ArmLowerClampPlate' or (role.startswith('Arm') and role not in ('ArmClampPlate','ArmKeystone')):field=HEAD_FIELDS['BottomPlate']
    return getattr(p,field) if field else 'Round head'


def standoff_base(p, stand):
    """Return physical head-bearing component, surface Z, and thickness."""
    from .parameters import plate_levels, underside_clamp_active
    if stand['shared_arm']:
        az = plate_levels(p)['arm_z']
        if underside_clamp_active(p):
            return 'ArmLowerClampPlate',min(0.,az)-p.UndersideClampThickness,p.UndersideClampThickness
        if az < 0.:
            return 'Arm'+stand['shared_arm']['arm'],az,p.ArmThickness
        return 'BottomPlate',0.,p.BottomThickness
    if stand['mount']=='Mid plate':
        return 'MidPlate',stand['base']-p.ClampThickness,p.ClampThickness
    if stand['mount']=='Arm clamp plate':
        return 'ArmClampPlate',stand['base']-p.ArmBraceThickness,p.ArmBraceThickness
    return 'BottomPlate',stand['base']-p.BottomThickness,p.BottomThickness


def arm_bolt_base(p,arm,point):
    """Physical bearing face of a non-shared arm bolt, opposite its nut."""
    from .parameters import plate_levels, underside_clamp_active
    from .nut_seats import joint_seat
    az=plate_levels(p)['arm_z']; axis=joint_seat(p,'Arm bolts',point)['axis']
    if axis<0:
        return 'Arm'+arm['name'],az+p.ArmThickness,p.ArmThickness,axis
    if underside_clamp_active(p):
        return 'ArmLowerClampPlate',min(0.,az)-p.UndersideClampThickness,p.UndersideClampThickness,axis
    if az<0.:
        return 'Arm'+arm['name'],az,p.ArmThickness,axis
    return 'BottomPlate',0.,p.BottomThickness,axis


def head_dimensions(nominal, bore):
    """90-degree nominal flush head (diameter = 2*d) plus 0.1 mm diametral fit."""
    outer=2.*nominal+.1
    return outer,(outer-bore)/2.


def countersink_specs(p, role=None):
    """Portable machining data for actual screw heads; nothing on motor pads."""
    if role is not None and role not in (*HEAD_FIELDS,'ActionCameraMount','ArmClampPlate','ArmLowerClampPlate','ArmFrontLeft','ArmFrontRight','ArmRearLeft','ArmRearRight'):
        return ()
    from .parameters import plate_levels, standoff_layouts, plate_holes, arm_layouts
    from .hardware_layout import metric_size
    items=[]
    def add(r,pt,z,axis,thickness,bore,d,label):
        diameter,depth=head_dimensions(d,bore)
        items.append(dict(role=r,point=tuple(pt),z=z,axis=axis,thickness=thickness,
                          bore=bore,nominal=d,head_diameter=diameter,depth=depth,label=label))
    if role!='ActionCameraMount' and any(standoff_head(p,r)=='Countersunk' for r in HEAD_FIELDS):
        levels=plate_levels(p);stands=standoff_layouts(p)
        def enabled(r):return (role is None or r==role) and standoff_head(p,r)=='Countersunk'
        for stand in stands:
            pt=stand['point'];nominal=metric_size(p.StandoffHoleDiameter)
            if enabled('TopPlate'):
                add('TopPlate',pt,levels['top_z']+p.TopThickness,-1,p.TopThickness,p.StandoffHoleDiameter,nominal,'Standoff screw')
            r,z,t=standoff_base(p,stand)
            if enabled(r):
                # Arms have their own root pattern, not the plate hole list.
                actual=p.RootHoleDiameter if r.startswith('Arm') and r not in ('ArmClampPlate','ArmLowerClampPlate') else max((2*radius for point,radius,_ in plate_holes(p,r) if math.dist(pt,point)<1e-6),default=p.StandoffHoleDiameter)
                add(r,pt,z,1,t,actual,nominal,'Standoff screw')
        for arm in arm_layouts(p):
            for pt in arm['bolts']:
                if any(s['shared_arm'] and math.dist(pt,s['point'])<1e-5 for s in stands):continue
                r,z,t,axis=arm_bolt_base(p,arm,pt)
                if enabled(r):
                    add(r,pt,z,axis,t,p.RootHoleDiameter,metric_size(p.RootHoleDiameter),'Arm bolt')
    if (role is None or role in ('TopPlate','BottomPlate','ActionCameraMount')) and p.CameraCageScrewHead=='Countersunk' and p.FPVEnabled and p.CameraCageStyle=='TPU cage':
        from .fpv import camera_slots
        from .action_camera_mount import upper_cage_screw_lift
        top=plate_levels(p)['top_z']+p.TopThickness
        lift=upper_cage_screw_lift(p)
        targets=(('BottomPlate',0.,1,p.BottomThickness,'BottomPlate',3.2),
                 ('ActionCameraMount' if lift else 'TopPlate',top+lift,-1,lift or p.TopThickness,'TopPlate',3.3 if lift else 3.2))
        for r,z,axis,t,source,bore in targets:
            if role is not None and role!=r:continue
            for a,b,_ in camera_slots(p,source):
                if math.dist(a,b)>1e-6:raise ValueError('TPU cage screws require round mounting holes.')
                add(r,a,z,axis,t,bore,3.,'TPU cage screw')
    return tuple(items)


def validate_heads(p):
    errors=[]
    try:items=countersink_specs(p)
    except (ValueError,ArithmeticError) as exc:return [str(exc)]
    for item in items:
        if item['depth']<=0:
            msg=f"{item['role']}: countersunk screw head is too small for the through-hole; select Round head."
        elif item['thickness']-item['depth']<MIN_REMAINING-1e-7:
            msg=f"{item['role']}: countersink needs {item['depth']+MIN_REMAINING:.2f} mm thickness to retain at least {MIN_REMAINING:g} mm below its widest taper; increase thickness or select Round head."
        else:continue
        if msg not in errors:errors.append(msg)
    return errors


def _seat_tools(item):
    import FreeCAD as App
    import Part
    x,y=item['point'];z=item['z'];axis=item['axis'];d=item['depth'];r=item['bore']/2
    # Exact face-to-depth frustum. Only the cut tool protrudes beyond the face;
    # the refill tool must never add material outside the original stock.
    direction=App.Vector(0,0,axis)
    exact=Part.makeCone(item['head_diameter']/2,r,d,App.Vector(x,y,z),direction)
    cut=Part.makeCone(item['head_diameter']/2+.02,r,d+.02,App.Vector(x,y,z-axis*.02),direction)
    bore=Part.makeCylinder(r,d+.2,App.Vector(x,y,z-axis*.1),direction)
    annulus=exact.cut(bore)
    return cut,annulus


def apply_countersinks(shape,p,role):
    for item in countersink_specs(p,role):
        if item['depth']<=0 or item['thickness']-item['depth']<MIN_REMAINING-1e-7:
            raise ValueError(role+': unsafe countersink depth or diameter; choose Round head or increase plate thickness.')
        cut,annulus=_seat_tools(item)
        # Reject any seat that opens into an edge, another cut, or a clearance
        # pocket. Never silently make a partial countersink with missing support.
        if annulus.cut(shape).Volume>max(1e-5,annulus.Volume*1e-5):
            raise ValueError(f"{role}: {item['label']} countersink at {item['point']} lacks continuous seating material. Move the opening, widen the plate or select Round head.")
        shape=shape.cut(cut).removeSplitter()
        if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1:
            raise ValueError(role+': countersink did not produce a valid connected solid.')
    return shape


def restore_countersinks(shape,p,role):
    """Recover through-hole geometry for flat cutting profiles only."""
    for item in countersink_specs(p,role):
        if role=='ActionCameraMount':continue
        _,annulus=_seat_tools(item)
        shape=shape.fuse(annulus).removeSplitter()
        if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1:
            raise ValueError(role+': could not recover the through-cut outline from a countersink.')
    return shape
