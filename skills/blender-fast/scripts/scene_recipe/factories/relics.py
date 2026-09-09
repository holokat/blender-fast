"""Six original relic and furnishing assemblies for the dungeon."""
import math
from .geometry import R, TAU


def cage(g):
    g.group('15 Suspended cage',(-12.5,.0,0))
    for z in [.8,3.0]:
        g.cylinder('Cage circular plate',(0,0,z),1.2,.12,'iron',48)
        g.ring('Cage frame hoop',(0,0,z),1.2,.08,'bronze')
    for i in range(28):
        a=i*TAU/28
        x,y=1.12*math.cos(a),1.12*math.sin(a)
        g.beam('Cage iron bar',(x,y,.85),(x,y,3.0),.032,'iron')
        g.beam('Cage roof rib',(x,y,3.0),(0,0,3.6),.035,'iron')
        for z in [1.0,2.8]:
            g.sphere('Cage bar collar',(x,y,z),(.067,.067,.055),'bronze')
    g.chain((0,0,3.65),(0,0,5.1),22)
    g.box('Cage beam',(-.8,0,5.2),(3.8,.26,.26),'wood')
    g.box('Cage post',(-2.45,0,2.5),(.25,.35,5),'wood')
    g.ring('Cage padlock',(.0,-1.16,1.75),.105,.03,'iron',(math.pi/2,0,0),24)
    g.box('Cage padlock body',(0,-1.20,1.59),(.22,.10,.22),'bronze')


def sarcophagus(g):
    g.group('16 Carved sarcophagus',(8.0,-3.1,0))
    for x in [-.9,.9]:
        for y in [-1.35,1.35]:
            g.box('Tomb foot',(x,y,.24),(.45,.55,.48),'stone5')
    g.box('Sarcophagus body',(0,0,.9),(2.3,3.6,1.2),'stone3')
    for z in [.42,1.42]:
        g.box('Tomb molding',(0,0,z),(2.45,3.72,.18),'stone6')
    g.box('Tomb lid',(0,0,1.65),(2.55,3.8,.35),'stone5')
    g.box('Effigy torso',(0,.05,1.96),(.65,1.5,.28),'stone6')
    g.sphere('Effigy head',(0,.99,2.02),(.24,.30,.23),'stone7')
    for x in [-.20,.20]:
        g.box('Effigy leg',(x,-1.0,1.94),(.28,.7,.23),'stone6')
        g.beam('Folded effigy arm',(x*2,.6,2.0),(x,-.1,2.13),.10,'stone7')
    for side in [-1,1]:
        for row in range(3):
            for col in range(21):
                g.box('Tomb carved mark',(side*1.158,(col-10)*.15,.63+row*.24),(.02,.045,.12),'bronze',(.0,.0,side*.1))
    for y in [-1.65,1.65]:
        g.ring('Tomb carrying ring',(0,y*1.13,.97),.18,.05,'bronze',(math.pi/2,0,0),32)


def treasure(g):
    g.group('17 Open treasury chest',(11.5,-8.3,0))
    for x in [-1.1,1.1]:
        for y in [-.58,.58]:
            g.box('Chest corner',(x,y,.57),(.13,.13,1.12),'iron')
    for row in range(5):
        for side in [-1,1]:
            g.box('Chest plank',(0,side*.6,.16+row*.20),(2.3,.12,.18),'woodlight')
            g.box('Chest end plank',(side*1.1,0,.16+row*.20),(.12,1.15,.18),'wood')
    g.box('Chest floor',(0,0,.11),(2.2,1.15,.13),'wood')
    g.box('Open chest lid',(0,.95,1.5),(2.4,1.25,.16),'wood',(1.1,0,0))
    for x in [-.85,.85]:
        g.box('Chest front strap',(x,-.68,.6),(.12,.05,1.06),'iron')
        for z in [.2,.4,.6,.8,1.0]:
            g.sphere('Chest rivet',(x,-.72,z),(.032,.022,.032),'gold')
    for i in range(170):
        x,y=R.uniform(-.97,.97),R.uniform(-.44,.44)
        g.cylinder('Treasure coin',(x,y,.8+R.uniform(-.03,.15)),.08,.026,'gold',16)
    for i in range(14):
        g.sphere('Treasury gemstone',(R.uniform(-.8,.8),R.uniform(-.4,.4),1.0),(.07,.1,.065),'gem')
    for i in range(50):
        g.cylinder('Spilled coin',(R.uniform(-1.1,1.4),R.uniform(-1.65,-.8),.16),.065,.024,'gold',16)


def map_table(g):
    g.group('18 Cartographers desk',(-5.8,-2.3,0))
    for x in [-1.1,1.1]:
        for y in [-.6,.6]:
            g.box('Desk turned leg',(x,y,.73),(.16,.16,1.45),'wood')
            for z in [.3,.6,1.1]:
                g.ring('Desk leg turning',(x,y,z),.11,.028,'woodlight',n=24)
    g.box('Desk top',(0,0,1.53),(2.8,1.8,.18),'woodlight')
    g.box('Unrolled map',(0,0,1.628),(1.8,1.2,.014),'paper')
    for i in range(38):
        x,y=R.uniform(-.8,.8),R.uniform(-.52,.52)
        g.box('Map ink mark',(x,y,1.637),(R.uniform(.03,.22),.012,.005),'wood',rotation=(0,0,R.uniform(-2,2)))
    for x in [-.92,.92]:
        obj=g.cylinder('Map scroll roller',(x,0,1.69),.065,1.28,'paper',24)
        obj.rotation_euler=(math.pi/2,0,0)
    g.ring('Survey compass',(.82,-.5,1.66),.14,.019,'bronze',n=32)
    g.candle((-1.13,.48,1.64),.55)
    g.bottle((1.1,.48,1.64),.09,.2,'iron')
    for i in range(5):
        g.box('Stacked journal',(-.9,-.45,1.68+i*.06),(.39,.45,.05),'cloth')


def ossuary(g):
    g.group('19 Ossuary and memorial',(-14.4,10.0,0))
    for x in [-1.0,1.0]:
        g.box('Ossuary pier',(x,0,1.5),(.28,.9,3.0),'stone3')
    for row in range(5):
        z=.15+row*.6
        g.box('Ossuary shelf',(0,0,z),(2.2,.9,.13),'stone5')
        for i in range(7):
            x=(i-3)*.25
            g.sphere('Ossuary skull',(x,-.15,z+.26),(.105,.14,.12),'bone')
            g.box('Skull jaw',(x,-.22,z+.18),(.10,.12,.06),'bone')
            for dx in [-.041,.041]:
                g.sphere('Eye socket',(x+dx,-.275,z+.27),(.024,.014,.03),'dark')
            for j in range(4):
                g.box('Skull tooth',(x+(j-1.5)*.02,-.286,z+.18),(.015,.016,.032),'bone')
    for x in [-1.25,1.25]:
        g.candle((x,0,.2),.65)


def chandelier(g):
    g.group('20 Suspended chandelier',(-1.0,3.0,6.25))
    for r,z in [(1.5,0),(.75,.7)]:
        g.ring('Chandelier frame',(0,0,z),r,.065,'iron',n=64)
        for i in range(16):
            a=i*TAU/16
            x,y=r*math.cos(a),r*math.sin(a)
            g.candle((x,y,z),.30+.10*(i%3))
            g.beam('Chandelier radial arm',(x,y,z),(0,0,z+.3),.026,'bronze')
    for i in range(4):
        a=i*TAU/4
        g.chain((1.5*math.cos(a),1.5*math.sin(a),0),(0,0,2.0),29)
    g.light('Chandelier glow',(0,0,-.15),430,(1,.57,.22),1.1)
