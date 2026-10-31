import unittest, math
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate,strap_slots,plate_levels,stack_reference_z
from freecad.rotorforge.strap_openings import notch_polygons
from freecad.rotorforge.reference_options import stack_usb_centre
from shapely.geometry import Polygon

class USBStrapTests(unittest.TestCase):
 def test_legacy_and_modes_preserve_slots(self):
  p=Parameters.from_dict({'StrapSlotWidth':4.,'StrapSlotLength':20.,'StrapEdgeInset':6.})
  self.assertEqual(len(strap_slots(p)),4)
  for style in ('Slots','Outline cutouts'):
   q=replace(p,StrapOpeningStyle=style)
   self.assertEqual(Parameters.from_dict(q.to_dict()),q)
   self.assertEqual(len(strap_slots(q)),4 if style=='Slots' else 0)
   self.assertEqual(len(notch_polygons(q)),4 if style=='Outline cutouts' else 0)
   self.assertEqual(strap_slots(replace(q,StrapOpeningStyle='Slots')),strap_slots(p))
  self.assertFalse(notch_polygons(replace(p,StrapSlotsEnabled=False,StrapOpeningStyle='Outline cutouts')))
 def test_notches_are_valid_and_symmetric(self):
  for kw in ({},{'TopCentreWidth':60.,'CentreSectionLength':60.},{'TopPlateShape':'Tapered front'}):
   p=Parameters(StrapOpeningStyle='Outline cutouts',**kw)
   self.assertFalse(validate(p)[0])
   polys=notch_polygons(p)
   for poly in polys:self.assertTrue(Polygon(poly).is_valid);self.assertGreater(Polygon(poly).area,0)
   for a,b in zip(polys[::2],polys[1::2]):self.assertEqual(a,tuple((-x,y) for x,y in b))
 def test_protects_hardware_web_and_ends(self):
  p=Parameters(StrapOpeningStyle='Outline cutouts')
  for kw in ({'StrapNotchDepth':30.},{'StrapNotchDepth':-1.},{'StrapOffsetY':1.},{'StrapOffsetY':50.},{'StrapNotchDepth':10.,'StrapOffsetY':42.}):
   self.assertTrue(validate(replace(p,**kw))[0],kw)
 def test_port_tracks_stack_and_validates_offsets(self):
  p=Parameters(DetailedStackReference=True)
  for spacing in (20.,30.5):
   for side in ('Left','Right'):
    q=replace(p,StackSpacing=spacing,StackUSBFace=side,StackUSBOffsetY=-2.,StackOffsetY=3.)
    x,y,z=stack_usb_centre(q)
    self.assertEqual(y,1.);self.assertEqual(x<0,side=='Left')
    self.assertAlmostEqual(stack_usb_centre(replace(q,StackMountHeight=q.StackMountHeight+2))[2],z+2)
    self.assertFalse(validate(q)[0])
   self.assertTrue(validate(replace(p,StackSpacing=spacing,StackUSBOffsetY=20.))[0])
 def test_preview_really_opens_outline(self):
  from freecad.rotorforge.airflow_gui import finished_part_path,QtCore
  p=Parameters(StrapOpeningStyle='Outline cutouts')
  for x in (-p.TopWidth/2+1,p.TopWidth/2-1):
   point=QtCore.QPointF(x,p.StrapOffsetY)
   self.assertFalse(finished_part_path(p,'TopPlate').contains(point))
   self.assertTrue(finished_part_path(replace(p,StrapSlotsEnabled=False),'TopPlate').contains(point))
