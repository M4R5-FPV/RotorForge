"""Bounded component cache with dependencies captured from real parameter reads.

No CAD imports: the same dependency rules can be tested outside FreeCAD.
Cached outputs are owned by the cache; callers receive copies.
"""
from collections import OrderedDict
from dataclasses import fields
import hashlib,json,time
from .parameters import Parameters
from .version import __version__

_NAMES=frozenset(f.name for f in fields(Parameters))
class TrackedParameters(Parameters):
 def __getattribute__(self,name):
  if name in _NAMES:
   try:object.__getattribute__(self,'_reads').add(name)
   except AttributeError:pass
  return super().__getattribute__(name)

_IDENTITIES=OrderedDict()
def remember_shape(shape,token):
 if shape.isNull():return
 key=shape.hashCode();bucket=_IDENTITIES.get(key,())
 _IDENTITIES[key]=list(bucket)[-3:]+[(shape,str(shape.Orientation),token)];_IDENTITIES.move_to_end(key)
 while len(_IDENTITIES)>192:_IDENTITIES.popitem(last=False)

def copy_entry(entry):
 value=entry['shape'].copy();remember_shape(value,entry['token']);return value

def shape_token(shape):
 if shape is None:return 'missing'
 if shape.isNull():return 'null'
 key=shape.hashCode()
 # hashCode is only a bucket. Verify native identity to handle hash collisions.
 bucket=_IDENTITIES.get(key,())
 for old,orientation,token in bucket:
  if old.hashCode()==key and str(old.Orientation)==orientation and old.isSame(shape):
   _IDENTITIES.move_to_end(key);return token
 raw=shape.exportBrepToString();token=hashlib.sha256(raw.encode()).hexdigest()
 _IDENTITIES[key]=list(bucket)[-3:]+[(shape,str(shape.Orientation),token)]
 _IDENTITIES.move_to_end(key)
 while len(_IDENTITIES)>192:_IDENTITIES.popitem(last=False)
 return token

class ShapeInputs(dict):
 def __init__(self,values):super().__init__(values);self.reads={}
 def __getitem__(self,key):
  value=super().__getitem__(key);self.reads[key]=shape_token(value);return value
 def get(self,key,default=None):
  value=super().get(key,default);self.reads[key]=shape_token(value);return value
 def items(self):
  for key in self:yield key,self[key]
 def values(self):
  for key in self:yield self[key]

class ComponentCache:
 def __init__(self,max_entries=160,max_bytes=64*1024*1024):
  self.entries=OrderedDict();self._by_key={};self.max_entries=max_entries;self.max_bytes=max_bytes;self.bytes=0;self.serial=0;self.events=[];self.latest={};self.last_entry=None
 def clear(self):self.entries.clear();self._by_key.clear();self.bytes=0;self.latest.clear();self.events=[];self.last_entry=None
 def begin(self):self.events=[]
 def get(self,key,p,inputs,builder):
  start=time.perf_counter();values=inputs or {};tokens={}
  def input_token(name):
   if name not in tokens:tokens[name]=shape_token(values.get(name))
   return tokens[name]
  # Entries are keyed by role, so retain only that role's candidates. Avoid
  # allocating a full reversed snapshot of every BRep entry on every lookup.
  for serial in reversed(self._by_key.get(key,())):
   entry=self.entries.get(serial)
   if entry is None:continue
   if any(getattr(p,n)!=v for n,v in entry['parameters'].items()):continue
   if any(input_token(n)!=token for n,token in entry['inputs'].items()):continue
   self.entries.move_to_end(serial);self.latest[key]=entry;self.last_entry=entry
   self.events.append(dict(role=key,action='reused',seconds=time.perf_counter()-start));return copy_entry(entry)
  signature=p.signature();traced=TrackedParameters(*signature);object.__setattr__(traced,'_reads',set());object.__setattr__(traced,'_parameter_signature',signature)
  upstream=ShapeInputs(values);shape=builder(traced,upstream)
  entry=self._put(dict(key=key,parameters={n:getattr(p,n) for n in sorted(traced._reads)},inputs=dict(upstream.reads),shape=shape.copy()))
  self.events.append(dict(role=key,action='rebuilt',seconds=time.perf_counter()-start));return copy_entry(entry)
 def _put(self,entry):
  if 'payload' not in entry:entry['payload']=entry['shape'].exportBrepToString()
  entry['token']='null' if entry['shape'].isNull() else hashlib.sha256(entry['payload'].encode()).hexdigest()
  remember_shape(entry['shape'],entry['token']);entry['bytes']=len(entry['payload'])
  self.serial+=1;self.entries[self.serial]=entry;self._by_key.setdefault(entry['key'],[]).append(self.serial);self.bytes+=entry['bytes'];self.latest[entry['key']]=entry;self.last_entry=entry
  while self.entries and (len(self.entries)>self.max_entries or self.bytes>self.max_bytes):
   serial,old=self.entries.popitem(last=False);self.bytes-=old['bytes']
   if serial in self._by_key.get(old['key'],()):self._by_key[old['key']].remove(serial)
   if not self._by_key.get(old['key']):self._by_key.pop(old['key'],None)
   if self.latest.get(old['key']) is old:self.latest.pop(old['key'],None)
  return entry
 def manifest(self,key):
  entry=self.latest.get(key)
  if entry is None:return ''
  # An entry's dependency values and digest never change after insertion.
  # Save the canonical manifest instead of JSON-serialising it repeatedly for
  # the document properties, native archive and each dependent part.
  if 'manifest' not in entry:
   entry['manifest']=json.dumps(dict(version=__version__,key=key,parameters=entry['parameters'],inputs=entry['inputs'],token=entry['token']),sort_keys=True,separators=(',',':'),allow_nan=False)
  return entry['manifest']
 def has_manifest(self,key,manifest):
  try:
   data=json.loads(manifest)
   if data['version']!=__version__ or data['key']!=key:return False
   # Only this role's cached entries can match. Checking every component is
   # unnecessary, particularly when restoring a large saved frame.
   return any((e:=self.entries.get(serial)) is not None and
              e['token']==data['token'] and e['parameters']==data['parameters'] and
              e['inputs']==data['inputs'] for serial in self._by_key.get(key,()))
  except (ValueError,KeyError,TypeError):return False
 def native_manifest_match(self,key,manifest,shape):
  """Fast, conservative check for an already cached native OCC solid.

  Distinct native shapes continue through the original BRep digest and
  geometric-verification path. Used only to avoid redundant serialization of
  the very same solid during repeated document updates.
  """
  if shape is None:return False
  try:
   data=json.loads(manifest)
   if data['version']!=__version__ or data['key']!=key:return False
   for serial in reversed(self._by_key.get(key,())):
    entry=self.entries.get(serial)
    if (entry is not None and entry['token']==data['token'] and
        entry['parameters']==data['parameters'] and entry['inputs']==data['inputs']):
     other=entry['shape']
     if (other.isSame(shape) and str(other.Orientation)==str(shape.Orientation) and
         other.Placement==shape.Placement):return True
  except (ValueError,KeyError,TypeError,AttributeError,RuntimeError):return False
  return False

 def seed(self,key,manifest,shape,payload=None):
  try:
   data=json.loads(manifest)
   token=shape_token(shape) if payload is None else 'null' if shape.isNull() else hashlib.sha256(payload.encode()).hexdigest()
   if data['version']!=__version__ or data['key']!=key or data['token']!=token:return False
   if not set(data['parameters'])<=_NAMES:return False
   if self.has_manifest(key,manifest):return True
   parameters={n:tuple(v) if isinstance(v,list) else v for n,v in data['parameters'].items()}
   self._put(dict(key=key,parameters=parameters,inputs=data['inputs'],shape=shape.copy(),**({'payload':payload} if payload is not None else {})));return True
  except (ValueError,KeyError,TypeError,AttributeError):return False

COMPONENTS=ComponentCache()
_INTERSECTIONS=OrderedDict()
def cached_overlap(a,b):
 key=tuple(sorted((shape_token(a),shape_token(b))))
 if key in _INTERSECTIONS:
  _INTERSECTIONS.move_to_end(key);return _INTERSECTIONS[key]
 value=a.common(b).Volume;_INTERSECTIONS[key]=value
 while len(_INTERSECTIONS)>2048:_INTERSECTIONS.popitem(last=False)
 return value

class NativeStageCache:
 """Small, memory-only cache of drilled structural blanks.

 These stages have no upstream shapes. Store an independent native copy,
 without serialising intermediate BReps or adding disk-cache records.
 """
 def __init__(self,max_entries=14):
  self.max_entries=max_entries;self.entries=OrderedDict();self.serial=0
  self.hits=0;self.misses=0
 def clear(self):self.entries.clear();self.hits=self.misses=0
 def get(self,key,p,builder):
  from .parameter_memo import parameter_signature
  for serial in reversed(self.entries):
   role,values,shape=self.entries[serial]
   if role==key and all(object.__getattribute__(p,n)==v for n,v in values.items()):
    self.entries.move_to_end(serial);self.hits+=1
    if hasattr(p,'_reads'):p._reads.update(values)
    return shape.copy()
  signature=parameter_signature(p);traced=TrackedParameters(*signature);object.__setattr__(traced,'_reads',set());object.__setattr__(traced,'_parameter_signature',signature)
  shape=builder(traced)
  values={n:object.__getattribute__(p,n) for n in traced._reads}
  if hasattr(p,'_reads'):p._reads.update(values)
  self.serial+=1;self.entries[self.serial]=(key,values,shape.copy());self.misses+=1
  while len(self.entries)>self.max_entries:self.entries.popitem(last=False)
  return shape

class BuildCollisions:
 """Short-lived exact broad phase for immutable solids in assembly validation."""
 def __init__(self):self._bounds={};self._overlaps={};self._solid_bounds={};self._exact=0;self._skipped=0;self._elapsed=0.
 def bounds(self,shape):
  key=id(shape)
  if key not in self._bounds:
   self._bounds[key]=(shape,None if shape.isNull() else shape.BoundBox)
  return self._bounds[key][1]
 def solid_bounds(self,shape):
  key=id(shape)
  if key not in self._solid_bounds:
   # Only compound/multi-solid shapes benefit. A single solid uses its
   # existing full bounding box; never decompose curved faces or mesh them.
   # Preserve fallback for non-solid shapes and unsupported CAD wrappers.
   try:
    solids=shape.Solids
    self._solid_bounds[key]=tuple(s.BoundBox for s in solids) if len(solids)>1 else (self.bounds(shape),) if len(solids)==1 else ()
   except (AttributeError,RuntimeError):self._solid_bounds[key]=()
  return self._solid_bounds[key]
 def report(self):
  return dict(exact_check_requests=self._exact,compound_skips=self._skipped,seconds=self._elapsed)
 def overlap(self,a,b):
  aa,bb=self.bounds(a),self.bounds(b)
  if aa is None or bb is None:return 0.
  if (min(aa.XMax,bb.XMax)<=max(aa.XMin,bb.XMin) or
      min(aa.YMax,bb.YMax)<=max(aa.YMin,bb.YMin) or
      min(aa.ZMax,bb.ZMax)<=max(aa.ZMin,bb.ZMin)):return 0.
  key=tuple(sorted((id(a),id(b))))
  if key not in self._overlaps:
   from .geometry_bounds import disjoint_groups
   first,second=self.solid_bounds(a),self.solid_bounds(b)
   if (len(first)>1 or len(second)>1) and disjoint_groups(first,second):
    self._overlaps[key]=0.;self._skipped+=1
   else:
    start=time.perf_counter();self._overlaps[key]=cached_overlap(a,b)
    self._elapsed+=time.perf_counter()-start;self._exact+=1
  return self._overlaps[key]

def clear_geometry_caches():
 COMPONENTS.clear();_INTERSECTIONS.clear();_IDENTITIES.clear()
