"""Memoized pure layouts retain provenance even when called from a warm cache."""
from functools import lru_cache,wraps

def parameter_signature(p):
 """Snapshot immutable fields once, without recording incidental cache reads."""
 try:return object.__getattribute__(p,'_parameter_signature')
 except AttributeError:
  signature=tuple(object.__getattribute__(p,n) for n in p.__dataclass_fields__)
  object.__setattr__(p,'_parameter_signature',signature)
  return signature

def parameter_cache(maxsize=128):
 def decorate(fn):
  @lru_cache(maxsize=maxsize)
  def cached(signature,args,kwargs):
   # Lazy import avoids a schema/FPV import cycle during workbench startup.
   from .dependency_cache import TrackedParameters
   p=TrackedParameters(*signature);object.__setattr__(p,'_reads',set())
   value=fn(p,*args,**dict(kwargs))
   return value,frozenset(p._reads)
  @wraps(fn)
  def wrapped(p,*args,**kwargs):
   signature=parameter_signature(p)
   value,reads=cached(signature,args,tuple(sorted(kwargs.items())))
   if hasattr(p,'_reads'):p._reads.update(reads)
   return value
  wrapped.cache_clear=cached.cache_clear;wrapped.cache_info=cached.cache_info
  return wrapped
 return decorate
