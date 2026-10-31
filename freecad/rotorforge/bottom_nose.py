"""Plate end profiles shared by CAD, Qt and portable support checks."""
from .parameter_memo import parameter_cache
NOSE_SHAPES=('Straight','Rounded nose','Pointed nose','Flat-tip nose','Swept shoulders','Concave nose','V-notch','Twin lobes','Stepped nose','Shallow W','Triple scallop','Arrowhead','Flat recess','Round U recess')

CAMERA_FRONT_SHAPES=('Camera U recess','Camera flared recess','Camera swept recess','Camera crescent','Camera stepped recess','Camera chamfered recess')
TOP_FRONT_SHAPES=('Straight',)+CAMERA_FRONT_SHAPES+NOSE_SHAPES[1:]

def camera_recess_width(p):
 return p.TopFrontRecessWidth or p.CameraWidth+2*p.TopFrontClearance

REAR_FRONT_MAP={name.replace('nose','end'):name for name in NOSE_SHAPES}
REAR_SHAPES=tuple(REAR_FRONT_MAP)+('Cable channel','Dual cable channels','Split tail','Stepped electronics tail')
REAR_FIELDS={'BottomPlate':'BottomRear','MidPlate':'MidRear','TopPlate':'TopRear'}

def edge_settings(p,role,end):
 if end=='Front':
  if role=='TopPlate':return p.TopFrontShape,p.TopFrontDepth,p.TopFrontTipWidth
  return (p.BottomNoseShape,p.BottomNoseDepth,p.BottomNoseTipWidth) if role=='BottomPlate' else ('Straight',0.,35.)
 if role not in REAR_FIELDS:return 'Straight',0.,35.
 from .parameters import three_plate
 if role=='BottomPlate' and three_plate(p) or role=='MidPlate' and not three_plate(p):return 'Straight',0.,35.
 prefix=REAR_FIELDS[role]
 return getattr(p,prefix+'Shape'),getattr(p,prefix+'Depth'),getattr(p,prefix+'TipWidth')

@parameter_cache(maxsize=128)
def edge_commands(p,role,end,width,rear,front):
 shape,depth,tip_width=edge_settings(p,role,end)
 if shape=='Straight':return ()
 reverse=end=='Rear'
 shape=REAR_FRONT_MAP.get(shape,shape)
 if reverse:rear,front=-front,-rear
 from .plate_profiles import centre_width_at
 d=max(0.,depth);f=front;k=.5522847498307936
 from .parameters import CENTRE_WIDTH_FIELDS
 outer=max(width,getattr(p,CENTRE_WIDTH_FIELDS[role]))/2
 camera=role=='TopPlate' and end=='Front' and shape in CAMERA_FRONT_SHAPES
 if camera:f-=p.TopFrontSetback
 centre=-p.CentreSectionY if reverse else p.CentreSectionY
 stations=(f-d,f,max(f-d,min(f,centre)))
 h=max(centre_width_at(p,role,-y if reverse else y,width) for y in stations)/2
 tip=h*tip_width/100
 if camera:half=camera_recess_width(p)/2
 start=(-h,f-d);commands=[]
 def line(x,y):commands.append(('L',(x,y)))
 def cubic(a,b,c):commands.append(('C',a,b,c))
 if camera:
  start=(-h,f)
  if shape=='Camera U recess':
   radius=min(2.,half/2,d/2);left=-half;right=half
   line(left,f);line(left,f-d+radius)
   cubic((left,f-d+radius-k*radius),(left+radius-k*radius,f-d),(left+radius,f-d))
   line(right-radius,f-d)
   cubic((right-radius+k*radius,f-d),(right,f-d+radius-k*radius),(right,f-d+radius))
   line(right,f)
  elif shape=='Camera flared recess':
   mouth=min(h,half*1.2)
   for pt in ((-mouth,f),(-half*.7,f-d),(half*.7,f-d),(mouth,f)):line(*pt)
  elif shape=='Camera swept recess':
   mouth=min(h,half*1.2);bottom=half*.65
   line(-mouth,f)
   cubic((-half*.85,f),(-half,f-d),(-bottom,f-d));line(bottom,f-d)
   cubic((half,f-d),(half*.85,f),(mouth,f))
  elif shape=='Camera crescent':
   line(-half,f);cubic((-half,f-4*d/3),(half,f-4*d/3),(half,f))
  elif shape=='Camera stepped recess':
   for pt in ((-half,f),(-half,f-.4*d),(-half*.7,f-.4*d),(-half*.7,f-d),(half*.7,f-d),(half*.7,f-.4*d),(half,f-.4*d),(half,f)):line(*pt)
  elif shape=='Camera chamfered recess':
   ch=min(half*.3,d*.3)
   for pt in ((-half,f),(-half,f-d+ch),(-half+ch,f-d),(half-ch,f-d),(half,f-d+ch),(half,f)):line(*pt)
  line(h,f)
 elif shape=='Rounded nose':
  cubic((-h,f-d+k*d),(-k*h,f),(0,f));cubic((k*h,f),(h,f-d+k*d),(h,f-d))
 elif shape=='Pointed nose':line(0,f);line(h,f-d)
 elif shape=='Flat-tip nose':line(-tip,f);line(tip,f);line(h,f-d)
 elif shape=='Swept shoulders':
  cubic((-h,f-d*.2),(-(h+tip)/2,f),(-tip,f));line(tip,f);cubic(((h+tip)/2,f),(h,f-d*.2),(h,f-d))
 elif shape=='Concave nose':
  start=(-h,f);cubic((-h/3,f-4*d/3),(h/3,f-4*d/3),(h,f))
 elif shape=='V-notch':start=(-h,f);line(0,f-d);line(h,f)
 elif shape=='Twin lobes':
  cubic((-h,f-d+k*d),(-.75*h,f),(-.5*h,f));cubic((-.25*h,f),(-.25*h,f-.55*d),(0,f-.55*d))
  cubic((.25*h,f-.55*d),(.25*h,f),(.5*h,f));cubic((.75*h,f),(h,f-d+k*d),(h,f-d))
 elif shape=='Stepped nose':
  for point in ((-(h+tip)/2,f-d),(-(h+tip)/2,f-.35*d),(-tip,f-.35*d),(-tip,f),(tip,f),(tip,f-.35*d),((h+tip)/2,f-.35*d),((h+tip)/2,f-d),(h,f-d)):line(*point)
 elif shape=='Shallow W':
  start=(-h,f)
  for point in ((-.5*h,f-d),(0,f),(.5*h,f-d),(h,f)):line(*point)
 elif shape=='Triple scallop':
  start=(-h,f)
  for i in range(3):
   a=-h+2*h*i/3;b=-h+2*h*(i+1)/3
   cubic((a+(b-a)/3,f-4*d/3),(a+2*(b-a)/3,f-4*d/3),(b,f))
 elif shape=='Arrowhead':
  for point in ((-.35*h,f-d),(0,f),(.35*h,f-d),(h,f-d)):line(*point)
 elif shape=='Flat recess':
  start=(-h,f)
  for point in ((-tip,f-d),(tip,f-d),(h,f)):line(*point)
 elif shape=='Round U recess':
  start=(-h,f);line(-tip,f);cubic((-tip,f-4*d/3),(tip,f-4*d/3),(tip,f));line(h,f)
 elif shape in ('Cable channel','Dual cable channels'):
  start=(-h,f)
  def channel(centre,half):
   radius=min(half,d/2);left=centre-half;right=centre+half
   line(left,f);line(left,f-d+radius)
   cubic((left,f-d+radius-k*radius),(left+radius-k*radius,f-d),(left+radius,f-d))
   line(right-radius,f-d)
   cubic((right-radius+k*radius,f-d),(right,f-d+radius-k*radius),(right,f-d+radius))
   line(right,f)
  if shape=='Cable channel':channel(0,tip)
  else:
   channel(-.48*h,min(.22*h,tip));channel(.48*h,min(.22*h,tip))
  line(h,f)
 elif shape=='Split tail':
  start=(-h,f)
  for point in ((-tip,f),(-tip,f-d),(tip,f-d),(tip,f),(h,f)):line(*point)
 elif shape=='Stepped electronics tail':
  for point in ((-(h+tip)/2,f-.25*d),(-tip,f-.25*d),(-tip,f),(tip,f),(tip,f-.25*d),((h+tip)/2,f-.25*d),(h,f-d)):line(*point)
 # A closed mask trims this end inside the original reach; it never adds stock.
 result=(('M',(-outer,rear-1)),('L',(-outer,f-d)),('L',(-h,f-d)),('L',start),*commands,('L',(outer,f-d)),('L',(outer,rear-1)),('L',(-outer,rear-1)))

 return tuple((item[0],*((x,-y if reverse else y) for x,y in item[1:])) for item in result)

@parameter_cache(maxsize=128)
def edge_polygon(p,role,end,width,rear,front):
 points=[];current=None
 for item in edge_commands(p,role,end,width,rear,front):
  if item[0] in ('M','L'):current=item[1];points.append(current)
  else:
   a=current;b,c,d=item[1:]
   for i in range(1,65):
    t=i/64;u=1-t
    points.append(tuple(u**3*a[j]+3*u*u*t*b[j]+3*u*t*t*c[j]+t**3*d[j] for j in (0,1)))
   current=d
 if len(points)>1 and points[0]==points[-1]:points.pop()
 return tuple(points)

def nose_commands(p,width,rear,front):return edge_commands(p,'BottomPlate','Front',width,rear,front)
def nose_polygon(p,width,rear,front):return edge_polygon(p,'BottomPlate','Front',width,rear,front)
