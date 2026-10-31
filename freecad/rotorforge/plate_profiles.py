"""Tapered centre widening shared by CAD, validation and editor previews."""
import math

CENTRE_WIDTH_FIELDS = {'BottomPlate':'BottomCentreWidth', 'MidPlate':'MidCentreWidth',
                       'TopPlate':'TopCentreWidth', 'ArmClampPlate':'ClampCentreWidth', 'ArmLowerClampPlate':'ClampCentreWidth'}


def centre_width_at(p, role, y, base_width):
    wide=getattr(p,CENTRE_WIDTH_FIELDS[role])
    if wide<=base_width:return base_width
    distance=abs(y-p.CentreSectionY)-p.CentreSectionLength/2
    if distance<=0:return wide
    if distance>=p.CentreShoulderLength:return base_width
    return base_width+(wide-base_width)*(1-distance/p.CentreShoulderLength)


def centre_polygon(p, role, base_width, rear, front, wide_override=None):
    wide=getattr(p,CENTRE_WIDTH_FIELDS[role]) if wide_override is None else wide_override
    if wide<=base_width:return ()
    low=p.CentreSectionY-p.CentreSectionLength/2
    high=p.CentreSectionY+p.CentreSectionLength/2
    shoulder=p.CentreShoulderLength
    points=[(-base_width/2,low-shoulder),(-wide/2,low),(-wide/2,high),(-base_width/2,high+shoulder),
            (base_width/2,high+shoulder),(wide/2,high),(wide/2,low),(base_width/2,low-shoulder)]
    # Clip axially, preserving exact front/rear reach in every mode.
    for bound,sign in ((rear,1),(front,-1)):
        clipped=[]
        if not points:return ()
        for a,b in zip(points,points[1:]+points[:1]):
            inside_a=sign*(a[1]-bound)>=0;inside_b=sign*(b[1]-bound)>=0
            if inside_a:clipped.append(a)
            if inside_a!=inside_b:
                t=(bound-a[1])/(b[1]-a[1]);clipped.append((a[0]+t*(b[0]-a[0]),bound))
        points=clipped
    unique=[]
    for point in points:
        if not unique or math.dist(point,unique[-1])>1e-9:unique.append(point)
    if len(unique)>1 and math.dist(unique[0],unique[-1])<1e-9:unique.pop()
    return tuple(unique) if len(unique)>=3 else ()


def polygon_interior_distance(point, points):
    if not points:return -float('inf')
    signs=[];distances=[]; inside=False
    for a,b in zip(points,points[1:]+points[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1];length2=dx*dx+dy*dy
        if length2<1e-18:continue
        if (a[1]>point[1]) != (b[1]>point[1]) and point[0] < a[0]+(point[1]-a[1])*dx/dy:inside=not inside
        signs.append(dx*(point[1]-a[1])-dy*(point[0]-a[0]))
        t=max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/length2))
        distances.append(math.hypot(point[0]-a[0]-t*dx,point[1]-a[1]-t*dy))
    return min(distances)*(1 if inside else -1)


def profiled_interior_distance(point,p,role,width,rear,front,radius):
    qx=abs(point[0])-(width/2-radius)
    qy=abs(point[1]-(rear+front)/2)-((front-rear)/2-radius)
    base=radius-math.hypot(max(qx,0),max(qy,0))-min(max(qx,qy),0)
    outline=plate_base_polygon(p,role,width,rear,front,radius)
    if outline:base=polygon_interior_distance(point,outline)
    inside=max(base,polygon_interior_distance(point,centre_polygon(p,role,width,rear,front)))
    from .bottom_nose import edge_polygon
    for end in ('Front','Rear'):
        mask=edge_polygon(p,role,end,width,rear,front)
        if mask:inside=min(inside,polygon_interior_distance(point,mask))
    return inside


def plate_base_polygon(p,role,width,rear,front,radius):
    field={'BottomPlate':'BottomPlateShape','MidPlate':'MidPlateShape','TopPlate':'TopPlateShape','ArmClampPlate':'ClampPlateShape','ArmLowerClampPlate':'ClampPlateShape'}[role]
    name=getattr(p,field);h=width/2; t=h*p.PlateEndWidth/100
    if name=='Rounded rectangle':return ()
    c=min(radius,h*.9,(front-rear)*.25)
    if name=='Octagonal':c=min(width*.16,(front-rear)*.16)
    if name in ('Chamfered rectangle','Octagonal'):
        return ((-h+c,rear),(h-c,rear),(h,rear+c),(h,front-c),(h-c,front),(-h+c,front),(-h,front-c),(-h,rear+c))
    if name=='Tapered front':return ((-h,rear),(h,rear),(t,front),(-t,front))
    if name=='Tapered rear':return ((-t,rear),(t,rear),(h,front),(-h,front))
    mid=(rear+front)/2
    if name=='Hexagonal':return ((-t,rear),(t,rear),(h,mid),(t,front),(-t,front),(-h,mid))
    shoulder=rear+(front-rear)*.68
    return ((-h,rear),(h,rear),(h,shoulder),(t,front),(-t,front),(-h,shoulder))
