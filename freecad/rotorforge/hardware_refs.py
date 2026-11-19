"""Optional simplified hardware references, separate from manufactured solids."""
import json,math,hashlib
from functools import lru_cache
import FreeCAD as App
import Part
from .document import read_parameters
from .hardware_layout import hardware_layout,SIZES,DEFAULT_OPTIONS,normalize_options

def cleanup(frame):
 # Remove retired presentation objects and restore any saved source visibility.
 for obj in list(frame.Document.Objects):
  if getattr(obj,'SourceFrame',None)!=frame:continue
  kind=getattr(obj,'AssemblyAidKind',None)
  if kind=='Settings':
   if 'Options' in obj.PropertiesList:
    raw=json.loads(obj.Options);clean=normalize_options(raw)
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
 t=settings(frame);saved=json.loads(t.Options);value=normalize_options(saved)
 if value!=saved:t.Options=json.dumps(value)
 return value
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
 o=options(frame)
 all_specs=hardware_layout(read_parameters(frame),o)
 role_specs=_group_specs(all_specs)
 # Old documents may still have combined owner-level hardware objects until
 # their first refresh; keep global Show/Hide working during that migration.
 for spec in all_specs:role_specs.setdefault(spec['owner'],[]).append(spec)
 for obj in objects(frame):
  if 'HardwareVisible' not in obj.PropertiesList:obj.addProperty('App::PropertyBool','HardwareVisible')
  role=str(obj.HardwareRole) if 'HardwareRole' in obj.PropertiesList else ''
  enabled=_reference_enabled(role,role_specs.get(role,[]),o)
  obj.HardwareVisible=bool(on and enabled)
  if App.GuiUp:obj.ViewObject.Visibility=obj.HardwareVisible and not t.ReferencesStale

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
def screw(d,length,nut,nut_z,head_style='Round head'):
 # Low-profile round button head: M3 nominal 5.7 mm diameter, 1.65 mm crown.
 r=.95*d;h=.55*d;radius=(r*r+h*h)/(2*h)
 if head_style=='Countersunk':
  # Flush head is inside the joint; length is measured from its outer face.
  head=Part.makeCone(d,d/2,d/2,App.Vector(0,0,0))
  recess=hexface(.65*d).extrude(App.Vector(0,0,.45*d));recess.translate(App.Vector(0,0,-.001))
  body=head.fuse(Part.makeCylinder(d/2,length)).cut(recess).removeSplitter()
 else:
  head=Part.makeSphere(radius,App.Vector(0,0,radius-h)).common(Part.makeCylinder(r,h,App.Vector(0,0,-h)))
  recess=hexface(.65*d).extrude(App.Vector(0,0,h*.65));recess.translate(App.Vector(0,0,-h-.001));head=head.cut(recess)
  body=head.fuse(Part.makeCylinder(d/2,length)).removeSplitter()
 parts=[body]
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

NUT_ROLE_SUFFIX = '::nuts'
SCREW_ROLE_SEPARATOR = '::screws::'


def _is_nut_role(role):
 return str(role).endswith(NUT_ROLE_SUFFIX)


def _screw_role(spec):
 # An arm can carry both its root bolts and motor screws; a plate can
 # carry standoff, cage and VTX screws. Owner-only grouping cannot support
 # independent visibility controls for these categories.
 return str(spec['owner'])+SCREW_ROLE_SEPARATOR+str(spec['group'])


def _group_specs(specs):
 """Group screw solids by (owner, category), and nuts by owner alone."""
 roles={}
 for spec in specs:
  roles.setdefault(_screw_role(spec),[]).append(spec)
  if spec['nut']:
   roles.setdefault(spec['owner']+NUT_ROLE_SUFFIX,[]).append(spec)
 return roles


def _role_label(role):
 if _is_nut_role(role):return role[:-len(NUT_ROLE_SUFFIX)]+' nuts / press nuts'
 if SCREW_ROLE_SEPARATOR in role:
  owner,category=role.split(SCREW_ROLE_SEPARATOR,1)
  return owner+' — '+category
 return role+' screws'  # legacy document object


def _legacy_owner(role):
 if SCREW_ROLE_SEPARATOR in role:return role.split(SCREW_ROLE_SEPARATOR,1)[0]
 return role


def _reference_enabled(role, specs, choices):
 """Apply category visibility to an individual hardware group, not its owner."""
 if _is_nut_role(role):return bool(choices['nuts'])
 return any(spec['group'] in choices['groups'] for spec in specs)


def _hidden_role(role,hidden):
 """Honor saved 0.92.99 owner-level visibility when loading into new groups."""
 return role in hidden or (SCREW_ROLE_SEPARATOR in role and _legacy_owner(role) in hidden)

def _hex_nut(spec):
 """Create only the removable hex nut, without its screw body."""
 d=spec['diameter'];height=SIZES[d][5]
 nut=hexface(SIZES[d][4]).extrude(App.Vector(0,0,height))
 nut=nut.cut(Part.makeCylinder(d/2,height+.02,App.Vector(0,0,-.01)))
 nut.translate(App.Vector(0,0,spec['nut_distance']))
 # Apply assembly placement to a compound as the original combined-screw
 # builder did, preserving the nut's local axial offset.
 shape=Part.makeCompound([nut])
 shape.Placement=App.Placement(App.Vector(*spec['point']),App.Rotation(App.Vector(0,0,1),App.Vector(*spec['axis'])))
 return shape


def _press_nut(spec,p):
 """Model the configured press nut on its own hardware reference object."""
 seat=spec['seat'];z=seat['z'];axis=seat['axis'];x,y=seat['point'];flangebase=z-axis*p.PressNutFlangeRecess
 flange=Part.makeCylinder(p.PressNutFlangeDiameter/2,p.PressNutFlangeHeight,App.Vector(x,y,flangebase),App.Vector(0,0,axis))
 shank=Part.makeCylinder(p.PressNutShankDiameter/2,p.PressNutShankDepth,App.Vector(x,y,flangebase),App.Vector(0,0,-axis))
 bore=Part.makeCylinder(1.5,p.PressNutShankDepth+p.PressNutFlangeHeight+.2,App.Vector(x,y,flangebase-axis*(p.PressNutShankDepth+.1)),App.Vector(0,0,axis))
 return flange.fuse(shank).cut(bore)


def _refresh(frame,o,automatic,recompute):
 from .nut_seats import validate_seats
 from .version import __version__
 p=getattr(getattr(frame,'Proxy',None),'_document_build_parameters',None) if automatic else None
 if p is None:p=read_parameters(frame)
 errors=validate_seats(p)
 if errors:raise ValueError('; '.join(errors))
 t=settings(frame);reference_flags(frame,t)
 o=options(frame) if o is None else normalize_options(o)
 specs=hardware_layout(p,o)
 # Keep nuts separate so they may be hidden while their corresponding screws
 # remain visible (and vice versa). No model geometry is modified.
 by_role=_group_specs(specs)
 old={};duplicates=[]
 for obj in objects(frame):
  role=str(obj.HardwareRole) if 'HardwareRole' in obj.PropertiesList else obj.Label.removesuffix(' fasteners')
  if role in old:duplicates.append(obj)
  else:old[role]=obj
 signatures={}
 for role,items in by_role.items():
  is_nut=_is_nut_role(role)
  inserts=tuple(getattr(p,n) for n in ('PressNutFlangeDiameter','PressNutFlangeHeight','PressNutShankDiameter','PressNutShankDepth','PressNutFlangeRecess')) if is_nut and any(s.get('press') for s in items) else ()
  # Display selections intentionally do not influence the mesh signature.
  signatures[role]=hashlib.sha256(json.dumps((__version__,is_nut,items,inserts),sort_keys=True).encode()).hexdigest()
 changed={role for role in by_role if role not in old or getattr(old[role],'HardwareSignature','')!=signatures[role]}
 # Generate all replacements before changing the document to keep failures safe.
 shapes={}
 for role in changed:
  is_nut=_is_nut_role(role)
  for spec in by_role[role]:
   if is_nut:
    shape=_press_nut(spec,p) if spec.get('press') else _hex_nut(spec)
   else:
    shape=screw(spec['diameter'],round(spec['length'],5),False,0.,spec.get('head','Round head')).copy()
    shape.Placement=App.Placement(App.Vector(*spec['point']),App.Rotation(App.Vector(0,0,1),App.Vector(*spec['axis'])))
   shapes.setdefault(role,[]).append(shape)
 parent=next((obj for obj in frame.Document.Objects if getattr(obj,'SourceFrame',None)==frame and getattr(obj,'AssemblyAidKind',None)=='Group'),None)
 if parent is None and by_role:
  parent=frame.Document.addObject('App::DocumentObjectGroup','HardwareReferences');parent.Label='Hardware references'
  parent.addProperty('App::PropertyLinkHidden','SourceFrame').SourceFrame=frame;parent.addProperty('App::PropertyString','AssemblyAidKind').AssemblyAidKind='Group'
  for root in frame.InList:
   if 'Generator' in root.PropertiesList and root.Generator==frame:root.addObject(parent);break
 # When upgrading an existing document, preserve any manual visibility
 # applied to the old owner-level object across its new category subgroups.
 legacy_visible={}
 for old_role,old_obj in old.items():
  if SCREW_ROLE_SEPARATOR in old_role or _is_nut_role(old_role):continue
  legacy_visible[old_role]=(bool(old_obj.HardwareVisible) if t.ReferencesStale and 'HardwareVisible' in old_obj.PropertiesList
                             else bool(old_obj.ViewObject.Visibility) if App.GuiUp else bool(t.ReferencesVisible))
 for obj in duplicates+[obj for role,obj in old.items() if role not in by_role]:frame.Document.removeObject(obj.Name)
 for role,items in by_role.items():
  obj=old.get(role);enabled=_reference_enabled(role,items,o)
  if automatic:
   previous=(bool(obj.HardwareVisible) if t.ReferencesStale and obj and 'HardwareVisible' in obj.PropertiesList else
             bool(obj.ViewObject.Visibility) if App.GuiUp and obj else
             legacy_visible.get(_legacy_owner(role),bool(t.ReferencesVisible)))
   visible=previous and enabled
  else:visible=enabled
  if obj is None:
   obj=frame.Document.addObject('Part::Feature','HardwareReference')
   obj.Label=_role_label(role)
   obj.addProperty('App::PropertyLink','SourceFrame').SourceFrame=frame;obj.addProperty('App::PropertyString','AssemblyAidKind').AssemblyAidKind='Hardware';parent.addObject(obj)
  else:obj.Label=_role_label(role)
  for kind,name in (('App::PropertyString','HardwareRole'),('App::PropertyString','HardwareSignature'),('App::PropertyBool','HardwareVisible')):
   if name not in obj.PropertiesList:obj.addProperty(kind,name)
  if role in changed:obj.Shape=Part.makeCompound(shapes[role])
  if obj.HardwareRole!=role:obj.HardwareRole=role
  if obj.HardwareSignature!=signatures[role]:obj.HardwareSignature=signatures[role]
  obj.HardwareVisible=visible
  if App.GuiUp:
   apply_hardware_colour(obj.ViewObject)
   obj.ViewObject.Visibility=visible
 encoded=json.dumps(o)
 if t.Options!=encoded:t.Options=encoded
 signature=hashlib.sha256(json.dumps(signatures,sort_keys=True).encode()).hexdigest()
 if t.SourceSignature!=signature:t.SourceSignature=signature
 t.ReferencesCreated=True;t.ReferencesStale=False
 if not automatic:t.ReferencesVisible=True
 if recompute:frame.Document.recompute()
 return specs


def saved_preferences(frame=None):
 """Capture choices without creating settings or changing the document."""
 from .hardware_preferences import validate_preferences
 t=existing_settings(frame) if frame is not None else None
 current=objects(frame) if frame is not None else []
 created=bool(getattr(t,'ReferencesCreated',bool(current)))
 visible=bool(getattr(t,'ReferencesVisible',True))
 stale=bool(getattr(t,'ReferencesStale',False))
 hidden=[]
 for obj in current:
  shown=(bool(obj.HardwareVisible) if stale and 'HardwareVisible' in obj.PropertiesList else
         bool(obj.ViewObject.Visibility) if App.GuiUp else bool(getattr(obj,'HardwareVisible',visible)))
  if not shown:hidden.append(str(getattr(obj,'HardwareRole',obj.Label.removesuffix(' fasteners'))))
 return validate_preferences(dict(version=1,created=created,visible=visible,
                                  options=json.loads(t.Options) if t is not None else dict(DEFAULT_OPTIONS),hidden_roles=hidden))


def restore_preferences(frame,value):
 """Apply explicitly saved display choices after a frame has been built."""
 from .hardware_preferences import validate_preferences
 value=validate_preferences(value)
 t=settings(frame);reference_flags(frame,t)
 if value['created']:
  refresh(frame,value['options'],recompute=False)
 else:
  for obj in list(objects(frame)):frame.Document.removeObject(obj.Name)
  t.Options=json.dumps(value['options']);t.ReferencesCreated=False;t.ReferencesStale=False
  t.SourceSignature=''
 t.ReferencesVisible=value['visible']
 hidden=set(value['hidden_roles'])
 all_specs=hardware_layout(read_parameters(frame),value['options']) if value['created'] else []
 role_specs=_group_specs(all_specs)
 for obj in objects(frame):
  role=str(obj.HardwareRole)
  shown=value['visible'] and not _hidden_role(role,hidden) and _reference_enabled(role,role_specs.get(role,[]),value['options'])
  obj.HardwareVisible=shown
  if App.GuiUp:obj.ViewObject.Visibility=shown
 frame.Document.recompute()
