"""Portable new cutout profiles, retained legacy choices and pattern layout."""
from pathlib import Path
import math,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.cutouts import CUTOUT_TYPES,PATTERN_DEFAULTS,cutout_polygon,encode_patterns,parse_patterns,pattern_instances

class AirflowShapeTests(unittest.TestCase):
    def test_existing_shapes_are_retained_first(self):
        self.assertEqual(CUTOUT_TYPES[:4],('Circle','Slot','Rounded rectangle','Hexagon'))
        self.assertEqual(len(set(CUTOUT_TYPES)),20)

    def test_polygon_dimensions_follow_width_and_length(self):
        for name in CUTOUT_TYPES:
            points=cutout_polygon(dict(PATTERN_DEFAULTS,shape=name,width=10,length=20))
            if not points:continue
            self.assertAlmostEqual(max(x for x,y in points)-min(x for x,y in points),10)
            self.assertAlmostEqual(max(y for x,y in points)-min(y for x,y in points),20)
            self.assertTrue(all(math.isfinite(v) for pt in points for v in pt))

    def test_familiar_polygon_areas_and_concave_chevron(self):
        for name,expected in (('Rectangle',200),('Triangle',100),('Diamond',100),('Trapezoid',150),('Chevron',100)):
            points=cutout_polygon(dict(PATTERN_DEFAULTS,shape=name,width=10,length=20))
            area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1])))/2
            self.assertAlmostEqual(area,expected)
        self.assertIn((0,0),cutout_polygon(dict(PATTERN_DEFAULTS,shape='Chevron')))

    def test_every_shape_roundtrips_with_overlapping_patterns(self):
        patterns=[dict(PATTERN_DEFAULTS,shape=name,x=0,columns=2,pitch_x=1) for name in CUTOUT_TYPES]
        self.assertEqual(parse_patterns(encode_patterns(patterns)),patterns)

    def test_rotation_moves_grid_without_changing_shapes(self):
        p=dict(PATTERN_DEFAULTS,shape='Ellipse',columns=3,pitch_x=4,rotation=90)
        instances=list(pattern_instances(p));self.assertEqual(len(instances),3)
        self.assertTrue(all(abs(i['x'])<1e-9 for i in instances))
        self.assertEqual([i['y'] for i in instances],[-4,0,4])
        self.assertTrue(all(i['shape']=='Ellipse' and i['rotation']==90 for i in instances))

    def test_invalid_names_and_dimensions_still_fail(self):
        for changes in ({'shape':'Unknown'},{'width':0},{'length':float('nan')},{'rows':21}):
            with self.assertRaises(ValueError):encode_patterns([dict(PATTERN_DEFAULTS,**changes)])

if __name__=='__main__':unittest.main()
