"""Create the installation guide for the namespaced workbench."""
from pathlib import Path
import os
from runpy import run_path
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether,Preformatted
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('ROTORFORGE_INSTALL_OUTPUT',str(ROOT/'build'/'RotorForge_Installation.pdf')))
VERSION=run_path(str(ROOT/'freecad'/'rotorforge'/'version.py'))['__version__']
for n,f in [('Body','DejaVuSans.ttf'),('Bold','DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(n,'/usr/share/fonts/truetype/dejavu/'+f))
pdfmetrics.registerFont(TTFont('Code','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold')
INK=colors.HexColor('#183542');TEAL=colors.HexColor('#08798a');PALE=colors.HexColor('#eef5f8')
styles={n:ParagraphStyle(n,fontName='Bold' if n in ('title','heading') else 'Body',fontSize=size,leading=lead,textColor=INK,spaceAfter=space) for n,size,lead,space in [('title',25,30,12),('heading',13,18,8),('body',9,13.2,8),('small',8,11,5)]}
story=[]
FOLDER_CODE='''import os
from PySide import QtCore, QtGui, QtWidgets
rf_mod = os.path.normpath(os.path.join(App.getUserAppDataDir(), "Mod"))
os.makedirs(rf_mod, exist_ok=True)
print(rf_mod)
QtWidgets.QApplication.clipboard().setText(rf_mod)
QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(rf_mod))'''
def para(t,style='body'):return Paragraph(t,styles[style])
def section(title):story.extend([Spacer(1,8),para(title,'heading')])
def steps(items):
 rows=[[Paragraph(f'{i:02}',ParagraphStyle('number',fontName='Bold',fontSize=12,textColor=TEAL)),para(t)] for i,t in enumerate(items,1)]
 table=Table(rows,colWidths=[29,450]);table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.append(table)
story.extend([para('ROTORFORGE / SETUP','small'),para('Installation &amp; updates','title'),para(f'Windows, macOS and Linux | Version {VERSION}'),para('Requires FreeCAD 1.x with Python 3.10 or later. No extra pip packages are needed for normal installation.')])
section('Open the correct Mod folder')
story.append(para('In your usual FreeCAD installation, open <b>View &gt; Panels &gt; Python console</b>. Paste this entire block and press Enter:'))
code_style=ParagraphStyle('code',fontName='Code',fontSize=8.1,leading=10.4,textColor=INK)
box=Table([[Preformatted(FOLDER_CODE,code_style)]],colWidths=[479]);box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#cfdee5')),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story.extend([box,Spacer(1,6),para('This creates Mod if needed, opens it and copies its exact path to the clipboard. In Windows Explorer, press <b>Ctrl+L</b>, then <b>Ctrl+V</b> and Enter to reopen it. The path follows your username, FreeCAD version and configured data location.')])
section('Windows')
story.append(para('For FreeCAD 1.1, copy the path below into the Windows Explorer <b>address bar</b> and press Enter. Use the method above if the folder is missing or your installation uses a different location.','small'))
path_style=ParagraphStyle('path',fontName='Code',fontSize=8.2,leading=11,textColor=INK)
paths=Table([[Preformatted(r'%APPDATA%\FreeCAD\v1-1\Mod',path_style)]],colWidths=[479]);paths.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(paths)
steps(['After opening Mod, extract the ZIP and close every FreeCAD window.','Move the old RotorForge folder out of Mod. Copy in the complete new inner RotorForge folder. <b>Replace; do not merge.</b> Keep your design files.','Confirm <b>Mod\\RotorForge\\freecad\\rotorforge\\init_gui.py</b>. Restart FreeCAD, select <b>RotorForge</b>, then <b>RotorForge &gt; New frame</b>.'])
section('macOS')
steps(['Extract the ZIP and quit FreeCAD completely with Command-Q.','In Finder, press Command-Shift-G and enter the printed Mod path. The usual location is <b>~/Library/Application Support/FreeCAD/Mod</b>.','Replace the old RotorForge folder with the complete new inner RotorForge folder. Confirm <b>Mod/RotorForge/freecad/rotorforge/init_gui.py</b>. Avoid extra folder nesting and do not install inside FreeCAD.app.','Restart FreeCAD, select <b>RotorForge</b> and choose <b>RotorForge &gt; New frame</b>.'])
story.append(PageBreak())
section('Linux')
steps(['Extract the ZIP and close FreeCAD.','Open the printed Mod directory. A common FreeCAD 1.x path is <b>~/.local/share/FreeCAD/Mod</b>. Sandboxed or portable packages may use another path.','Replace the old RotorForge folder with the complete new inner RotorForge folder. Confirm <b>Mod/RotorForge/freecad/rotorforge/init_gui.py</b>.','Restart FreeCAD, select <b>RotorForge</b>, then <b>RotorForge &gt; New frame</b>. No system-wide install or executable permission is needed for the Python files.'])
section('Updating existing designs')
story.append(para('Back up your FCStd files and saved JSON settings before updating. Keep personal designs outside the plugin folder. Close FreeCAD before replacing the installation. Remove duplicate RotorForge installations from Mod.'))
story.append(para('RotorForge uses <b>freecad.rotorforge</b> and deliberately has no top-level Init.py or InitGui.py. The small outer rotorforge folder is a compatibility bridge for older saved documents; keep it with the rest of the package. Do not add freecad/__init__.py or move the inner package out of its folder structure.'))
story.append(para('Open a saved FCStd file, double-click <b>Frame Parameters</b>, review its settings and choose <b>Update frame</b>. Existing saved proxy paths are supported, and new saves use the namespaced implementation. Geometry controls and the saved JSON schema are retained. Use Save As if you want to keep the earlier generated model.'))
section('If RotorForge does not appear')
steps(['Check the Mod path in the same FreeCAD installation you launch. Confirm <b>Mod/RotorForge/freecad/rotorforge/init_gui.py</b> with no extra RotorForge directory nesting.','Extract the archive first and replace the whole old folder. Leaving old Init.py or InitGui.py files behind can interfere with the new startup. Quit and restart FreeCAD completely.','Open <b>View &gt; Panels &gt; Report view</b> and inspect loading errors. Confirm you are using FreeCAD 1.x.','For a temporary session, run <b>Launch_RotorForge.FCMacro</b> from the extracted folder through <b>Macro &gt; Macros</b>. Keep the complete workbench installed for persistent parametric editing.'])
section('Help and uninstalling')
story.append(para('Choose <b>RotorForge &gt; Help</b> for the complete control guide. To uninstall, close FreeCAD and remove Mod/RotorForge. Your saved designs and manufacturing exports remain separate; keep the workbench installed while you need to regenerate parametric models.'))
def footer(c,d):
 w,h=A4;c.setStrokeColor(colors.HexColor('#cfdee5'));c.line(52,h-35,w-52,h-35);c.line(52,44,w-52,44);c.setFillColor(TEAL);c.setFont('Bold',8);c.drawString(52,h-25,'RotorForge');c.setFillColor(INK);c.setFont('Body',7);c.drawRightString(w-52,h-25,'Drone Frame Editor / Installation');c.drawString(52,29,f'Installation guide / {VERSION}');c.drawRightString(w-52,29,str(d.page))
OUT.parent.mkdir(parents=True,exist_ok=True)
SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=52,rightMargin=52,topMargin=52,bottomMargin=58,title='RotorForge Installation',author='RotorForge contributors').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
