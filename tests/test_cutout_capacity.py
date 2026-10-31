"""Capacity regression: older detailed designs must accept new outline patterns."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.cutouts import PATTERN_DEFAULTS,MAX_PATTERNS,encode_patterns,parse_patterns
class CutoutCapacityTests(unittest.TestCase):
 def test_add_outline_to_32_existing_patterns(self):
  old=[dict(PATTERN_DEFAULTS,x=i) for i in range(32)]
  notch=dict(PATTERN_DEFAULTS,mode='Outline notch',shape='Circle',x=25,width=6)
  saved=parse_patterns(encode_patterns(old+[notch]))
  self.assertEqual(saved[:32],old);self.assertEqual(saved[-1],notch)
 def test_full_capacity_and_grid_budget(self):
  patterns=[dict(PATTERN_DEFAULTS) for _ in range(200)]
  self.assertEqual(len(parse_patterns(encode_patterns(patterns))),200)
  with self.assertRaises(ValueError):encode_patterns(patterns+[dict(PATTERN_DEFAULTS)])
  patterns=[dict(PATTERN_DEFAULTS,columns=20,rows=10),dict(PATTERN_DEFAULTS)]
  with self.assertRaisesRegex(ValueError,'enabled cutouts'):encode_patterns(patterns)
  patterns[-1]['enabled']=False
  self.assertEqual(len(parse_patterns(encode_patterns(patterns))),2)
 def test_disabled_patterns_are_still_bounded(self):
  with self.assertRaises(ValueError):encode_patterns([dict(PATTERN_DEFAULTS,enabled=False)]*(MAX_PATTERNS+1))
if __name__=='__main__':unittest.main()
