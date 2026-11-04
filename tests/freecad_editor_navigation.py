import FreeCAD as App
import sys,os,json,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
report={}
try:
 from freecad.rotorforge.gui import FrameDialog,QtWidgets,register_commands
 from freecad.rotorforge.parameters import Parameters
 d=FrameDialog();d.show();QtWidgets.QApplication.processEvents()
 categories=list(d.category_tabs)
 assert len(categories)==7
 for index,category in enumerate(categories):
  assert d.tabs.tabText(index)==''
  assert d.tabs.tabToolTip(index)==category
  assert not d.tabs.tabIcon(index).isNull()
  d.tabs.setCurrentIndex(index)
  assert d.tabs.currentWidget()==d.category_tabs[category]
  assert all(d.category_tabs[category].tabText(i) for i in range(d.category_tabs[category].count()))
 for caption,name in d.search_locations.items():
  if name.startswith('@'):continue
  d.jump_to_control(caption)
  assert d.tabs.currentWidget()==d.category_tabs[d.section_pages[__import__('freecad.rotorforge.gui',fromlist=['tab_name']).tab_name(name)][0]]
 assert d.values()==Parameters()
 assert len(register_commands())==7
 assert 'freecad.rotorforge.section_editor' not in sys.modules
 d.tabs.setCurrentIndex(0);d.category_tabs['Frame'].setCurrentIndex(0)
 QtWidgets.QApplication.processEvents();d.grab().save(str(out / 'editor.png'))
 from freecad.rotorforge.gui import QtCore
 assert len(d.tabs.buttons)==7
 assert d.tabs.buttons[0].y()<d.tabs.buttons[6].y()
 point=QtCore.QPointF(180,100)
 d.preview.zoom_at(point,2)
 assert d.preview.zoom==2 and d.preview.pan==QtCore.QPointF(-180,-100)
 d.preview.reset_view();assert d.preview.zoom==1 and d.preview.pan.isNull()
 d.resize(950,650)
 d.tabs.setCurrentWidget(d.category_tabs['TPU'])
 QtWidgets.QApplication.processEvents()
 tpu=d.category_tabs['TPU']
 assert len(tpu._rows)==2, len(tpu._rows)
 assert all(b.isVisible() for b in tpu.buttons)
 QtWidgets.QApplication.processEvents()
 d.grab().save(str(out / 'tpu.png'))
 d.jump_to_control('Finishing > Airflow / outlines > Cutout type, outline notch, patterns')
 QtWidgets.QApplication.processEvents()
 assert not d.preview_panel.isVisible()
 QtWidgets.QApplication.processEvents()
 d.grab().save(str(out / 'airflow.png'))
 f=d.category_tabs['Finishing']
 Path(str(out / 'metrics.json')).write_text(json.dumps({'dialog':[d.width(),d.height()], 'header':[f.header.width(),f.header.height(),f.header.isVisible()], 'rows':[[x.width(),x.height(),x.isVisible()] for x in f._rows], 'buttons':[[b.text(),b.isVisible(),b.mapTo(d,QtCore.QPoint()).x(),b.mapTo(d,QtCore.QPoint()).y()] for b in f.buttons]}))
 scroll=d.section_pages['Airflow / outlines'][1]
 print('AIRFLOW',d.size(),scroll.verticalScrollBar().maximum(),scroll.horizontalScrollBar().maximum(),flush=True)
 assert scroll.horizontalScrollBar().maximum()==0
 assert scroll.verticalScrollBar().maximum()==0
 d.airflow.add_pattern();assert len(d.airflow.patterns)==1
 d.airflow.inputs['width'].setValue(5);d.airflow.apply_pattern();assert d.airflow.patterns[0]['width']==5
 d.airflow.inputs['width'].setValue(6);d.airflow.discard_changes();assert d.airflow.inputs['width'].value()==5
 d.airflow.remove_pattern();assert not d.airflow.patterns
 d.tabs.setCurrentIndex(0);QtWidgets.QApplication.processEvents();assert d.preview_panel.isVisible()
 d.preview.zoom_at(point,2);d.preview.grab();assert d.preview.last_error is None
 d.preview.view_mode='AllParts';d.preview.grab();assert d.preview.last_error is None
 d.preview.reset_view()
 assert d.windowFlags() & QtCore.Qt.WindowMaximizeButtonHint
 assert d.find_control.mapTo(d,QtCore.QPoint()).y()>=d.generate.mapTo(d,QtCore.QPoint()).y()-10
 report={'status':'passed','checks':['Seven vertical main icons','Wrapping subsections visible at 950x650','Control search navigation across all fields','Cursor-anchored zoom and reset','Full-width airflow without outer scroll at 950x650','Default parameters unchanged','Original commands retained'],'FreeCAD':App.Version()}
except Exception:report={'status':'failed','error':traceback.format_exc()}
Path(str(out / 'checks.json')).write_text(json.dumps(report,indent=2))
os._exit(0 if report['status']=='passed' else 1)
