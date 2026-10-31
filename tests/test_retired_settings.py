"""Earlier optional settings import without restoring removed controls."""
import unittest
from dataclasses import fields
from freecad.rotorforge.parameters import Parameters,RETIRED_PARAMETERS
from freecad.rotorforge.editor_sections import FIELD_LOCATION,SECTIONS
class RetiredSettingsTests(unittest.TestCase):
 def test_import_keeps_supported_dimensions(self):
  p=Parameters(Layout='Deadcat',CameraTopRearOffset=4,LiPoPadEnabled=True,LiPoPadPattern='Hexagon cells')
  data=p.to_dict();data.update({name:'discarded' for name in RETIRED_PARAMETERS})
  self.assertEqual(Parameters.from_dict(data),p)
 def test_retired_values_are_not_saved(self):
  self.assertFalse(RETIRED_PARAMETERS.intersection(Parameters().to_dict()))
  self.assertFalse(RETIRED_PARAMETERS.intersection(FIELD_LOCATION))
  self.assertEqual({category for category,*rest in SECTIONS},{'Frame','Arms','Hardware','Battery','FPV','Finishing','TPU'})
 def test_other_unknown_keys_still_rejected(self):
  with self.assertRaisesRegex(ValueError,'Unknown parameter'):
   Parameters.from_dict(dict(Parameters().to_dict(),UnexpectedSetting=1))
