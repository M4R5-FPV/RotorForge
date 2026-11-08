"""Export must not be blocked by optional bumper STEP quality checks."""
import tempfile
import unittest
from pathlib import Path
from freecad.rotorforge.step_safety import export_bumper_step

class FakeSolid:
    def __init__(self, data=b'step', faces=5, fail=False):
        self.Solids = [self]
        self.Faces = list(range(faces))
        self.data = data
        self.fail = fail
    def isValid(self): return True
    def copy(self): return FakeSolid(self.data, len(self.Faces), self.fail)
    def exportStep(self, filename):
        if self.fail: raise RuntimeError('optional optimised STEP failed')
        Path(filename).write_bytes(self.data)

class FakeCompound(FakeSolid):
    def __init__(self, only_solid, data=b'original'):
        super().__init__(data, len(only_solid.Faces)+1)
        self.Solids = [only_solid]

class StepTests(unittest.TestCase):
    def test_ordinary_bumper_uses_legacy_step(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'FrontBumper_print.step'
            original=FakeSolid()
            self.assertEqual(export_bumper_step(original,path),path)
            self.assertEqual(path.read_bytes(),b'step')
    def test_extra_faces_are_not_exported_when_solid_succeeds(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'FrontBumper_print.step'
            assert export_bumper_step(FakeCompound(FakeSolid(b'clean')),path)==path
            self.assertEqual(path.read_bytes(),b'clean')
    def test_failed_optional_isolation_falls_back_to_baseline_export(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'FrontBumper_print.step'
            self.assertEqual(export_bumper_step(FakeCompound(FakeSolid(fail=True)),path),path)
            self.assertEqual(path.read_bytes(),b'original')
    def test_missing_solid_data_does_not_block_baseline_export(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'FrontBumper_print.step'
            source=FakeSolid(b'valid-legacy');source.Solids=[]
            self.assertEqual(export_bumper_step(source,path),path)
            self.assertEqual(path.read_bytes(),b'valid-legacy')

if __name__ == '__main__': unittest.main()
