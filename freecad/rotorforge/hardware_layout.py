"""Portable placement rules for assembly aids; no CAD or editor dependencies."""
import math
from .parameters import (arm_layouts,plate_levels,standoff_layouts,stack_holes,stack_reference_z,
                         stack_mounting_role,three_plate,arm_braces,underside_clamp_active)
from .fpv import camera_mounts,camera_screw_offsets,camera_position_y,camera_pivot_height,camera_body_centre,vtx_holes,vtx_deck_z

HARDWARE_GROUPS=('Arm bolts','Motor screws','Standoff screws','Stack hardware','Camera screws','VTX hardware')
SIZES={1.4:(2.6,1.4,3.2,.3,3.2,1.2),1.6:(3.,1.6,4.,.3,3.2,1.3),2.:(3.8,2.,5.,.3,4.,1.6),2.5:(4.5,2.5,6.,.5,5.,2.),3.:(5.5,3.,7.,.5,5.5,2.4),4.:(7.,4.,9.,.8,7.,3.2)}
DEFAULT_OPTIONS=dict(groups=list(HARDWARE_GROUPS),nuts=True,engagement=3.)

def metric_size(hole):
    """Use a nominal diameter below a clearance bore; never enlarge the hole."""
    return max((d for d in SIZES if d<=hole+.001),default=1.4)

def hardware_layout(p,options=None):
    o=dict(DEFAULT_OPTIONS,**(options or {}));eng=float(o['engagement'])
    if not math.isfinite(eng) or not .5<=eng<=10:raise ValueError('Thread engagement must be between 0.5 and 10 mm.')
    levels=plate_levels(p);az=levels['arm_z'];stands=standoff_layouts(p);result=[]
    def add(group,name,point,axis,hole,length,owner,nut=False):
        if group not in o['groups']:return
        d=metric_size(hole);hd,hh,wd,wt,nw,nh=SIZES[d]
        # Point is the supporting face; the round head sits outside the joint.
        result.append(dict(group=group,name=name,point=tuple(point),axis=tuple(axis),diameter=d,
                           length=max(length,d),nut=bool(nut and (o['nuts'] or group=='Stack hardware')),
                           nut_distance=length-nh if nut else 0.,owner=owner))
    rootbottom=min(0.,az)- (p.UndersideClampThickness if underside_clamp_active(p) else 0.)
    roottop=levels['mid_z']+p.ClampThickness if three_plate(p) else (levels['stack_deck_z'] if arm_braces(p) else max(p.BottomThickness,az+p.ArmThickness))
    for a in arm_layouts(p):
        role='Arm'+a['name']
        for i,pt in enumerate(a['bolts']):
            if any(math.dist(pt,s['point'])<1e-5 and s['shared_arm'] for s in stands):continue
            from .nut_seats import joint_seat
            seat=joint_seat(p,'Arm bolts',pt);d=metric_size(p.RootHoleDiameter);nh=SIZES[d][5]
            face=seat['z'];axis=seat['axis'];press=p.ArmNutMount=='M3 press nut';depth=seat['depth']
            start=rootbottom if axis>0 else max(p.BottomThickness,az+p.ArmThickness)
            length=abs(face-start)+(p.PressNutFlangeHeight-p.PressNutFlangeRecess if press else nh-depth)
            add('Arm bolts',f'{a["name"]} root {i+1}',(*pt,start),(0,0,axis),p.RootHoleDiameter,length,role,True)
            if result and result[-1]['name']==f'{a["name"]} root {i+1}':result[-1].update(seat=seat,press=press)
        for i,pt in enumerate(a['motor_holes']):add('Motor screws',f'{a["name"]} motor {i+1}',(*pt,az),(0,0,1),p.MotorHoleDiameter,p.ArmThickness+eng,role)
    for i,s in enumerate(stands):
        add('Standoff screws',f'{s["position"]} {i+1} top',(*s['point'],levels['top_z']+p.TopThickness),(0,0,-1),p.StandoffHoleDiameter,p.TopThickness+min(eng,s['length']/2),'TopPlate')
        # Shared bolts pass through the complete arm sandwich into the standoff.
        bottom=rootbottom if s['shared_arm'] else s['base']-(p.ClampThickness if s['mount']=='Mid plate' else p.ArmBraceThickness if s['mount']=='Arm clamp plate' else p.BottomThickness)
        add('Standoff screws',f'{s["position"]} {i+1} base',(*s['point'],bottom),(0,0,1),p.StandoffHoleDiameter,s['base']-bottom+min(eng,s['length']/2),'MidPlate' if s['mount']=='Mid plate' else 'ArmClampPlate' if s['mount']=='Arm clamp plate' else 'BottomPlate')
    carrier=stack_mounting_role(p);deck=levels['stack_deck_z']
    thick=p.ClampThickness if carrier=='MidPlate' else p.ArmBraceThickness if carrier=='ArmClampPlate' else p.BottomThickness
    for i,pt in enumerate(stack_holes(p)):
        d=metric_size(p.StackHoleDiameter)
        start=deck-thick
        length=stack_reference_z(p)+p.StackHeight+SIZES[d][5]-start
        add('Stack hardware',f'Stack {i+1}',(*pt,start),(0,0,1),p.StackHoleDiameter,length,carrier,True)
        if p.StackPressNuts and result and result[-1]['name']==f'Stack {i+1}':
            from .nut_seats import joint_seat
            result[-1].update(seat=joint_seat(p,'Stack hardware',pt),press=True)
    if p.FPVEnabled:
        cy,cz=camera_body_centre(p)
        for m in camera_mounts(p):
            sign=-1 if m['role'].endswith('Left') else 1;x=m['plate_x'][0 if sign<0 else 1]
            from .camera_interface import lip_sides
            if p.FlexCameraMode=='Captured inserts' and lip_sides(p)[1]:x+=sign*max(.8,p.FlexPadThickness/2)
            for i,(dy,dz) in enumerate(camera_screw_offsets(p,p.CameraTilt)):
                add('Camera screws',f'{m["role"]} {i+1}',(x,cy+dy,cz+dz),(-sign,0,0),p.CameraSideHoleDiameter,abs(x)-p.CameraWidth/2+eng,m['role'])
        deck=vtx_deck_z(p);thick=p.ClampThickness if three_plate(p) else p.BottomThickness
        for i,(pt,r,_) in enumerate(vtx_holes(p)[:4]):
            add('VTX hardware',f'VTX {i+1}',(*pt,deck-thick),(0,0,1),2*r,thick+eng,'MidPlate' if three_plate(p) else 'BottomPlate',False)
    return result
