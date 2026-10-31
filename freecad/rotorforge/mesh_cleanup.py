"""Conservative repair of sub-micron STL tessellation seams."""
from collections import Counter,defaultdict
from itertools import product
import math

def weld_micro_seams(mesh,factory=None,tolerance=1e-4):
 """Weld only unmatched vertices within 0.0001 mm; never fill a real opening.
 A valid CAD solid can acquire microscopic boundary edges when tessellation
 coordinates are stored as floats. Keep the source mesh unless a closed result
 is obtained. Already-closed meshes take the fast path without reconstruction.
 """
 if mesh.isSolid():return mesh
 points,faces=mesh.Topology
 edges=Counter(tuple(sorted((a,b))) for face in faces for a,b in zip(face,face[1:]+face[:1]))
 boundary=sorted({i for (a,b),count in edges.items() if count!=2 for i in (a,b)})
 buckets=defaultdict(list);remap={};offsets=tuple(product((-1,0,1),repeat=3))
 for i in boundary:
  point=points[i];key=tuple(math.floor(v/tolerance) for v in point)
  candidates=(j for offset in offsets for j in buckets[tuple(a+b for a,b in zip(key,offset))])
  representative=next((j for j in candidates if sum((a-b)**2 for a,b in zip(point,points[j]))<=tolerance*tolerance),i)
  remap[i]=representative
  if representative==i:buckets[key].append(i)
 if all(i==j for i,j in remap.items()):return mesh
 triangles=[];seen=set()
 for face in faces:
  ids=tuple(remap.get(i,i) for i in face);key=tuple(sorted(ids))
  if len(set(ids))<3 or key in seen:continue
  seen.add(key);triangles.append(tuple(points[i] for i in ids))
 if factory is None:
  import Mesh
  factory=Mesh.Mesh
 repaired=factory(triangles)
 return repaired if repaired.isSolid() else mesh
