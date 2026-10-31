"""Deterministic, thickness-separated cutting sheets, in millimetres."""
import math

PROFILE_GAP=12.0
ARM_GAP=4.0
ARM_ROLES=('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight')
SHEET_MARGIN=10.0
ROW_WIDTH=420.0
SHEET_GAP=30.0


def stock_token(thickness):
    return format(thickness,'.6f').rstrip('0').rstrip('.').replace('.','p')+'mm'


def arrange_profiles(items):
    """Pack pre-oriented arms in one alternating row, then shelf other parts.

    Each input has role, width, height and thickness. Sheet coordinates start
    at the lower left stock origin; combined_y separates the stock sheets.
    No stock dimensions or tool compensation are inferred.
    """
    groups={}
    for item in items:
        if any(not math.isfinite(item[k]) or item[k]<=0 for k in ('width','height','thickness')):
            raise ValueError('Cutting profile dimensions and thickness must be positive and finite.')
        groups.setdefault(round(item['thickness'],6),[]).append(item)
    sheets=[];combined_y=0.
    for thickness,parts in sorted(groups.items()):
        x=y=SHEET_MARGIN;row_height=0.;right=top=SHEET_MARGIN;placed=[]
        arms=sorted((i for i in parts if i['role'] in ARM_ROLES),key=lambda i:ARM_ROLES.index(i['role']))
        for item in arms:
            placed.append(dict(item,x=x,y=y))
            right=max(right,x+item['width']);top=max(top,y+item['height'])
            x+=item['width']+ARM_GAP;row_height=max(row_height,item['height'])
        if arms:
            x=SHEET_MARGIN;y+=row_height+PROFILE_GAP;row_height=0.
        for item in (i for i in parts if i['role'] not in ARM_ROLES):
            width,height=item['width'],item['height']
            if x>SHEET_MARGIN and x+width>ROW_WIDTH-SHEET_MARGIN:
                x=SHEET_MARGIN;y+=row_height+PROFILE_GAP;row_height=0.
            placed.append(dict(item,x=x,y=y))
            right=max(right,x+width);top=max(top,y+height)
            x+=width+PROFILE_GAP;row_height=max(row_height,height)
        sheets.append(dict(thickness=thickness,token=stock_token(thickness),width=right+SHEET_MARGIN,
                           height=top+SHEET_MARGIN,combined_y=combined_y,parts=placed))
        combined_y+=top+SHEET_MARGIN+SHEET_GAP
    return dict(units='mm',gap=PROFILE_GAP,arm_gap=ARM_GAP,margin=SHEET_MARGIN,row_width=ROW_WIDTH,
                rotation='Arms aligned vertically with alternating motor ends; other flattened axes retained',sheets=sheets)


def document_layout(settings, layout, faces, export_folder, origin_x):
    """Replace this frame's native cutting snapshot in one undoable transaction."""
    import FreeCAD as App
    from .document import component_objects
    doc=settings.Document
    matches=[o for o in doc.Objects if 'RotorForgeCuttingLayout' in o.PropertiesList
             and o.RotorForgeCuttingLayout and o.SourceFrame==settings]
    if len(matches)>1:raise ValueError('More than one cutting layout belongs to this frame; remove the duplicate layouts before exporting.')
    existing=matches[0] if matches else None
    for sheet in layout['sheets']:
        for item in sheet['parts']:
            if not faces[item['role']].isValid():raise ValueError('Invalid cutting profile: '+item['role'])
    undo_mode=doc.UndoMode
    if not undo_mode:doc.UndoMode=1
    doc.openTransaction('Refresh RotorForge cutting profiles')
    try:
        if existing:
            root=existing
        else:
            root=doc.addObject('App::Part','RotorForgeCuttingProfiles')
            root.addProperty('App::PropertyBool','RotorForgeCuttingLayout','Cutting layout');root.RotorForgeCuttingLayout=True
            root.addProperty('App::PropertyLinkGlobal','SourceFrame','Cutting layout');root.SourceFrame=settings
            root.addProperty('App::PropertyPath','ExportFolder','Cutting layout')
            root.addProperty('App::PropertyString','Snapshot','Cutting layout')
            root.addProperty('App::PropertyLength','PartGap','Cutting layout')
            root.Placement.Base=App.Vector(origin_x,0,0)
        root.Label='Cutting profiles (DXF / SVG)'
        root.ExportFolder=str(export_folder.resolve());root.Snapshot='Export snapshot - re-export after editing the frame'
        root.PartGap=layout['gap']
        if 'ArmGap' not in root.PropertiesList:root.addProperty('App::PropertyLength','ArmGap','Cutting layout')
        root.ArmGap=layout['arm_gap']
        oldgroups={round(g.StockThickness.Value,6):g for g in root.Group}
        oldparts={o.SourceRole:o for g in root.Group for o in g.Group}
        sources=component_objects(settings);usedparts=set();usedgroups=set()
        for sheet in layout['sheets']:
            group=oldgroups.get(sheet['thickness'])
            if group is None:
                group=doc.addObject('App::Part','CutStock_'+sheet['token']);root.addObject(group)
                group.addProperty('App::PropertyLinkGlobal','SourceFrame','Cutting sheet');group.SourceFrame=settings
                for prop in ('StockThickness','SheetWidth','SheetHeight'):group.addProperty('App::PropertyLength',prop,'Cutting sheet')
                group.addProperty('App::PropertyPath','DXFFile','Cutting sheet');group.addProperty('App::PropertyPath','SVGFile','Cutting sheet')
            group.Label=f"Stock {sheet['thickness']:g} mm";usedgroups.add(group.Name)
            group.Placement.Base=App.Vector(0,sheet['combined_y'],0)
            for prop,val in [('StockThickness',sheet['thickness']),('SheetWidth',sheet['width']),('SheetHeight',sheet['height'])]:setattr(group,prop,val)
            group.DXFFile=str((export_folder/('Stock_'+sheet['token']+'.dxf')).resolve())
            group.SVGFile=str((export_folder/('Stock_'+sheet['token']+'.svg')).resolve())
            ordered=[]
            for item in sheet['parts']:
                role=item['role'];obj=oldparts.get(role)
                if obj is None:
                    obj=doc.addObject('Part::Feature','Cut_'+role)
                    obj.addProperty('App::PropertyString','SourceRole','Cutting profile');obj.SourceRole=role
                    obj.addProperty('App::PropertyLinkGlobal','SourcePart','Cutting profile')
                    obj.addProperty('App::PropertyLength','StockThickness','Cutting profile')
                else:
                    for oldgroup in list(root.Group):
                        if oldgroup!=group and obj in oldgroup.Group:oldgroup.removeObject(obj)
                group.addObject(obj);ordered.append(obj);usedparts.add(obj.Name)
                obj.Label=role+f" - {sheet['thickness']:g} mm"
                obj.Placement=App.Placement();obj.Shape=faces[role].copy()
                obj.Placement.Base=obj.Placement.Base+App.Vector(item['x'],item['y'],0)
                obj.SourcePart=sources.get(role);obj.StockThickness=sheet['thickness']
                if App.GuiUp:
                    obj.ViewObject.ShapeColor=(.72,.84,.87);obj.ViewObject.LineColor=(.08,.26,.3)
                    obj.ViewObject.DisplayMode='Flat Lines'
            group.Group=ordered
        for obj in oldparts.values():
            if obj.Name not in usedparts:doc.removeObject(obj.Name)
        for group in oldgroups.values():
            if group.Name not in usedgroups:doc.removeObject(group.Name)
        root.Group=[next(g for g in root.Group if abs(g.StockThickness.Value-sheet['thickness'])<1e-7) for sheet in layout['sheets']]
        doc.recompute();doc.commitTransaction();return root
    except Exception:
        doc.abortTransaction();raise
    finally:
        if not undo_mode:doc.UndoMode=undo_mode
