"""Memoized pure layouts retain provenance even when called from a warm cache."""
from functools import lru_cache,wraps
from collections import OrderedDict

def parameter_signature(p):
 """Snapshot immutable fields once, without recording incidental cache reads."""
 try:return object.__getattribute__(p,'_parameter_signature')
 except AttributeError:
  signature=tuple(object.__getattribute__(p,n) for n in p.__dataclass_fields__)
  object.__setattr__(p,'_parameter_signature',signature)
  return signature

def parameter_cache(maxsize=128):
 def decorate(fn):
  recent=OrderedDict()
  @lru_cache(maxsize=maxsize)
  def cached(signature,args,kwargs):
   # Lazy import avoids a schema/FPV import cycle during workbench startup.
   from .dependency_cache import TrackedParameters
   names=tuple(TrackedParameters.__dataclass_fields__)
   group=(args,kwargs)
   entries=recent.get(group,[])
   for old_values,value,reads in reversed(entries):
    if all(signature[index]==old for index,old in old_values):
     recent.move_to_end(group);return value,reads
   p=TrackedParameters(*signature);object.__setattr__(p,'_reads',set())
   value=fn(p,*args,**dict(kwargs))
   reads=frozenset(p._reads)
   entries.append((tuple((names.index(n),signature[names.index(n)]) for n in reads),value,reads))
   recent[group]=entries[-4:];recent.move_to_end(group)
   while len(recent)>maxsize:recent.popitem(last=False)
   return value,reads
  @wraps(fn)
  def wrapped(p,*args,**kwargs):
   signature=parameter_signature(p)
   value,reads=cached(signature,args,tuple(sorted(kwargs.items())))
   if hasattr(p,'_reads'):p._reads.update(reads)
   return value
  def clear():cached.cache_clear();recent.clear()
  wrapped.cache_clear=clear;wrapped.cache_info=cached.cache_info
  return wrapped
 return decorate
