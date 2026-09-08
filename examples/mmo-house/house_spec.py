"""Deterministic stylized fantasy house specification, dimensions in metres."""
import math
import random

PALETTE = {
 'plaster':('#eed4a5',.82,0), 'plaster_light':('#f9dfb5',.8,0),
 'wood':('#503428',.8,0), 'wood_light':('#965b37',.72,0), 'wood_gold':('#bc8150',.72,0),
 'door':('#36777b',.64,0), 'door_light':('#509397',.63,0),
 'stone':('#8f9b95',.9,0), 'stone_light':('#b8b8a1',.92,0), 'stone_dark':('#687a77',.92,0),
 'roof0':('#354f68',.71,0), 'roof1':('#416078',.74,0), 'roof2':('#4e7189',.72,0), 'roof3':('#658394',.77,0),
 'iron':('#293e3e',.48,.5), 'brass':('#e4ad5a',.4,.55),
 'glass':('#ffba56',.32,0,2.0), 'grass':('#6f8755',1,0), 'moss':('#7a9968',1,0),
 'earth':('#585d46',1,0), 'ground':('#c9c3b8',1,0),
 'leaf':('#557c60',1,0), 'leaf_light':('#829764',1,0), 'leaf_dark':('#3e6855',1,0),
 'flower':('#f7c35d',.8,0), 'flower_pink':('#d97975',.8,0), 'pot':('#ad6852',.92,0),
 'mushroom':('#c3684f',.86,0), 'cream':('#eddbb0',.9,0),
}


def create_spec():
    rng=random.Random(7421)
    items=[]
    def add(kind,mat,pos,scale=(1,1,1),rot=(0,0,0),**extra):
        items.append(dict(kind=kind,mat=mat,pos=pos,scale=scale,rot=rot,**extra))
    def box(mat,pos,scale,rot=(0,0,0)):add('box',mat,pos,scale,rot)
    def beam(a,b,width=.14,mat='wood',depth=None):
        add('beam',mat,(0,0,0),a=a,b=b,width=width,depth=depth or width)
    def sphere(mat,pos,scale):add('ico',mat,pos,scale)
    def cyl(mat,pos,scale,rot=(0,0,0)):add('cylinder',mat,pos,scale,rot)
    def torus(mat,pos,scale,rot=(0,0,0)):add('torus',mat,pos,scale,rot)
    # The round, layered terrain plinth.
    cyl('earth',(0,0,-.22),(6.6,6.1,.48))
    cyl('grass',(0,0,.04),(6.55,6.05,.16))
    # Foundation and warm plaster volumes.
    box('stone_dark',(0,0,.46),(6,4.35,.7))
    for z in (.35,.65):
        for x in range(9):
            box(rng.choice(['stone','stone_light','stone_dark']),(-2.7+x*.67,-2.205,z),(.62,.23,.27))
        for y in range(6):
            box(rng.choice(['stone','stone_light']),(3.02,-1.83+y*.7,z),(.23,.64,.27))
    box('plaster',(0,0,2.31),(5.9,4.3,3.0))
    # End gables are prisms, generated directly from their silhouette.
    for y in (-2.13,2.13):
        add('gable','plaster_light',(0,y,3.81),(5.9,.18,2.65))
    for z in (.85,2.35,3.86):
        for y in (-2.24,2.24):box('wood',(0,y,z),(6.2,.18,.19))
        for x in (-3.0,3.0):box('wood',(x,0,z),(.18,4.4,.19))
    for x in (-2.94,-1.95,0,1.95,2.94):
        for y in (-2.25,2.25):box('wood',(x,y,2.36),(.18,.2,3.12))
    for x in (-3.02,3.02):
        for y in (-2.05,0,2.05):box('wood',(x,y,2.35),(.18,.18,3.12))
    # Diagonal braces make the frame legible at a distance.
    for x in (-2.4,2.4):
        beam((x-.37,-2.36,2.48),(x+.37,-2.36,3.63),.12)
    beam((-2.8,-2.36,3.94),(0,-2.36,6.42),.17)
    beam((0,-2.36,6.42),(2.8,-2.36,3.94),.17)
    beam((0,-2.37,3.94),(0,-2.37,6.4),.17)
    beam((-1.7,-2.37,4.07),(-1.7,-2.37,4.95),.12)
    beam((1.7,-2.37,4.07),(1.7,-2.37,4.95),.12)
    # Flared slate roof, separately modelled overlapping tiles.
    for side in (-1,1):
        for row in range(13):
            t=(row+.45)/13
            x=side*3.56*t
            z=6.52-2.93*t+.38*t*t
            slope=(-2.93+.76*t)/3.56
            angle=-math.atan(slope)*side
            for col in range(13):
                y=-2.56+col*.421+(row%2)*.052
                add('box',f'roof{rng.choices(range(4),[3,4,2,1])[0]}',(x,y,z+rng.uniform(-.018,.018)),(.405,.447,.10),(0,angle,rng.uniform(-.009,.009)))
        for y in (-2.79,2.8):
            for row in range(4):
                t1=row/4;t2=(row+1)/4
                beam((side*3.6*t1,y,6.56-2.93*t1+.38*t1*t1),(side*3.6*t2,y,6.56-2.93*t2+.38*t2*t2),.18,'wood_gold')
        beam((side*3.6,-2.8,4.0),(side*3.6,2.8,4.0),.2,'wood')
    beam((0,-2.95,6.64),(0,2.97,6.64),.23,'wood_gold')
    for y in (-2.85,2.83):
        cyl('wood_gold',(0,y,6.86),(.10,.10,.52))
        sphere('brass',(0,y,7.14),(.15,.15,.20))
    # Side extension with a sloping tiled roof.
    box('stone_dark',(3.83,.5,.42),(1.94,3.5,.6))
    box('plaster',(3.84,.5,1.85),(1.9,3.43,2.55))
    for y in (-1.23,2.22):
        box('wood',(3.85,y,.85),(2.03,.18,.18))
        box('wood',(3.85,y,2.97),(2.03,.18,.18))
        box('wood',(4.81,y,1.91),(.18,.18,2.35))
    for row in range(7):
        t=(row+.4)/7
        for col in range(9):
            add('box',f'roof{rng.randrange(4)}',(2.88+2.2*t,-1.49+col*.47,3.73-.81*t),(.43,.49,.09),(0,.35,0))
    for y in (-1.63,2.6):beam((2.85,y,3.83),(5.12,y,2.98),.17,'wood_gold')
    beam((5.12,-1.63,2.98),(5.12,2.6,2.98),.18,'wood')
    # Arched doorway with cut planks and radial stone surround.
    add('arch','wood',(.72,-2.365,.78),(1.66,.13,2.35))
    radius=.7; spring=2.25
    for i in range(9):
        x=-radius+(i+.5)*(2*radius/9)
        top=spring+math.sqrt(max(0,radius*radius-x*x))
        box('door_light' if i%3==1 else 'door',(.72+x,-2.45,(.83+top)/2),(.143,.105,top-.83))
    for z in (1.15,1.85):box('iron',(.73,-2.53,z),(1.32,.075,.055))
    for side in (-1,1):
        for j in range(5):box('stone_light',(.72+side*.88,-2.43,1.0+j*.26),(.25,.23,.245))
    for i in range(11):
        ang=i*math.pi/10
        box('stone_light',(.72+.87*math.cos(ang),-2.43,2.25+.87*math.sin(ang)),(.27,.24,.25),(0,ang-math.pi/2,0))
    torus('brass',(1.08,-2.60,1.57),(.095,.095,.095),(math.pi/2,0,0))
    sphere('brass',(1.08,-2.62,1.69),(.05,.04,.05))
    # Windows, paired shutters, planter boxes.
    def front_window(cx,y,z,w=1.2,h=1.1):
        box('wood',(cx,y,z),(w+.25,.19,h+.24))
        box('glass',(cx,y-.11,z),(w,.035,h))
        for dx in (-w/2,0,w/2):box('wood_gold',(cx+dx,y-.17,z),(.065,.1,h+.10))
        for dz in (-h/2,0,h/2):box('wood_gold',(cx,y-.18,z+dz),(w+.13,.1,.065))
        for side in (-1,1):
            sx=cx+side*(w/2+.27)
            for j in range(3):box('door',(sx+side*(j-1)*.1,y-.05,z),(.095,.15,h+.10))
            for dz in (-h*.35,h*.35):box('wood_light',(sx,y-.16,z+dz),(.34,.08,.07))
        box('wood_light',(cx,y-.25,z-h/2-.16),(w+.24,.40,.19))
        for i in range(7):
            xx=cx-w*.46+i*w*.153
            sphere('leaf',(xx,y-.31,z-h/2+.03),(.18,.17,.16))
            sphere('flower_pink' if i%2 else 'flower',(xx,y-.34,z-h/2+.15),(.07,.07,.07))
    front_window(-1.36,-2.36,1.79,1.05,.96)
    front_window(3.86,-1.37,1.92,1.00,1.00)
    # Round gable window.
    cyl('wood_gold',(0,-2.40,5.15),(.54,.54,.15),(math.pi/2,0,0))
    cyl('glass',(0,-2.50,5.15),(.43,.43,.025),(math.pi/2,0,0))
    torus('wood',(0,-2.53,5.15),(.47,.47,.47),(math.pi/2,0,0))
    for rot in (0,math.pi/2):box('wood_gold',(0,-2.55,5.15),(.065,.10,.84),(0,rot,0))
    # Side window on extension.
    box('wood',(4.85,.6,1.92),(.17,1.30,1.25))
    box('glass',(4.95,.6,1.92),(.03,1.09,1.02))
    for yy in (.055,.6,1.145):box('wood_gold',(4.99,yy,1.92),(.08,.065,1.13))
    for zz in (1.4,1.92,2.44):box('wood_gold',(4.99,.6,zz),(.08,1.18,.065))
    box('wood_light',(5.06,.6,1.3),(.38,1.43,.19))
    # Porch platform, steps, timber posts and pitched canopy.
    box('stone_dark',(.72,-3.16,.35),(2.5,1.72,.40))
    for j in range(11):box('wood_light',(-.43+j*.23,-3.17,.59),(.21,1.65,.13))
    for j in range(3):box('stone',(.72,-4.17-j*.30,.37-j*.09),(1.75,.34,.16))
    for x in (-.48,1.93):
        box('wood',(x,-3.82,1.8),(.18,.18,2.5))
        box('stone_light',(x,-3.82,.72),(.32,.32,.26))
        beam((x,-3.82,2.30),(x+(.38 if x<0 else -.38),-3.82,2.82),.13,'wood_gold')
    beam((-.65,-3.83,2.94),(2.12,-3.83,2.94),.17,'wood_gold')
    for side in (-1,1):
        for r in range(5):
            t=(r+.45)/5
            for c in range(5):add('box',f'roof{(r+c)%4}',(.72+side*1.46*t,-2.6-c*.37,3.55-.66*t),(.38,.41,.085),(0,side*.424,0))
        beam((.72,-4.27,3.64),(.72+side*1.55,-4.27,2.95),.14,'wood_gold')
    # Chimney masonry with staggered stone joints.
    box('stone_dark',(1.45,1.15,6.38),(.72,.74,2.15))
    for level in range(7):
        z=5.49+level*.29
        for j in range(2):
            box(rng.choice(['stone','stone_light']),(1.25+j*.4, .76,z),(.37,.15,.26))
            box(rng.choice(['stone','stone_light']),(1.87,.96+j*.4,z),(.15,.37,.26))
    box('stone_light',(1.46,1.15,7.40),(1.00,1.02,.23))
    box('iron',(1.46,1.15,7.54),(.55,.59,.08))
    # Warm lanterns, with iron cages and bracket arms.
    def lantern(x,y,z):
        beam((x,y+.2,z+.42),(x,y-.17,z+.42),.055,'iron')
        torus('iron',(x,y-.17,z+.24),(.08,.08,.08),(math.pi/2,0,0))
        box('glass',(x,y-.18,z),(.22,.23,.32))
        for dx in (-.14,.14):
            for dy in (-.14,.14):box('iron',(x+dx,y-.18+dy,z),(.035,.035,.40))
        box('iron',(x,y-.18,z-.22),(.36,.36,.08))
        add('cone','iron',(x,y-.18,z+.25),(.25,.25,.22))
    lantern(2.17,-2.5,2.23)
    lantern(-2.7,-2.45,2.3)
    # Barrels made from individual staves and dark iron hoops.
    def barrel(x,y,s=1):
        for j in range(12):
            a=j*math.tau/12
            box('wood_light' if j%3 else 'wood_gold',(x+.34*s*math.cos(a),y+.34*s*math.sin(a),.62*s),(.19*s,.11*s,.84*s),(0,0,a+math.pi/2))
        cyl('wood',(x,y,1.06*s),(.35*s,.35*s,.09*s))
        for z in (.36,.85):torus('iron',(x,y,z*s),(.36*s,.36*s,.36*s))
    barrel(-3.38,-2.95)
    barrel(-4.20,-2.71,.8)
    # Crates and pumpkins.
    for x,y,z,s in [(2.93,-3.01,.53,.68),(3.49,-2.75,.47,.55)]:
        box('wood',(x,y,z),(s,s,s))
        for zz in (-s*.31,0,s*.31):box('wood_light',(x,y-s*.515,z+zz),(s*.97,.055,s*.25))
        beam((x-s*.43,y-s*.57,z-s*.43),(x+s*.43,y-s*.57,z+s*.43),.075,'wood_gold')
    for i in range(3):
        x=3.0+i*.38;y=-3.82+(i%2)*.15
        sphere('pot',(x,y,.32),(.24,.23,.22))
        beam((x,y,.49),(x-.02,y,.61),.05,'wood')
    # Cobbles and border stones lead toward the lit doorway.
    for row in range(8):
        yy=-4.38-row*.23
        center=.70+.30*math.sin(row*.6)
        for c in range(5):
            box(rng.choice(['stone','stone_light','stone_dark']),(center+(c-2)*.35+rng.uniform(-.025,.025),yy,.19),(.31,.20,.11),(0,0,rng.uniform(-.12,.12)))
    for a in [i*math.tau/36 for i in range(36)]:
        if math.sin(a)<-.65:continue
        sphere(rng.choice(['stone','stone_dark']),(6.15*math.cos(a),5.66*math.sin(a),.18),(rng.uniform(.17,.30),.23,.19))
    # Herb beds and a small faceted tree.
    for x,y in [(-2.7,-3.55),(-4.8,-1.6),(5.05,2.8),(5.45,-.8),(-3.8,2.85),(-4.8,1.6)]:
        for j in range(4):
            sphere(rng.choice(['leaf','leaf_light','leaf_dark']),(x+rng.uniform(-.3,.3),y+rng.uniform(-.3,.3),.35+rng.uniform(0,.14)),(.43,.37,.36))
        for j in range(5):
            xx=x+rng.uniform(-.35,.35);yy=y+rng.uniform(-.35,.35)
            beam((xx,yy,.22),(xx,yy,.78),.025,'leaf_dark')
            sphere('flower' if j%2 else 'flower_pink',(xx,yy,.79),(.065,.065,.07))
    tx,ty=-4.5,1.0
    beam((tx,ty,.14),(tx+.16,ty+.1,2.45),.25,'wood_light')
    for dx,dy,dz in [(-.7,.15,2.45),(.7,.3,2.7),(.0,-.5,2.9)]:
        beam((tx+.1,ty,1.6),(tx+dx,ty+dy,dz),.12,'wood_light')
    for dx,dy,dz,sz in [(-.7,.1,2.75,.8),(.7,.3,3.0,.87),(0,-.5,3.2,.9),(0,.1,3.7,.78),(-.5,-.3,3.45,.65),(.6,-.4,3.55,.60)]:
        sphere(rng.choice(['leaf','leaf_light']),(tx+dx,ty+dy,dz),(sz,sz*.83,sz*.8))
    # Fence gives the back edge a readable scale.
    for x in [-5.4,-4.4,-3.4,3.8,4.8,5.7]:
        box('wood_light',(x,3.55,.67),(.13,.13,1.05))
        add('cone','wood_gold',(x,3.55,1.23),(.12,.12,.17))
    for a,b in [(-5.4,-3.4),(3.8,5.7)]:
        for z in (.48,.89):beam((a,3.55,z),(b,3.55,z),.095,'wood_gold')
    # Hanging leaf-shaped shop sign, no invented real-world brand.
    beam((-2.03,-2.46,3.3),(-2.03,-3.05,3.3),.075,'iron')
    for x in (-2.22,-1.86):beam((x,-3.04,3.3),(x,-3.04,3.03),.025,'iron')
    box('wood',(-2.04,-3.04,2.80),(.74,.13,.49),(0,.04,0))
    sphere('brass',(-2.05,-3.13,2.80),(.10,.025,.18))
    beam((-2.16,-3.16,2.63),(-1.95,-3.16,2.98),.025,'brass')
    return {'seed':7421,'palette':PALETTE,'items':items}

if __name__=='__main__':
    import json
    from pathlib import Path
    out=Path(__file__).resolve().with_name('house-spec.json')
    spec=create_spec();out.write_text(json.dumps(spec,separators=(',',':'))+'\n')
    print(f'{len(spec["items"])} mesh objects specified; {out.stat().st_size} bytes')
