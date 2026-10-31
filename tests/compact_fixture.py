from dataclasses import replace
from freecad.rotorforge.parameters import Parameters as Base
def Parameters(**kw):
 p=Base(FPVEnabled=True,StandoffCount='6 (3 pairs)',StandoffPair3Y=-94.,StandoffPair3Width=28.,MidReachMode='Custom',MidRearReach=102.,TopReachMode='Custom',TopRearReach=102.)
 return replace(p,**kw)
Parameters.from_dict=Base.from_dict
