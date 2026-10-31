"""Optional simplified hardware references, separate from manufactured solids."""
import json,math,hashlib
from functools import lru_cache
import FreeCAD as App
import Part
from .document import read_parameters
from .hardware_layout import hardware_layout,SIZES,DEFAULT_OPTIONS

def cleanup(frame):
 # Remove retired presentation objects and restore any saved source visibility.
 for obj in list(frame.Document.Objects):
  if getattr(obj,'SourceFrame',None)!=frame:continue
  kind=getattr(obj,'AssemblyAidKind',None)
  if kind=='Settings':
   if 'Options' in obj.PropertiesList:
    raw=json.loads(obj.Options);clean={k:raw.get(k,v) for k,v in DEFAULT_OPTIONS.items()}
    if clean!=raw:obj.Options=json.dumps(clean)
   if App.GuiUp and 'OriginalVisibility' in obj.PropertiesList:
    for name,visible in json.loads(obj.OriginalVisibility or '{}').items():
     source=frame.Document.getObject(name)
     if source:source.ViewObject.Visibility=visible
   for prop in ('OriginalVisibility','Presentation','AttachmentPoints'):
    if prop in obj.PropertiesList:obj.removeProperty(prop)
  elif kind in ('Exploded','Removal','Attachment') or kind=='Hardware' and 'OwnerRole' in obj.PropertiesList:frame.Document.removeObject(obj.Name)
 for obj in list(frame.Document.Objects):
  if getattr(obj,'SourceFrame',None)==frame and getattr(obj,'AssemblyAidKind',None)=='Group' and not obj.Group:frame.Document.removeObject(obj.Name)

def settings(frame):
 cleanup(frame)
 for obj in frame.Document.Objects:
  if getattr(obj,'AssemblyAidKind',None)=='Settings' and getattr(obj,'SourceFrame',None)==frame:
   obj.Label='Hardware reference settings';return obj
 obj=frame.Document.addObject('App::FeaturePython','HardwareSettings');obj.Label='Hardware reference settings'
 obj.addProperty('App::PropertyLink','SourceFrame').SourceFrame=frame;obj.addProperty('App::PropertyString','AssemblyAidKind').AssemblyAidKind='Settings'
 obj.addProperty('App::PropertyString','Options').Options=json.dumps(DEFAULT_OPTIONS);obj.addProperty('App::PropertyString','SourceSignature')
 for parent in frame.InList:
  if 'Generator' in parent.PropertiesList and parent.Generator==frame:parent.addObject(obj);break
 return obj

def objects(frame):return [o for o in frame.Document.Objects if getattr(o,'SourceFrame',None)==frame and getattr(o,'AssemblyAidKind',None)=='Hardware']
def options(frame):
 t=settings(frame);saved=json.loads(t.Options);value={k:saved.get(k,v) for k,v in DEFAULT_OPTIONS.items()};t.Options=json.dumps(value);return value
def existing_settings(frame):
 return next((o for o in frame.Document.Objects if getattr(o,'AssemblyAidKind',None)=='Settings' and getattr(o,'SourceFrame',None)==frame),None)

def reference_flags(frame,t):
 current=objects(frame)
 legacy_stale=str(t.SourceSignature)=='Refresh hardware after changing the frame.'
 for name,value in (('ReferencesCreated',bool(current) or str(t.SourceSignature) in ('Current','Refresh hardware after changing the frame.')),('ReferencesVisible',True if legacy_stale else any(o.ViewObject.Visibility for o in current) if App.GuiUp and current else True),('ReferencesStale',legacy_stale)):
  if name not in t.PropertiesList:t.addProperty('App::PropertyBool',name);setattr(t,name,value)
 if legacy_stale:
  for obj in current:
   if 'HardwareVisible' not in obj.PropertiesList:obj.addProperty('App::PropertyBool','HardwareVisible');obj.HardwareVisible=True

def invalidate_refs(frame):
 t=existing_settings(frame)
 if t is None:return
 reference_flags(frame,t)
 if not t.ReferencesStale:
  for obj in objects(frame):
   if 'HardwareVisible' not in obj.PropertiesList:obj.addProperty('App::PropertyBool','HardwareVisible')
   obj.HardwareVisible=bool(obj.ViewObject.Visibility) if App.GuiUp else t.ReferencesVisible
 if App.GuiUp:
  for obj in objects(frame):obj.ViewObject.Visibility=False
 t.ReferencesStale=True
 t.SourceSignature='References paused until the frame is valid.'

def set_visible(frame,on):
 t=settings(frame);reference_flags(frame,t);t.ReferencesVisible=on
 for obj in objects(frame):
  if 'HardwareVisible' not in obj.PropertiesList:obj.addProperty('App::PropertyBool','HardwareVisible')
  obj.HardwareVisible=on
  if App.GuiUp:obj.ViewObject.Visibility=on and not t.ReferencesStale

def sync_refs(frame):
 # Opening the dialog alone must not opt a frame into generating hardware.
 t=existing_settings(frame)
 if t is None:return
 reference_flags(frame,t)
 if t.ReferencesCreated:refresh(frame,automatic=True,recompute=False)


def apply_hardware_colour(view):
 colour=(.035,.038,.042)
 view.ShapeColor=colour;view.LineColor=(.012,.014,.016)
 field='ShapeAppearance' if 'ShapeAppearance' in view.PropertiesList else 'ShapeMaterial' if 'ShapeMaterial' in view.PropertiesList else None
 if field:
  value=getattr(view,field);material=value[0] if field=='ShapeAppearance' and value else value
  if material:
   material.DiffuseColor=colour;material.SpecularColor=(.18,.18,.18);material.Shininess=28.
   setattr(view,field,[material] if field=='ShapeAppearance' else material)

def hexface(across):
 r=across/math.sqrt(3);pts=[App.Vector(r*math.cos(i*math.pi/3),r*math.sin(i*math.pi/3),0) for i in range(6)]
 return Part.Face(Part.makePolygon(pts+[pts[0]]))

@lru_cache(maxsize=256)
def screw(d,length,nut,nut_z):
 # Low-profile round button head: M3 nominal 5.7 mm diameter, 1.65 mm crown.
 r=.95*d;h=.55*d;radius=(r*r+h*h)/(2*h)
 head=Part.makeSphere(radius,App.Vector(0,0,radius-h)).common(Part.makeCylinder(r,h,App.Vector(0,0,-h)))
 recess=hexface(.65*d).extrude(App.Vector(0,0,h*.65));recess.translate(App.Vector(0,0,-h-.001));head=head.cut(recess)
 parts=[head.fuse(Part.makeCylinder(d/2,length)).removeSplitter()]
 if nut:
  n=hexface(SIZES[d][4]).extrude(App.Vector(0,0,SIZES[d][5]));n=n.cut(Part.makeCylinder(d/2,SIZES[d][5]+.02,App.Vector(0,0,-.01)));n.translate(App.Vector(0,0,nut_z));parts.append(n)
 return Part.makeCompound(parts)

_REFRESHING=set()
def refresh(frame,o=None,automatic=False,recompute=True):
 key=(frame.Document.Name,frame.Name)
 if key in _REFRESHING:return []
 _REFRESHING.add(key)
 try:return _refresh(frame,o,automatic,recompute)
 finally:_REFRESHING.discard(key)

def _refresh(frame,o,automatic,recompute):
 from .nut_seats import validate_seats
 from .version import __version__
 p=read_parameters(frame);errors=validate_seats(p)
 if errors:raise ValueError('; '.join(errors))
 t=settings(frame);reference_flags(frame,t)
 o=options(frame) if o is None else o
 specs=hardware_layout(p,o);by_role={}
 for spec in specs:by_role.setdefault(spec['owner'],[]).append(spec)
 old={};duplicates=[]
 for obj in objects(frame):
  role=str(obj.HardwareRole) if 'HardwareRole' in obj.PropertiesList else obj.Label.removesuffix(' fasteners')
  if role in old:duplicates.append(obj)
  else:old[role]=obj
 # Signatures include only this owner's actual fasteners and insert dimensions.
 signatures={}
 for role,items in by_role.items():
  insert=tuple(getattr(p,n) for n in ('PressNutFlangeDiameter','PressNutFlangeHeight','PressNutShankDiameter','PressNutShankDepth','PressNutFlangeRecess')) if any(s.get('press') and s['nut'] for s in items) else ()
  signatures[role]=hashlib.sha256(json.dumps((__version__,items,insert),sort_keys=True).encode()).hexdigest()
 changed={role for role in by_role if role not in old or getattr(old[role],'HardwareSignature','')!=signatures[role]}
 needed=[s for role in changed for s in by_role[role]]
 # Build all changed shapes before modifying document objects.
 shapes={}
 specs_to_return=specs
 specs=needed
 for s in specs:
  shape=screw(s['diameter'],round(s['length'],5),s['nut'] and (not s.get('press') or s['group']=='Stack hardware'),round(s['nut_distance'],5)).copy()
  shape.Placement=App.Placement(App.Vector(*s['point']),App.Rotation(App.Vector(0,0,1),App.Vector(*s['axis'])))
  if s.get('press') and s['nut']:
   seat=s['seat'];z=seat['z'];axis=seat['axis'];x,y=seat['point'];flangebase=z-axis*p.PressNutFlangeRecess
   flange=Part.makeCylinder(p.PressNutFlangeDiameter/2,p.PressNutFlangeHeight,App.Vector(x,y,flangebase),App.Vector(0,0,axis))
   shank=Part.makeCylinder(p.PressNutShankDiameter/2,p.PressNutShankDepth,App.Vector(x,y,flangebase),App.Vector(0,0,-axis))
   bore=Part.makeCylinder(1.5,p.PressNutShankDepth+p.PressNutFlangeHeight+.2,App.Vector(x,y,flangebase-axis*(p.PressNutShankDepth+.1)),App.Vector(0,0,axis))
   shape=Part.makeCompound([shape,flange.fuse(shank).cut(bore)])
  shapes.setdefault(s['owner'],[]).append(shape)
 parent=next((obj for obj in frame.Document.Objects if getattr(obj,'SourceFrame',None)==frame and getattr(obj,'AssemblyAidKind',None)=='Group'),None)
 if parent is None and by_role:
  parent=frame.Document.addObject('App::DocumentObjectGroup','HardwareReferences');parent.Label='Hardware references'
  parent.addProperty('App::PropertyLinkHidden','SourceFrame').SourceFrame=frame;parent.addProperty('App::PropertyString','AssemblyAidKind').AssemblyAidKind='Group'
  for root in frame.InList:
   if 'Generator' in root.PropertiesList and root.Generator==frame:root.addObject(parent);break
 for obj in duplicates+[obj for role,obj in old.items() if role not in by_role]:frame.Document.removeObject(obj.Name)
 for role in by_role:
  obj=old.get(role)
  visible=(bool(obj.HardwareVisible) if t.ReferencesStale and obj and 'HardwareVisible' in obj.PropertiesList else bool(obj.ViewObject.Visibility) if App.GuiUp and obj else bool(t.ReferencesVisible)) if automatic else True
  if obj is None:
   obj=frame.Document.addObject('Part::Feature','HardwareReference');obj.Label=role+' fasteners'
   obj.addProperty('App::PropertyLink','SourceFrame').SourceFrame=frame;obj.addProperty('App::PropertyString','AssemblyAidKind').AssemblyAidKind='Hardware';parent.addObject(obj)
  for kind,name in (('App::PropertyString','HardwareRole'),('App::PropertyString','HardwareSignature'),('App::PropertyBool','HardwareVisible')):
   if name not in obj.PropertiesList:obj.addProperty(kind,name)
  if role in changed:obj.Shape=Part.makeCompound(shapes[role])
  if obj.HardwareRole!=role:obj.HardwareRole=role
  if obj.HardwareSignature!=signatures[role]:obj.HardwareSignature=signatures[role]
  obj.HardwareVisible=visible
  if App.GuiUp:apply_hardware_colour(obj.ViewObject);obj.ViewObject.Visibility=visible
 encoded=json.dumps(o)
 if t.Options!=encoded:t.Options=encoded
 signature=hashlib.sha256(json.dumps(signatures,sort_keys=True).encode()).hexdigest()
 if t.SourceSignature!=signature:t.SourceSignature=signature
 t.ReferencesCreated=True;t.ReferencesStale=False
 if not automatic:t.ReferencesVisible=True
 if recompute:frame.Document.recompute()
 return specs_to_return
