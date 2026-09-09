"""Six independently modeled workshop, storage, and machinery assemblies."""
import math
from .geometry import R, TAU


def alchemy(g):
    g.group('09 Alchemy laboratory',(-6,3,0))
    for x in [-1.35,1.35]:
        for y in [-.55,.55]:
            g.box('Workbench leg',(x,y,.68),(.16,.16,1.35),'wood')
    for i in range(9):
        g.box('Workbench plank',((i-4)*.35,0,1.4),(.33,1.5,.16),'woodlight')
    for x in [-1.4,1.4]:
        g.box('Laboratory rack post',(x,.56,2.4),(.11,.12,1.8),'iron')
    for z in [2.0,2.8]:
        g.box('Bottle shelf',(0,.55,z),(3.1,.5,.09),'wood')
        for i in range(16):
            g.bottle(((i-7.5)*.18,.5,z+.045),.06+.015*(i%3),.26+.07*(i%4))
    for i in range(8):
        g.bottle(((i-3.5)*.29,-.35,1.49),.09,.38+.11*(i%3))
    for x in [-.65,.65]:
        g.sphere('Distillation flask',(x,-.05,1.96),(.24,.24,.30),'glass')
        g.cylinder('Flask neck',(x,-.05,2.3),.065,.25,'glass',16)
        g.ring('Flask cradle',(x,-.05,1.67),.23,.024,'iron',n=24)
    for i in range(40):
        a=i*.47
        g.beam('Copper condenser coil',(-.45+i*.023,.0+.14*math.cos(a),2.35+.14*math.sin(a)),
               (-.45+(i+1)*.023,.14*math.cos(a+.47),2.35+.14*math.sin(a+.47)),.025,'bronze')
    g.candle((-1.22,-.3,1.49),.50)


def library(g):
    g.group('10 Chained library',(-5.8,9,0))
    for x in [-2,2]:
        g.box('Library upright',(x,0,2.25),(.18,.72,4.5),'wood')
    g.box('Library back',(0,.3,2.25),(4,.12,4.5),'wood')
    for level in range(6):
        z=.25+level*.72
        g.box('Library shelf',(0,-.05,z),(4.2,.8,.12),'woodlight')
        for i in range(30):
            height=R.uniform(.32,.58)
            x=(i-14.5)*.126
            material=['cloth','wood','iron','woodlight'][i%4]
            g.box('Bound volume',(x,-.07,z+.07+height/2),(.105,.45,height),material,(0,R.uniform(-.07,.07),0))
            for dz in [-.13,.13]:
                g.box('Book spine band',(x,-.305,z+.09+height/2+dz),(.09,.012,.025),'gold')
            if i%7==0:
                g.chain((x,-.36,z+.4),(x+.1,-.4,z+.05),7)
    for x in [-2.1,2.1]:
        g.cone('Bookcase finial',(x,0,4.75),.18,.5,'bronze')


def armory(g):
    g.group('11 Weapons and shield rack',(-12.5,-7.6,0))
    for x in [-1.6,1.6]:
        g.box('Weapon rack upright',(x,0,1.45),(.15,.2,2.9),'wood')
        g.box('Weapon rack foot',(x,0,.13),(.45,1.15,.2),'wood')
    for z in [.65,2.4]:
        g.box('Weapon crossbar',(0,0,z),(3.5,.17,.16),'wood')
    for i in range(9):
        x=(i-4)*.35
        g.beam('Spear shaft',(x,-.18,.12),(x,-.18,2.68),.033,'woodlight')
        g.cone('Spear blade',(x,-.18,3.02),.11,.65,'silver',4)
        for j in range(9):
            g.ring('Spear leather wrap',(x,-.18,.75+j*.027),.043,.012,'cloth',n=12)
    for x in [-1.1,0,1.1]:
        shield=g.cylinder('Round shield',(x,-.4,1.35),.45,.085,'wood',48)
        shield.rotation_euler=(math.pi/2,0,0)
        g.ring('Shield rim',(x,-.465,1.35),.45,.037,'iron',(math.pi/2,0,0))
        g.sphere('Shield boss',(x,-.51,1.35),(.14,.09,.14),'bronze')
        for i in range(16):
            a=i*TAU/16
            g.sphere('Shield rivet',(x+.395*math.cos(a),-.49,1.35+.395*math.sin(a)),(.025,.017,.025),'iron')


def supplies(g):
    g.group('12 Provisions and cooperage',(-7.3,-7.9,0))
    for index,(x,y) in enumerate([(-1,0),(0,.5),(1,0),(-.65,-.85),(.6,-.85)]):
        for i in range(24):
            a=i*TAU/24
            for section in range(4):
                z=.17+section*.30
                radius=.47+.065*math.sin((section+.5)*math.pi/4)
                g.box('Barrel stave',(x+radius*math.cos(a),y+radius*math.sin(a),z),(.126,.065,.295),'woodlight',(0,0,a+math.pi/2))
        for z in [.15,.48,.91,1.18]:
            g.ring('Barrel iron hoop',(x,y,z),.535,.03,'iron')
        for i in range(8):
            u=(i-3.5)*.11
            length=2*math.sqrt(max(0,.46**2-u**2))
            g.box('Barrel lid plank',(x+u,y,1.25),(.103,length,.055),'wood')
    for row in range(2):
        for i in range(3):
            x,y,z=(i-1)*.65,1.45,.30+row*.58
            g.box('Provision crate',(x,y,z),(.6,.6,.54),'wood')
            for k in [-1,0,1]:
                g.box('Crate plank joint',(x+k*.17,y-.31,z),(.018,.016,.49),'dark')
            for dz in [-.18,.18]:
                g.box('Crate band',(x,y-.325,z+dz),(.58,.035,.055),'iron')


def hoist(g):
    g.group('13 Chain hoist and winch',(12.4,1.0,0))
    for x in [-1.25,1.25]:
        g.box('Hoist timber upright',(x,0,2.0),(.23,.3,4.0),'wood')
        g.beam('Hoist brace',(x,-.65,.1),(x,0,2.7),.085,'wood')
    g.box('Hoist crossbeam',(0,0,4.1),(3.25,.35,.3),'woodlight')
    for x in [-.4,.4]:
        g.ring('Winch drum flange',(x,0,1.2),.42,.07,'iron',(0,math.pi/2,0))
    g.beam('Winch drum axle',(-.7,0,1.2),(.7,0,1.2),.22,'wood')
    for i in range(19):
        g.ring('Drum rope winding',((i-9)*.035,0,1.2),.24,.022,'woodlight',(0,math.pi/2,0),24)
    g.ring('Hoist upper pulley',(0,0,3.77),.23,.045,'bronze',(math.pi/2,0,0),32)
    g.chain((0,-.25,1.65),(0,-.25,3.72),33)
    for x in [-.7,.7]:
        g.chain((0,-.25,1.8),(x,-.25,.6),20)
    for i in range(6):
        g.box('Hoist pallet',((i-2.5)*.25,-.25,.5),(.22,1.3,.12),'wood')
    for i in range(12):
        g.box('Iron ingot cargo',((i%3-1)*.28,(i//3-1.5)*.25-.25,.65),(.25,.22,.15),'iron')


def organ(g):
    g.group('14 Pipe organ',(6.0,10.2,0))
    g.box('Organ cabinet',(0,0,1.2),(3.7,1.2,2.4),'wood')
    for i in range(27):
        x=(i-13)*.126
        h=1.2+1.9*abs(i-13)/13
        g.cylinder('Organ pipe',(x,-.03,2.35+h/2),.049,h,'bronze',16)
        g.cylinder('Pipe mouth',(x,-.085,2.7),.019,.17,'dark',8)
        for z in [2.55,3.1]:
            g.ring('Pipe ferrule',(x,-.03,z),.055,.012,'gold',n=16)
    for row in range(2):
        for i in range(30):
            g.box('Organ ivory key',((i-14.5)*.095,-.79-row*.15,1.65-row*.14),(.089,.42,.05),'bone')
            if i%7 not in [2,6]:
                g.box('Organ ebony key',((i-14.5)*.095+.045,-.68-row*.15,1.69-row*.14),(.045,.24,.04),'dark')
    for side in [-1,1]:
        for i in range(9):
            g.sphere('Organ stop',(side*1.63,-.66,1.25+i*.10),(.05,.04,.05),'bone')
