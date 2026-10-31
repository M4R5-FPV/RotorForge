"""Independent rear reach must preserve the front pair and existing mounting geometry."""
from dataclasses import replace
from pathlib import Path
import math,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters,motor_centres,arm_layouts,validate,save_parameters,load_parameters
class DeadcatExtensionTests(unittest.TestCase):
 def test_extension_is_measured_along_each_rear_arm(self):
  for width in (250,330):
   for spread in (1.,1.2,1.4):
    p=Parameters(Layout='Deadcat',Wheelbase=width,FrontSpread=spread)
    base=arm_layouts(p)
    for extra in (0.,10.,30.5,100.):
     arms=arm_layouts(replace(p,RearArmExtension=extra))
     self.assertEqual(motor_centres(p)[:2],motor_centres(replace(p,RearArmExtension=extra))[:2])
     for i,(a,b) in enumerate(zip(base,arms)):
      self.assertEqual(a['root'],b['root'])
      for x,y in zip(a['unit'],b['unit']):self.assertAlmostEqual(x,y)
      for before,after in zip(a['bolts'],b['bolts']):self.assertAlmostEqual(math.dist(before,after),0)
      self.assertAlmostEqual(b['length']-a['length'],extra if i>=2 else 0)
      if i>=2:self.assertAlmostEqual(math.dist(a['motor'],b['motor']),extra)
 def test_mirror_symmetry_and_larger_diagonals(self):
  p=Parameters(Layout='Deadcat',RearArmExtension=25)
  fr,fl,rl,rr=motor_centres(p)
  self.assertEqual(rl,(-rr[0],rr[1]));self.assertEqual(fr,(-fl[0],fl[1]))
  self.assertAlmostEqual(math.dist(fr,rl),math.dist(fl,rr))
  self.assertGreater(math.dist(fr,rl),p.Wheelbase)
  self.assertGreater(abs(rr[0]),abs(motor_centres(replace(p,RearArmExtension=0))[3][0]))
  self.assertLess(rr[1],motor_centres(replace(p,RearArmExtension=0))[3][1])
 def test_other_layouts_ignore_but_retain_saved_extension(self):
  for layout in ('True X','Stretched X'):
   p=Parameters(Layout=layout,RearArmExtension=25)
   self.assertEqual(motor_centres(p),motor_centres(replace(p,RearArmExtension=0)))
   self.assertEqual(Parameters.from_dict(p.to_dict()).RearArmExtension,25)
 def test_older_settings_default_to_original_layout(self):
  data=Parameters(Layout='Deadcat').to_dict();data.pop('RearArmExtension')
  p=Parameters.from_dict(data)
  self.assertEqual(p.RearArmExtension,0)
  self.assertAlmostEqual(math.dist(motor_centres(p)[0],motor_centres(p)[2]),p.Wheelbase)
 def test_json_save_reload_and_reject_invalid_values(self):
  p=Parameters(Layout='Deadcat',RearArmExtension=18.25)
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'frame.json';save_parameters(path,p);self.assertEqual(load_parameters(path),p)
  for value in (-1,301):self.assertTrue(any('Rear arm extension' in e for e in validate(replace(p,RearArmExtension=value))[0]))
  for value in (float('nan'),float('inf'),True,'25'):
   with self.assertRaises(ValueError):Parameters.from_dict(dict(p.to_dict(),RearArmExtension=value))
if __name__=='__main__':unittest.main()
