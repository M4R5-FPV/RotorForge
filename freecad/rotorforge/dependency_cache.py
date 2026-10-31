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
  self.entries=OrderedDict();self.max_entries=max_entries;self.max_bytes=max_bytes;self.bytes=0;self.serial=0;self.events=[];self.latest={};self.last_entry=None
 def clear(self):self.entries.clear();self.bytes=0;self.latest.clear();self.events=[];self.last_entry=None
 def begin(self):self.events=[]
 def get(self,key,p,inputs,builder):
  start=time.perf_counter();values=inputs or {}
  for serial,entry in reversed(list(self.entries.items())):
   if entry['key']!=key:continue
   if any(getattr(p,n)!=v for n,v in entry['parameters'].items()):continue
   if any(shape_token(values.get(n))!=token for n,token in entry['inputs'].items()):continue
   self.entries.move_to_end(serial);self.latest[key]=entry;self.last_entry=entry
   self.events.append(dict(role=key,action='reused',seconds=time.perf_counter()-start));return copy_entry(entry)
  traced=TrackedParameters(*p.signature());object.__setattr__(traced,'_reads',set())
  upstream=ShapeInputs(values);shape=builder(traced,upstream)
  entry=self._put(dict(key=key,parameters={n:getattr(p,n) for n in sorted(traced._reads)},inputs=dict(upstream.reads),shape=shape.copy()))
  self.events.append(dict(role=key,action='rebuilt',seconds=time.perf_counter()-start));return copy_entry(entry)
 def _put(self,entry):
  if 'payload' not in entry:entry['payload']=entry['shape'].exportBrepToString()
  entry['token']='null' if entry['shape'].isNull() else hashlib.sha256(entry['payload'].encode()).hexdigest()
  remember_shape(entry['shape'],entry['token']);entry['bytes']=len(entry['payload'])
  self.serial+=1;self.entries[self.serial]=entry;self.bytes+=entry['bytes'];self.latest[entry['key']]=entry;self.last_entry=entry
  while self.entries and (len(self.entries)>self.max_entries or self.bytes>self.max_bytes):
   _,old=self.entries.popitem(last=False);self.bytes-=old['bytes']
   if self.latest.get(old['key']) is old:self.latest.pop(old['key'],None)
  return entry
 def manifest(self,key):
  entry=self.latest.get(key)
  if entry is None:return ''
  return json.dumps(dict(version=__version__,key=key,parameters=entry['parameters'],inputs=entry['inputs'],token=entry['token']),sort_keys=True,separators=(',',':'),allow_nan=False)
 def has_manifest(self,key,manifest):
  try:
   data=json.loads(manifest)
   return data['version']==__version__ and any(e['key']==key and e['token']==data['token'] and e['parameters']==data['parameters'] and e['inputs']==data['inputs'] for e in self.entries.values())
  except (ValueError,KeyError,TypeError):return False
 def seed(self,key,manifest,shape,payload=None):
  try:
   data=json.loads(manifest)
   token=shape_token(shape) if payload is None else 'null' if shape.isNull() else hashlib.sha256(payload.encode()).hexdigest()
   if data['version']!=__version__ or data['key']!=key or data['token']!=token:return False
   if not set(data['parameters'])<=_NAMES:return False
   if any(e['key']==key and e['token']==data['token'] and e['parameters']==data['parameters'] and e['inputs']==data['inputs'] for e in self.entries.values()):return True
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

def clear_geometry_caches():
 COMPONENTS.clear();_INTERSECTIONS.clear();_IDENTITIES.clear()
