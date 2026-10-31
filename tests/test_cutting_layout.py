from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.cutting_layout import arrange_profiles,stock_token,ARM_ROLES
class CuttingLayoutTests(unittest.TestCase):
 def test_stock_groups_clearance_and_margin(self):
  items=[dict(role=str(i),width=110+i,height=70,thickness=2 if i%2 else 5) for i in range(9)]
  layout=arrange_profiles(items);self.assertEqual([s['thickness'] for s in layout['sheets']],[2,5])
  self.assertEqual(sum(len(s['parts']) for s in layout['sheets']),9)
  for sheet in layout['sheets']:
   for i,a in enumerate(sheet['parts']):
    self.assertGreaterEqual(a['x'],10);self.assertGreaterEqual(a['y'],10)
    self.assertLessEqual(a['x']+a['width'],sheet['width']-10)
    for b in sheet['parts'][i+1:]:
     self.assertTrue(a['x']+a['width']+12<=b['x'] or b['x']+b['width']+12<=a['x'] or a['y']+a['height']+12<=b['y'] or b['y']+b['height']+12<=a['y'])
  self.assertGreaterEqual(layout['sheets'][1]['combined_y'],layout['sheets'][0]['height']+30)
 def test_stable_order_no_rotation_and_large_part(self):
  items=[dict(role='large',width=500.,height=80.,thickness=2.5),dict(role='next',width=20.,height=30.,thickness=2.5)]
  a=arrange_profiles(items);self.assertEqual(a,arrange_profiles(items));self.assertEqual(a['sheets'][0]['parts'][0]['width'],500)
  self.assertGreater(a['sheets'][0]['parts'][1]['y'],10);self.assertEqual(stock_token(2.5),'2p5mm')
 def test_invalid_dimensions(self):
  for value in (0,-1,float('nan'),float('inf')):
   with self.assertRaises(ValueError):arrange_profiles([dict(role='bad',width=value,height=30,thickness=2)])
 def test_complete_arm_row_even_when_wider_than_target(self):
  items=[dict(role='BottomPlate',width=50,height=100,thickness=5)]+[dict(role=r,width=130,height=180+i,thickness=5) for i,r in enumerate(reversed(ARM_ROLES))]
  sheet=arrange_profiles(items)['sheets'][0];arms=sheet['parts'][:4]
  self.assertEqual([a['role'] for a in arms],list(ARM_ROLES))
  self.assertEqual([a['y'] for a in arms],[10]*4)
  self.assertGreater(sheet['width'],420)
  for a,b in zip(arms,arms[1:]):self.assertEqual(b['x']-a['x']-a['width'],4)
  self.assertGreaterEqual(sheet['parts'][4]['y'],max(a['y']+a['height'] for a in arms)+12)
if __name__=='__main__':unittest.main()
