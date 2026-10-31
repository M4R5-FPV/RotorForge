"""Portable outline settings and compatibility with interior airflow patterns."""
from pathlib import Path
from dataclasses import replace
import json,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.cutouts import PATTERN_DEFAULTS,CUTOUT_TYPES,OUTLINE_ROLES,parse_patterns,encode_patterns,pattern_instances
from freecad.rotorforge.parameters import Parameters,save_parameters,load_parameters

class OutlineNotchTests(unittest.TestCase):
    def test_old_patterns_default_to_interior(self):
        old=dict(PATTERN_DEFAULTS);old.pop('mode')
        self.assertEqual(parse_patterns(json.dumps([old]))[0]['mode'],'Interior')
    def test_all_shapes_and_plates_roundtrip(self):
        for role in OUTLINE_ROLES:
            for shape in CUTOUT_TYPES:
                p=dict(PATTERN_DEFAULTS,role=role,shape=shape,mode='Outline notch',columns=3,pitch_x=3)
                self.assertEqual(parse_patterns(encode_patterns([p])),[p])
                self.assertTrue(all(i['mode']=='Outline notch' for i in pattern_instances(p)))
    def test_unsupported_parts_and_modes_rejected(self):
        for change in ({'role':'ArmFrontRight'},{'role':'CameraMountLeft'},{'role':'ArmKeystone'},{'mode':'Anything'}):
            p=dict(PATTERN_DEFAULTS,mode='Outline notch');p.update(change)
            with self.assertRaises(ValueError):encode_patterns([p])
    def test_mixed_modes_preserve_settings(self):
        patterns=[dict(PATTERN_DEFAULTS),dict(PATTERN_DEFAULTS,mode='Outline notch',x=17,y=0)]
        p=Parameters.from_dict(dict(Parameters().to_dict(),CutoutPatterns=encode_patterns(patterns)))
        self.assertEqual(parse_patterns(p.CutoutPatterns),patterns)

if __name__=='__main__':unittest.main()
