"""Disposable native components for repeated builds across FreeCAD sessions.

Only successful builds are saved. Exact inputs and generator/CAD versions,
archive CRCs, BRep digests and shape validity must match. Loading seeds the
existing dependency cache; normal assembly validation still runs.
"""
from pathlib import Path
import hashlib,json,os,tempfile,zipfile
MAX_FILES=8
MAX_BYTES=128*1024*1024
MAX_UNPACKED=64*1024*1024
FORMAT=1

def cache_key(signature,runtime):
 from .version import __version__
 raw=json.dumps(dict(format=FORMAT,generator=__version__,runtime=runtime,parameters=signature),sort_keys=True,separators=(',',':'),allow_nan=False)
 return hashlib.sha256(raw.encode()).hexdigest()

def read_archive(directory,key):
 path=Path(directory)/(key+'.zip')
 try:
  with zipfile.ZipFile(path) as archive:
   infos=archive.infolist()
   if len(infos)>161 or sum(i.file_size for i in infos)>MAX_UNPACKED:return []
   index=json.loads(archive.read('index.json'))
   if index['format']!=FORMAT or index['key']!=key:return []
   records=[]
   for row in index['components']:
    manifest=row['manifest'];data=json.loads(manifest);payload=archive.read(row['file']).decode('utf-8')
    if hashlib.sha256(payload.encode()).hexdigest()!=row['digest'] or data['key']!=row['role']:return []
    records.append((row['role'],manifest,payload))
  try:os.utime(path,None)
  except OSError:pass
  return records
 except (OSError,ValueError,KeyError,TypeError,UnicodeError,zipfile.BadZipFile,RuntimeError):return []

def write_archive(directory,key,records):
 path=Path(directory);temporary=None
 try:
  if sum(len(payload.encode()) for role,manifest,payload in records)>MAX_UNPACKED or len(records)>160:return False
  path.mkdir(parents=True,exist_ok=True)
  with tempfile.NamedTemporaryFile(dir=path,suffix='.tmp',delete=False) as stream:temporary=Path(stream.name)
  index=dict(format=FORMAT,key=key,components=[])
  with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
   for i,(role,manifest,payload) in enumerate(records):
    name=str(i)+'.brep';archive.writestr(name,payload)
    index['components'].append(dict(role=role,manifest=manifest,file=name,digest=hashlib.sha256(payload.encode()).hexdigest()))
   archive.writestr('index.json',json.dumps(index,sort_keys=True,separators=(',',':')))
  os.replace(temporary,path/(key+'.zip'));temporary=None
  size=0
  for i,f in enumerate(sorted(path.glob('*.zip'),key=lambda f:f.stat().st_mtime,reverse=True)):
   size+=f.stat().st_size
   if i>=MAX_FILES or size>MAX_BYTES:f.unlink()
  return True
 except (OSError,ValueError,TypeError,zipfile.BadZipFile):return False
 finally:
  if temporary is not None:
   try:temporary.unlink()
   except OSError:pass

def location():
 if os.environ.get('ROTORFORGE_DISABLE_DISK_CACHE')=='1':return None
 if 'ROTORFORGE_CACHE_DIR' in os.environ:return Path(os.environ['ROTORFORGE_CACHE_DIR'])
 import FreeCAD as App
 getter=getattr(App,'getUserCachePath',None)
 root=getter() if getter else str(Path(App.getUserAppDataDir())/'Cache')
 return Path(root)/'RotorForge'/'components'

def identity(signature):
 import FreeCAD as App,Part
 return cache_key(signature,dict(freecad=list(App.Version()),occ=str(Part.OCC_VERSION)))

def restore(signature,cache):
 try:
  directory=location()
  if directory is None:return 0
  import Part
  from .version import __version__
  pending=[]
  for role,manifest,payload in read_archive(directory,identity(signature)):
   if cache.has_manifest(role,manifest):continue
   data=json.loads(manifest)
   if data['version']!=__version__:return 0
   shape=Part.Shape();shape.importBrepFromString(payload)
   if not shape.isNull() and not shape.isValid():return 0
   token='null' if shape.isNull() else hashlib.sha256(payload.encode()).hexdigest()
   if data['token']!=token:return 0
   pending.append((role,manifest,shape,payload))
  return sum(cache.seed(*row) for row in pending)
 except MemoryError:raise
 except Exception:return 0

def save(signature,cache):
 try:
  directory=location()
  if directory is None:return
  roles=dict.fromkeys(e['role'] for e in cache.events)
  records=[(role,cache.manifest(role),cache.latest[role]['payload']) for role in roles if role in cache.latest]
  write_archive(directory,identity(signature),records)
 except MemoryError:raise
 except Exception:pass  # Cache storage must never prevent a valid frame build.
