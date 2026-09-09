"""Large architectural assemblies with distinct construction and silhouettes."""
import math
from .geometry import R, TAU


def chamber(g):
    g.group('01 Cutaway vaulted chamber')
    g.box('Foundation', (0,0,-.5), (33,25,1), 'dark')
    for row in range(36):
        for col in range(48):
            x,y = (col-23.5)*.675,(row-17.5)*.675
            g.box('Worn flagstone',(x,y,-.01+R.uniform(-.025,.025)),(.65,.65,.20),rotation=(0,0,R.uniform(-.014,.014)))
    # A central opening leaves the portal silhouette visible through the back wall.
    g.brick_wall(-9.5,11.8,13,5.7)
    g.brick_wall(9.5,11.8,13,5.7)
    g.brick_wall(-16,0,24,4.2,along='y')
    g.brick_wall(16,0,24,1.14,along='y')
    for x in [-15,-8,8,15]:
        for z in [.25,.5,4.8,5.0]:
            g.box('Buttress capital',(x,11.2,z),(1.1,1.2,.24))
        for z in range(12):
            g.box('Buttress shaft',(x,11.25,.72+z*.34),(.7,.8,.31))
    for x in [-12,-6,6,12]:
        g.arch((x,11.38,.7),2.0,2.1,depth=.6)
    for x in [-14,-7,7,14]:
        for y in [-10.9,10.9]:
            g.cylinder('Wall sconce base',(x,y,2.45),.18,.24,'bronze')
            g.cone('Sconce flame',(x,y,2.85),.15,.6,'flame')
            g.light('Sconce light',(x,y-.25,2.9),95,(1,.4,.10),.25)


def portal(g):
    g.group('02 Rune gateway', (0,9,0))
    for level in range(4):
        g.box('Gateway approach step',(0,-.4-level*.4,.12+level*.14),(6.2-level*.35,3.5-level*.45,.24))
    g.arch((0,0,.65),2.25,2.5,1.3)
    for side in [-1,1]:
        g.box('Carved plinth',(side*2.45,0,.45),(1.2,1.7,.9))
        g.cone('Gateway pinnacle',(side*2.35,0,5.4),.42,1.2,'stone6',8)
        for row in range(17):
            for mark in [-1,1]:
                g.box('Engraved luminous stroke',(side*2.24+mark*.07,-.68,1.0+row*.20),(.027,.015,.12),'rune',(0,mark*.5,0))
    g.cylinder('Portal darkness',(0,.32,3.0),2.03,.08,'dark',64).rotation_euler=(math.pi/2,0,0)
    for radius in [1.75,1.92,2.05]:
        g.ring('Portal energy ring',(0,.22,3),radius,.026,'rune',(math.pi/2,0,0),96)
    for i in range(120):
        a=i*TAU/120
        r=1.7 if i%3 else 1.88
        g.box('Gateway runic marker',(r*math.cos(a),.19,3+r*math.sin(a)),(.025,.018,.12),'rune',(0,math.pi/2-a,0))
    for i in range(15):
        a=i*.49
        r=.2+i*.07
        g.sphere('Floating portal mote',(r*math.cos(a),.0,3+r*math.sin(a)),(.035,.035,.035),'rune')
    g.light('Portal glow',(0,-.75,3.1),540,(.12,.75,1),1.5)


def staircase(g):
    g.group('03 Spiral stair tower',(-12.1,6.5,0))
    for z,r,h in [(.16,2.55,.32),(.42,2.3,.22),(2.85,.43,5.5)]:
        g.cylinder('Stair tower masonry',(0,0,z),r,h,'stone3',48)
    for i in range(32):
        a=-math.pi/2+i*.21
        z=.6+i*.155
        g.box('Spiral tread',(1.18*math.cos(a),1.18*math.sin(a),z),(2.0,.48,.15),'stone5',(0,0,a))
        p=(2.12*math.cos(a),2.12*math.sin(a),z)
        g.beam('Stair baluster',p,(p[0],p[1],z+1.0),.028,'iron')
        b=a+.21
        g.beam('Rising handrail',(p[0],p[1],z+1),(2.12*math.cos(b),2.12*math.sin(b),z+1.155),.04,'bronze')
        for rr in [.5,.9,1.3,1.7]:
            g.cylinder('Tread fixing',(rr*math.cos(a),rr*math.sin(a),z+.09),.033,.035,'iron',8)
    for z in [1,2,3,4,5]:
        g.ring('Column collar',(0,0,z),.45,.07,'bronze')
    g.sphere('Stair finial',(0,0,5.85),(.23,.23,.32),'gold')


def forge(g):
    g.group('04 Smithy and furnace',(12,7.6,0))
    for row in range(13):
        for col in range(6):
            if row<5 and col in [2,3]:
                continue
            g.box('Furnace brick',((col-2.5)*.55,0,.22+row*.34),(.52,1.35,.31))
    g.arch((0,-.74,0),.77,1.0,.38)
    g.box('Firebox',(0,-.35,.6),(1.25,1.0,1.1),'dark')
    for i in range(35):
        g.sphere('Burning coal',(R.uniform(-.6,.6),R.uniform(-.9,.1),R.uniform(.18,.45)),(.12,.13,.09),'flame')
    g.light('Forge light',(0,-1,.9),340,(1,.19,.02),.5)
    for x in [-.9,.9]:
        for z in [.9,1.8,2.7,3.6]:
            g.box('Chimney iron strap',(x,-.72,z),(.14,.09,.40),'iron')
    g.box('Anvil block',(-.2,-2.2,.5),(1.1,.9,1),'wood')
    g.box('Anvil foot',(-.2,-2.2,1.1),(1.3,.8,.22),'iron')
    g.box('Anvil waist',(-.2,-2.2,1.42),(.6,.55,.5),'iron')
    g.box('Anvil face',(-.2,-2.2,1.76),(1.65,.65,.25),'silver')
    horn=g.cone('Anvil horn',(.85,-2.2,1.7),.28,1.2,'iron')
    horn.rotation_euler=(0,math.pi/2,0)
    for i in range(10):
        x=-1.6+i*.14
        g.beam('Blacksmith tool handle',(x,-1.35,.25),(x,-1.1,1.45),.035,'wood')
        g.box('Tool head',(x,-1.1,1.48),(.20,.1,.1),'iron')
    for i in range(16):
        g.box('Bellows pleat',(2.1,-.3,.65+i*.032),(.85-i*.012,1.45,.024),'cloth')


def throne(g):
    g.group('05 Carved throne dais',(6,5.7,0))
    for i in range(4):
        g.box('Throne step',(0,-.15-i*.28,.12+i*.15),(4-i*.28,3.0-i*.30,.25))
    g.box('Throne seat',(0,0,1.6),(1.8,1.5,.3),'stone3')
    g.box('Throne cushion',(0,-.12,1.80),(1.5,1.25,.15),'cloth')
    for x in [-.78,.78]:
        for y in [-.58,.58]:
            g.box('Throne leg',(x,y,1.14),(.28,.28,.85),'stone4')
        g.box('Throne arm',(x,-.15,2.3),(.32,1.3,.28),'stone5')
        g.sphere('Throne arm carved beast',(x,-.76,2.42),(.22,.28,.25),'stone6')
    g.box('Throne tall back',(0,.65,2.94),(1.9,.32,2.7),'stone4')
    for i in range(7):
        g.cone('Throne crown spike',((i-3)*.29,.65,4.25+.35*(1-abs(i-3)/3)),.16,.8,'bronze')
    for x in [-.62,0,.62]:
        g.box('Backrest carved flute',(x,.455,2.95),(.11,.05,2.1),'bronze')
    for i in range(30):
        a=i*TAU/30
        g.sphere('Throne inlay',(math.cos(a)*.44,.43,3.35+math.sin(a)*.44),(.04,.027,.04),'gem')
    g.box('Royal banner',(0,.44,2.63),(.5,.03,1.9),'cloth')


def ritual(g):
    g.group('06 Ritual circle and altar',(0,-1.7,0))
    for z,r,h in [(.12,3.5,.24),(.34,3.15,.22),(.52,2.85,.17)]:
        g.cylinder('Ritual dais',(0,0,z),r,h,'stone2',96)
    for r in [1.8,2.15,2.75]:
        g.ring('Runic floor ring',(0,0,.615),r,.021,'rune',n=96)
    for i in range(72):
        a=i*TAU/72
        g.box('Runic floor symbol',(2.46*math.cos(a),2.46*math.sin(a),.615),(.04,.18,.02),'rune',(0,0,a+.4))
    for i in range(5):
        a=i*TAU/5; b=(i+2)*TAU/5
        g.beam('Engraved pentagram',(1.79*math.cos(a),1.79*math.sin(a),.63),(1.79*math.cos(b),1.79*math.sin(b),.63),.018,'bronze')
    g.box('Altar pedestal',(0,.25,1.08),(1.3,.95,.9),'stone5')
    g.box('Altar slab',(0,.25,1.61),(2.2,1.25,.22),'stone6')
    for x in [-.9,.9]:
        for y in [-.2,.7]:
            g.candle((x,y,1.74),.45)
    g.sphere('Suspended ritual crystal',(0,.25,2.5),(.23,.23,.58),'gem')
    for i in range(12):
        a=i*TAU/12
        g.candle((3*math.cos(a),3*math.sin(a),.47),.35+.12*(i%3))
    g.light('Ritual glow',(0,0,2.8),150,(.09,.7,1),.9)


def waterwell(g):
    g.group('07 Underground well',(3.6,-7.9,0))
    for row in range(4):
        for i in range(28):
            a=(i+.5*(row%2))*TAU/28
            g.box('Well coping stone',(1.2*math.cos(a),1.2*math.sin(a),.16+row*.3),(.36,.48,.27),rotation=(0,0,a+math.pi/2))
    g.cylinder('Well water',(0,0,.68),.98,.025,'water',64)
    for x in [-1.55,1.55]:
        g.box('Well upright',(x,0,1.65),(.2,.25,3.3),'wood')
    g.beam('Well axle',(-1.75,0,2.9),(1.75,0,2.9),.12,'wood')
    for i in range(18):
        g.ring('Wound well rope',((i-8.5)*.047,0,2.9),.14,.023,'woodlight',(0,math.pi/2,0),24)
    g.beam('Hanging rope',(0,-.15,.9),(0,-.15,2.86),.025,'woodlight')
    for i in range(14):
        a=i*TAU/14
        g.box('Bucket stave',(.27*math.cos(a),-.15+.27*math.sin(a),.88),(.09,.05,.42),'wood',(0,0,a+math.pi/2))
    for z in [.72,1.03]:
        g.ring('Bucket hoop',(0,-.15,z),.29,.025,'iron',n=24)


def collapsed_passage(g):
    g.group('08 Collapsed side passage',(12.9,-3.1,0))
    g.arch((0,1,0),1.8,2.1,.85)
    for i in range(95):
        g.box('Fallen masonry',(R.uniform(-2.1,2.1),R.uniform(-1.35,1.3),R.uniform(.1,.6)),
              (R.uniform(.18,.75),R.uniform(.18,.55),R.uniform(.18,.45)),rotation=tuple(R.uniform(-.7,.7) for _ in range(3)))
    for side in [-1,1]:
        g.box('Broken timber shore',(side*1.4,.3,1.7),(.22,.24,3.8),'wood',(0,side*.15,0))
    for i in range(17):
        g.beam('Broken grate bar',(-1.4+i*.17,.9,.2),(-1.4+i*.17,.9,1.5+R.random()),.035,'iron')
