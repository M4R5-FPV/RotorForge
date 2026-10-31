import unittest
from collections import Counter
from freecad.rotorforge.mesh_cleanup import weld_micro_seams
class Mesh:
 def __init__(self,triangles):
  vertices=[];faces=[];lookup={}
  for triangle in triangles:
   face=[]
   for p in triangle:
    p=tuple(p)
    if p not in lookup:lookup[p]=len(vertices);vertices.append(p)
    face.append(lookup[p])
   faces.append(tuple(face))
  self.Topology=vertices,faces
 def isSolid(self):
  _,faces=self.Topology
  counts=Counter(tuple(sorted((a,b))) for f in faces for a,b in zip(f,f[1:]+f[:1]))
  return bool(counts) and all(c==2 for c in counts.values())
def tetra(gap=0):
 a,b,c,d=(0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)
 shifted=(gap,0.,0.)
 return Mesh([(a,c,b),(shifted,b,d),(b,c,d),(c,a,d)])
class MeshCleanupTests(unittest.TestCase):
 def test_already_closed_mesh_is_untouched(self):
  m=tetra();self.assertTrue(m.isSolid());self.assertIs(weld_micro_seams(m,Mesh),m)
 def test_microscopic_seam_closes_without_mutating_input(self):
  m=tetra(1e-6);self.assertFalse(m.isSolid());r=weld_micro_seams(m,Mesh)
  self.assertTrue(r.isSolid());self.assertFalse(m.isSolid());self.assertEqual(len(r.Topology[1]),4)
 def test_real_opening_is_not_filled(self):
  m=tetra(.1);self.assertIs(weld_micro_seams(m,Mesh),m);self.assertFalse(m.isSolid())
 def test_incomplete_repair_keeps_original_mesh(self):
  m=tetra(1e-6);points,faces=m.Topology;m=Mesh([tuple(points[i] for i in f) for f in faces[:-1]])
  self.assertIs(weld_micro_seams(m,Mesh),m)
