import unittest,json
from unittest.mock import patch
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.cutouts import PATTERN_DEFAULTS,encode_patterns,pattern_instances
try:
 from freecad.rotorforge import airflow_gui as ui
 from PySide6 import QtTest
except ImportError:ui=None
@unittest.skipIf(ui is None,'Qt unavailable')
class CutoutLocatorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.app=ui.QtWidgets.QApplication.instance() or ui.QtWidgets.QApplication([])
 def setUp(self):
  self.p=Parameters();self.e=ui.AirflowEditor(lambda:self.p);self.e.preview.resize(640,320)
  self.patterns=[dict(PATTERN_DEFAULTS,shape='Circle',x=-9.,y=-20.,width=10.),dict(PATTERN_DEFAULTS,shape='Rectangle',x=-9.,y=-20.,width=8.,length=8.),dict(PATTERN_DEFAULTS,role='BottomPlate',shape='Diamond',x=10.,y=25.,enabled=False)]
  self.e.set_json(encode_patterns(self.patterns))
 def tearDown(self):self.e.close();self.e.deleteLater()
 def screen(self,x,y):return self.e.preview.view()[1].map(ui.QtCore.QPointF(x,y))
 def click(self,x,y):QtTest.QTest.mouseClick(self.e.preview,ui.QtCore.Qt.LeftButton,ui.QtCore.Qt.NoModifier,self.screen(x,y).toPoint())
 def test_search_and_part_filter_do_not_change_saved_patterns(self):
  events=[];self.e.changed.connect(events.append);before=encode_patterns(self.e.patterns)
  self.e.find_pattern.setText('8x8');self.assertEqual([i for i in range(3) if not self.e.pattern_list.item(i).isHidden()],[1])
  self.e.find_pattern.setText('-9,-20');self.assertEqual([i for i in range(3) if not self.e.pattern_list.item(i).isHidden()],[0,1])
  self.e.find_pattern.setText('diamond off');self.assertEqual([not self.e.pattern_list.item(i).isHidden() for i in range(3)],[False,False,True])
  self.e.filter_role.setCurrentIndex(self.e.filter_role.findData('TopPlate'));self.assertTrue(all(self.e.pattern_list.item(i).isHidden() for i in range(3)))
  self.assertEqual(encode_patterns(self.e.patterns),before);self.assertFalse(events)
 def test_exact_number_search_and_original_indices(self):
  values=[dict(PATTERN_DEFAULTS,x=float(i)) for i in range(20)];self.e.set_json(encode_patterns(values))
  self.e.find_pattern.setText('#2');self.assertEqual([i for i in range(20) if not self.e.pattern_list.item(i).isHidden()],[1])
  self.assertTrue(self.e.choose_pattern(1));self.e.inputs['width'].setValue(7.);self.e.apply_pattern()
  self.assertEqual(self.e.patterns[1]['width'],7.);self.assertEqual(self.e.patterns[0]['width'],4.)
 def test_preview_click_cycles_overlapping_saved_patterns(self):
  before=encode_patterns(self.e.patterns);self.click(-9,-20);self.assertEqual(self.e._selected_index,1)
  self.click(-9,-20);self.assertEqual(self.e._selected_index,0)
  self.click(-9,-20);self.assertEqual(self.e._selected_index,1)
  self.assertEqual(encode_patterns(self.e.patterns),before)
 def test_picking_rotated_array_selects_the_whole_pattern(self):
  p=dict(PATTERN_DEFAULTS,x=0.,y=0.,columns=2,rows=2,pitch_x=16.,pitch_y=20.,rotation=35.)
  self.e.set_json(encode_patterns([p]));instance=list(pattern_instances(self.e.patterns[0]))[-1]
  self.click(instance['x'],instance['y']);self.assertEqual(self.e._selected_index,0)
  self.assertEqual(self.e.inputs['columns'].value(),2);self.assertEqual(len(self.e.preview.records()[0][1]),4)
  self.e._selected_index=-1;self.e.pattern_list.setCurrentRow(-1);self.click(0,0);self.assertEqual(self.e._selected_index,0)
 def test_unapplied_edits_survive_list_and_preview_selection(self):
  self.e.choose_pattern(0);self.e.inputs['width'].setValue(12.)
  self.e.pattern_list.setCurrentRow(1);self.assertEqual(self.e._selected_index,0);self.assertEqual(self.e.pattern_list.currentRow(),0)
  self.assertEqual(self.e.inputs['width'].value(),12.);self.assertTrue(self.e.has_pending_changes())
  self.click(-9,-20);self.assertEqual(self.e._selected_index,0)
  self.e.discard_changes();self.assertTrue(self.e.choose_pattern(1));self.assertFalse(self.e.has_pending_changes())
 def test_disabled_patterns_are_editable_without_expanding_every_inactive_array(self):
  values=[dict(PATTERN_DEFAULTS,enabled=False,columns=20,rows=20) for _ in range(200)]
  self.e.set_json(encode_patterns(values));self.assertEqual(len(self.e.preview.records()),0)
  self.e.choose_pattern(0);self.assertEqual(len(self.e.preview.records()),1);self.assertEqual(len(self.e.preview.records()[0][1]),400)
 def test_filtered_selection_keeps_an_explicit_number_and_zoom_can_reset(self):
  self.e.choose_pattern(0);self.e.preview.zoom_selected();self.assertTrue(self.e.preview._focus)
  self.assertLess(self.e.preview.view()[1].m11(),100.)
  self.e.find_pattern.setText('Diamond');self.assertIn('Selected #1 (hidden',self.e.filter_count.text());self.assertEqual(self.e.apply_button.text(),'Apply to #1')
  self.assertFalse(self.e.zoom_button.isEnabled());self.e.preview.fit_plate();self.assertFalse(self.e.preview._focus)
 def test_hit_cache_reuses_paths_and_preview_paints(self):
  self.e.preview.records()
  with patch.object(ui,'cutout_path',wraps=ui.cutout_path) as build:
   self.e.preview.records();self.e.choose_pattern(1);self.e.preview.records();self.assertEqual(build.call_count,0)
  self.e.preview.grab();self.assertIsNone(self.e.preview.last_error)
