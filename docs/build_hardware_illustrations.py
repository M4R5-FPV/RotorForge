"""Hardware and nut-seat figures using the guide's material palette."""
from guide_style import *
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,arm_layouts
from freecad.rotorforge.airflow_gui import finished_part_path
from freecad.rotorforge.nut_seats import seats
p=Parameters()
base=[(finished_part_path(p,'Arm'+a['name']),LIGHT) for a in arm_layouts(p)]+[(finished_part_path(p,'MidPlate'),LIGHT)]
for s in seats(replace(p,ArmNutMount='M3 press nut')):base.append((ellipse(*s['point'],2.85),'#090a0b'))
gallery('HardwareReferences.png',[cell('Round button heads at arm mounting positions',*base)],1,rowheight=650,cellwidth=1600)
plate=rect(-12,0,24,3);hexcut=rect(-2.825,2.2,5.65,.8);bore=rect(-1.6,-1,3.2,7)
hexplate=plate.subtracted(hexcut.united(bore));nut=rect(-2.75,2.2,5.5,2.4).subtracted(bore)
pressplate=plate.subtracted(rect(-2.11,-1,4.22,6));press=rect(-2.78,3,5.56,1.5).united(rect(-2.34,1.47,4.68,1.53)).subtracted(rect(-1.5,0,3,6))
gallery('NutSeats.png',[cell('Hex nut: partial 0.8 mm pocket',(hexplate,BLUE),(nut,'#090a0b')),cell('M3 press nut: 4.22 mm through bore',(pressplate,BLUE),(press,'#090a0b'))],2,rowheight=430)
