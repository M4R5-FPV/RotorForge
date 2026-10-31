"""Native nut pockets and broaching holes, with separate through-cut flattening."""
import math
import FreeCAD as App
import Part
from .nut_seats import seats

def hex_prism(point,across,z,height):
 x,y=point;r=across/math.sqrt(3);pts=[App.Vector(x+r*math.cos(i*math.pi/3),y+r*math.sin(i*math.pi/3),z) for i in range(6)]
 return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(0,0,height))

def tools(p,s):
 from .hardware_layout import SIZES,metric_size
 x,y=s['point'];z=s['z'];d=s['depth'];lo=z-d if s['axis']>0 else z
 if s['mode']=='Recessed hex nut':
  across=SIZES[metric_size(s['bore'])][4]+p.NutRecessClearance
  return None,hex_prism(s['point'],across,lo,d),across/math.sqrt(3)
 low=z-s['thickness'] if s['axis']>0 else z
 through=Part.makeCylinder(p.PressNutBore/2,s['thickness']+.02,App.Vector(x,y,low-.01))
 pocket=Part.makeCylinder((p.PressNutFlangeDiameter+p.NutRecessClearance)/2,d,App.Vector(x,y,lo)) if d else None
 return through,pocket,(p.PressNutFlangeDiameter+(p.NutRecessClearance if d else 0.))/2

def apply_seats(shape,p,role):
 for s in seats(p,role):
  through,pocket,radius=tools(p,s);x,y=s['point'];facez=s['z']-s['axis']*.04
  # Require an intact bearing rim around the complete seat, including nearby cuts.
  bandz=facez-.02
  margin=1. if s['mode']=='M3 press nut' else p.MinimumWeb
  ring=Part.makeCylinder(radius+margin,.04,App.Vector(x,y,bandz)).cut(Part.makeCylinder(radius+.001,.06,App.Vector(x,y,bandz-.01)))
  if ring.cut(shape).Volume>1e-5:raise ValueError(role+': insufficient bearing material around a nut seat; widen the plate or move the bolt.')
  if through is not None:shape=shape.cut(through)
  if pocket is not None:shape=shape.cut(pocket)
 return shape

def restore_pockets(shape,p,role):
 for s in seats(p,role):
  through,pocket,_=tools(p,s)
  if pocket is None:continue
  x,y=s['point'];b=pocket.BoundBox;diam=p.PressNutBore if s['mode']=='M3 press nut' else s['bore']
  bore=Part.makeCylinder(diam/2,b.ZLength+.2,App.Vector(x,y,b.ZMin-.1));shape=shape.fuse(pocket.cut(bore)).removeSplitter()
 return shape

def operations(p):
 from .hardware_layout import SIZES,metric_size
 result=[]
 for s in seats(p):
  if s['mode']=='M3 press nut' and not s['depth']:continue
  result.append(dict(part=s['role'],operation='Hex nut pocket' if s['mode']=='Recessed hex nut' else 'Press-nut flange counterbore',face='Upper' if s['axis']>0 else 'Lower',rotation_deg=0,x_frame_mm=s['point'][0],y_frame_mm=s['point'][1],through_diameter_mm=p.PressNutBore if s['mode']=='M3 press nut' else s['bore'],outer_diameter_mm=p.PressNutFlangeDiameter+p.NutRecessClearance if s['mode']=='M3 press nut' else '',across_flats_mm=SIZES[metric_size(s['bore'])][4]+p.NutRecessClearance if s['mode']=='Recessed hex nut' else '',depth_mm=s['depth']))
 return result
