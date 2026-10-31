"""Portable shoe settings and front profiles; no CAD or Qt imports."""
BUMPER_SHAPES=('Follow bottom plate','Rounded shoe','Flat shoe','Chamfered shoe','Pointed shoe','Twin-lobe shoe','Swept-shoulder shoe','Flat-tip shoe','Centre-crown shoe','Shield shoe','Recessed-centre shoe','Stepped shoe','Capsule shoe','Bullnose shoe','Arrowhead shoe','V-recess shoe','Twin-shoulder shoe','Clipped-corner shoe')
FIELDS={
 'FlexFrontBumper':(False,'Create front bumper','One printable TPU shoe around the front of the actual bottom plate. Includes an underside sole, edge wall and upper retaining lip; no carbon geometry is changed.'),
 'FlexBumperShape':('Rounded shoe','Bumper front shape','Eighteen styles: follow the plate or choose rounded, swept, flat, crowned, shield, twin-shoulder or recessed protective toes.',BUMPER_SHAPES),
 'FlexBumperWidth':(0.,'Bumper toe width (0 = automatic)','Overall width of the added protective toe. Zero uses the plate grip width. The grip keeps its plate fit and blends continuously into wider or narrower toes. Ignored by Follow bottom plate.'),
 'FlexBumperReach':(20.,'Shoe reach behind nose','Length of bottom plate captured behind its actual foremost edge. The rear remains open for sliding the shoe onto the plate.'),
 'FlexBumperProjection':(4.,'Extra toe projection','Additional protective material ahead of the wall. Ignored by Follow bottom plate.'),
 'FlexBumperTipWidth':(0.,'Toe feature width (0 = automatic)','Central flat or recess width as a percentage of toe width. Zero retains the style proportions. Applies to chamfered, swept, flat-tip, crown, recessed, stepped and the six additional profiles.'),
 'FlexBumperRecess':(0.,'Toe recess depth (0 = automatic)','Depth of central recesses as a percentage of extra projection. Zero uses the style default; 1 to 90 percent customizes Twin-lobe, Recessed-centre, V-recess and Twin-shoulder shoes without cutting the plate grip.'),
 'FlexBumperLipReach':(0.,'Lip capture length (0 = full reach)','Length of upper retaining lip measured backward from the carbon nose. Zero uses the full shoe reach. A shorter lip makes fitting easier while the sole and outside wall keep their original reach.'),
 'FlexBumperWall':(2.,'Bumper wall thickness','Protective material outside the plate, in addition to fit clearance.'),
 'FlexBumperSole':(2.,'Shoe sole thickness','TPU below the underside fit gap; printed as the shoe base.'),
 'FlexBumperLip':(1.2,'Retaining lip thickness','Vertical thickness of the upper retaining lip.'),
 'FlexBumperOverlap':(2.,'Retaining lip overlap','Inward reach of the upper lip over the plate edge. Camera tabs are relieved automatically.'),
 'FlexBumperFit':(.2,'Plate fit clearance','Clearance around the carbon edge and above/below its faces. Start with a test fit for your TPU and plate thickness.')}

def toe_commands(shape,half,front,wall,projection,tip_width=0,recess=0):
 if shape=='Follow bottom plate':return ()
 f=front+wall;tip=f+projection;k=.5522847498307936
 t=lambda default:(tip_width/100 if tip_width else default)
 d=lambda default:(1-recess/100 if recess else default)
 commands=[('M',(-half,front-wall)),('L',(-half,f))]
 if shape=='Rounded shoe':commands.extend((('C',(-half,f+k*projection),(-k*half,tip),(0,tip)),('C',(k*half,tip),(half,f+k*projection),(half,f))))
 elif shape=='Flat shoe':commands.extend((('L',(-half,tip)),('L',(half,tip)),('L',(half,f))))
 elif shape=='Chamfered shoe':commands.extend((('L',(-t(.65)*half,tip)),('L',(t(.65)*half,tip)),('L',(half,f))))
 elif shape=='Pointed shoe':commands.extend((('L',(0,tip)),('L',(half,f))))
 elif shape=='Twin-lobe shoe':
  commands.extend((('C',(-half,tip),(-.5*half,tip),(-.5*half,tip)),('C',(-.2*half,tip),(-.2*half,f+d(.55)*projection),(0,f+d(.55)*projection)),('C',(.2*half,f+d(.55)*projection),(.2*half,tip),(.5*half,tip)),('C',(.5*half,tip),(half,tip),(half,f))))
 elif shape=='Swept-shoulder shoe':
  commands.extend((('C',(-half,f+.7*projection),(-.6*half,tip),(-t(.35)*half,tip)),('L',(t(.35)*half,tip)),('C',(.6*half,tip),(half,f+.7*projection),(half,f))))
 elif shape=='Flat-tip shoe':commands.extend((('L',(-t(.3)*half,tip)),('L',(t(.3)*half,tip)),('L',(half,f))))
 elif shape=='Centre-crown shoe':
  a=t(.15)*half;b=(half+a)/2;level=f+.35*projection
  commands.extend((('L',(-half,level)),('L',(-b,level)),('C',(-(b+a)/2,level),(-(b+a)/2,tip),(-a,tip)),('L',(a,tip)),('C',((b+a)/2,tip),((b+a)/2,level),(b,level)),('L',(half,level)),('L',(half,f))))
 elif shape=='Shield shoe':
  commands.extend((('L',(-half,f+.3*projection)),('L',(-.75*half,f+.85*projection)),('L',(0,tip)),('L',(.75*half,f+.85*projection)),('L',(half,f+.3*projection)),('L',(half,f))))
 elif shape=='Recessed-centre shoe':
  commands.extend((('L',(-half,tip)),('C',(-t(.4)*half,tip),(-t(.4)*half,f+d(.35)*projection),(0,f+d(.35)*projection)),('C',(t(.4)*half,f+d(.35)*projection),(t(.4)*half,tip),(half,tip)),('L',(half,f))))
 elif shape=='Stepped shoe':
  for x,y in ((-half,f+.35*projection),(-.65*half,f+.35*projection),(-.65*half,f+.7*projection),(-t(.25)*half,f+.7*projection),(-t(.25)*half,tip),(t(.25)*half,tip),(t(.25)*half,f+.7*projection),(.65*half,f+.7*projection),(.65*half,f+.35*projection),(half,f+.35*projection),(half,f)):commands.append(('L',(x,y)))
 elif shape=='Capsule shoe':
  a=t(.55)*half
  commands.extend((('C',(-half,tip),(-a,tip),(-a,tip)),('L',(a,tip)),('C',(a,tip),(half,tip),(half,f))))
 elif shape=='Bullnose shoe':
  a=t(.75)*half
  commands.extend((('C',(-half,f+.8*projection),(-a,tip),(0,tip)),('C',(a,tip),(half,f+.8*projection),(half,f))))
 elif shape=='Arrowhead shoe':
  a=t(.12)*half
  commands.extend((('L',(-.7*half,f+.4*projection)),('L',(-a,tip)),('L',(a,tip)),('L',(.7*half,f+.4*projection)),('L',(half,f))))
 elif shape=='V-recess shoe':
  a=t(.5)*half
  commands.extend((('L',(-half,tip)),('L',(-a,tip)),('L',(0,f+d(.4)*projection)),('L',(a,tip)),('L',(half,tip)),('L',(half,f))))
 elif shape=='Twin-shoulder shoe':
  a=t(.45)*half;valley=f+d(.45)*projection
  commands.extend((('C',(-half,tip),(-.8*half,tip),(-.65*half,tip)),('L',(-a,valley)),('L',(a,valley)),('L',(.65*half,tip)),('C',(.8*half,tip),(half,tip),(half,f))))
 elif shape=='Clipped-corner shoe':
  a=t(.5)*half
  commands.extend((('L',(-half,f+.35*projection)),('L',(-.8*half,f+.8*projection)),('L',(-a,tip)),('L',(a,tip)),('L',(.8*half,f+.8*projection)),('L',(half,f+.35*projection)),('L',(half,f))))
 commands.extend((('L',(half,front-wall)),('L',(-half,front-wall))))
 return tuple(commands)


def shoulder_hull(points,half,front,back=None):
 """Convex outer transition to the toe shoulder, preserving toe-only recesses.

 The cavity/lip are cut afterwards from the unmodified plate, so widening
 this external envelope never scales or loosens the actual plate fit.
 """
 if back is None:back=front
 points=sorted(set((float(x),float(y)) for x,y in points)|{(-half,front),(half,front),(-half,back),(half,back)})
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 lower=[];upper=[]
 for chain,seq in ((lower,points),(upper,reversed(points))):
  for pt in seq:
   while len(chain)>=2 and cross(chain[-2],chain[-1],pt)<=1e-10:chain.pop()
   chain.append(pt)
 return tuple(lower[:-1]+upper[:-1])
