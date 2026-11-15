"""Cage layout and material selection without CAD imports."""
import math

def cage_active(p):return p.FPVEnabled and p.CameraCageStyle=='TPU cage'
def camera_thickness(p):
    return p.CameraBracketThickness

def screw_cage(p):return p.CameraCageStyle=='TPU cage'
def cage_density(p):return p.FlexDensity if p.CameraCageStyle=='TPU cage' else p.CarbonDensity

def shaped_wall(p,profile):
    if not p.FPVEnabled or p.CameraCageStyle=='TPU cage':return profile
    if p.CameraCageFrontShape==p.CameraCageRearShape=='Straight':return profile
    br,bf,tf,tr=profile
    def edge(a,b,style):
        points=[]
        for i in range(17):
            t=i/16
            depth=0 if style=='Straight' else math.sin(math.pi*t) if style=='Rounded waist' else 1-abs(2*t-1) if style=='Faceted waist' else 4*t*(1-t)*(1.25-.5*t)
            front=a==bf;sign=-1 if front else 1;amount=p.CameraCageProfileDepth
            if style in ('Rounded extension','Faceted extension','Swept extension','Full extension'):
                depth=(math.sin(math.pi*t) if style=='Rounded extension' else 1-abs(2*t-1) if style=='Faceted extension' else 4*t*(1-t)*(1.25-.5*t) if style=='Swept extension' else min(1.,t*4,(1-t)*4))
                amount=-(p.CameraCageFrontReach if front else p.CameraCageRearReach)
            points.append((a[0]+(b[0]-a[0])*t+sign*amount*depth,a[1]+(b[1]-a[1])*t))
        return points
    return tuple([br]+edge(bf,tf,p.CameraCageFrontShape)+edge(tr,br,p.CameraCageRearShape)[:-1])

def validate_cage(p):
    if not p.FPVEnabled:return []
    errors=[]
    limits={'CameraCageProfileDepth':(0,8),'CameraCageFrontReach':(0,25),'CameraCageRearReach':(0,25),'CameraCageEdgeWeb':(2,12),'CameraTPUBridge':(1,5),'CameraTPUHardClearance':(0.05,3),'CameraTPUFrontBridgeRearReach':(1,15),'CameraTPUFrontBridgeHeight':(1,8),'CameraTPUFrontBridgeBlend':(0,10),'CameraTPUBottomRearReach':(4,40),'CameraTPUTopRearReach':(4,40),'CameraTPUScrewBore':(3,6),'CameraTPUInsertDepth':(2,8),'CameraTPUBossWall':(1,4),'O4InsertDiameter':(4,9),'O4PadDiameter':(4,10),'CameraTPUInnerReach':(0,30),'CameraTPUClampFit':(0,1),'CameraTPUClampWall':(.8,4),'CameraTPUBumperReach':(.8,10),'CameraTPUBumperWidth':(0,5),'CameraTPUBumperToe':(0,15),'CameraTPUScrewClearance':(0,1)}
    for name,(lo,hi) in limits.items():
        value=getattr(p,name)
        if not math.isfinite(value) or not lo<=value<=hi:errors.append(f'{name} must be {lo}–{hi}.')
    if screw_cage(p) and p.StandoffHeight<2*(p.CameraTPUInsertDepth+1):errors.append('Top and bottom insert pockets need separate blind ends; increase cage height or reduce insert depth.')
    return errors

def joined_cage(p):return p.FPVEnabled and p.CameraCageStyle=='TPU cage'
def active_camera_roles(p):
    if not p.FPVEnabled:return ()
    return ('CameraMountLeft',) if joined_cage(p) else ('CameraMountLeft','CameraMountRight')
def boss_x(p,sign):
    if screw_cage(p):
        from .tpu_mount_layout import mounting_x
        return sign*mounting_x(p)
    return sign*(p.CameraWidth/2+p.CameraSideClearance/2)
