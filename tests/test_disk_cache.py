"""Native cache archives are disposable, bounded and tied to exact inputs."""
import json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from freecad.rotorforge import disk_cache as d
class DiskCacheTests(unittest.TestCase):
 def records(self):return [('TopPlate',json.dumps(dict(key='TopPlate')),'native geometry')]
 def test_exact_identity_and_runtime(self):
  self.assertEqual(d.cache_key((1,'a'),{'occ':'a'}),d.cache_key((1,'a'),{'occ':'a'}))
  self.assertNotEqual(d.cache_key((1,'a'),{'occ':'a'}),d.cache_key((2,'a'),{'occ':'a'}))
  self.assertNotEqual(d.cache_key((1,'a'),{'occ':'a'}),d.cache_key((1,'a'),{'occ':'b'}))
 def test_roundtrip_and_unknown_key(self):
  with tempfile.TemporaryDirectory() as t:
   self.assertTrue(d.write_archive(t,'test',self.records()));self.assertEqual(d.read_archive(t,'test'),self.records())
   self.assertEqual(d.read_archive(t,'other'),[]);self.assertFalse(list(Path(t).glob('*.tmp')))
 def test_truncation_and_payload_tampering_fall_back(self):
  with tempfile.TemporaryDirectory() as t:
   d.write_archive(t,'test',self.records());path=Path(t)/'test.zip'
   with zipfile.ZipFile(path) as z:index=z.read('index.json')
   with zipfile.ZipFile(path,'w') as z:z.writestr('index.json',index);z.writestr('0.brep','changed geometry')
   self.assertEqual(d.read_archive(t,'test'),[]);path.write_bytes(b'PKbroken');self.assertEqual(d.read_archive(t,'test'),[])
 def test_wrong_role_and_configuration_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   d.write_archive(t,'test',[('TopPlate',json.dumps(dict(key='BottomPlate')),'data')]);self.assertEqual(d.read_archive(t,'test'),[])
   d.write_archive(t,'test',self.records());(Path(t)/'test.zip').rename(Path(t)/'other.zip');self.assertEqual(d.read_archive(t,'other'),[])
 def test_storage_failure_does_not_block_build(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'file';path.write_text('occupied');self.assertFalse(d.write_archive(path,'test',self.records()));self.assertEqual(d.read_archive(path,'test'),[])
 def test_count_and_unpacked_limits(self):
  with tempfile.TemporaryDirectory() as t:
   with patch.object(d,'MAX_FILES',2):
    for i in range(4):d.write_archive(t,str(i),self.records())
   self.assertEqual(len(list(Path(t).glob('*.zip'))),2)
   with patch.object(d,'MAX_UNPACKED',3):
    self.assertFalse(d.write_archive(t,'huge',self.records()));self.assertEqual(d.read_archive(t,'3'),[])
