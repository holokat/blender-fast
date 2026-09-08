"""Original decorative jet concept. Dimensions describe artwork, not aircraft engineering."""
import json
import math
from pathlib import Path

PALETTE = {
    'body': ['#637d89', .34, .65], 'wing': ['#78939d', .31, .6],
    'dark': ['#192b35', .4, .65], 'rubber': ['#0f1921', .7, .1],
    'metal': ['#adc3c8', .24, .85], 'gold': ['#d69951', .3, .7],
    'canopy': ['#132d3e', .13, .75], 'light': ['#b8efff', .25, .3, 2],
    'red': ['#ee5a48', .4, .3, 1], 'floor': ['#d7dcdd', .75, 0],
}


def make_spec():
    meshes = {}; items = []
    def mesh(name, vertices, faces):
        meshes[name] = {'vertices': vertices, 'faces': faces}
        return name
    def item(name, shape, mat, pos=(0,0,0), scale=(1,1,1), rot=(0,0,0)):
        items.append(dict(name=name, mesh=shape, mat=mat, pos=pos, scale=scale, rot=rot))
    def prism(name, points, thick=.09):
        n=len(points)
        return mesh(name, [(x,y,z+t) for t in (-thick/2,thick/2) for x,y,z in points],
                    [list(range(n-1,-1,-1)),list(range(n,2*n))]+[[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)])
    def loft(name, rings, count=32):
        vertices=[(rx*math.cos(a*math.tau/count),y,z+rz*math.sin(a*math.tau/count)) for y,rx,rz,z in rings for a in range(count)]
        faces=[[i*count+j,i*count+(j+1)%count,(i+1)*count+(j+1)%count,(i+1)*count+j] for i in range(len(rings)-1) for j in range(count)]
        faces.extend([list(range(count-1,-1,-1)),list(range((len(rings)-1)*count,len(rings)*count))])
        return mesh(name,vertices,faces)
    def annulus(name, radius, width, depth, count=40):
        vertices=[(r*math.cos(j*math.tau/count),y,r*math.sin(j*math.tau/count)) for y,r in [(-depth/2,radius),(-depth/2,radius-width),(depth/2,radius),(depth/2,radius-width)] for j in range(count)]
        faces=[]
        for j in range(count):
            k=(j+1)%count
            for a,b in [(0,1),(2,0),(1,3),(3,2)]:faces.append([a*count+j,a*count+k,b*count+k,b*count+j])
        return mesh(name,vertices,faces)
    box=prism('box',[(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],1)
    rivet=loft('fastener',[(-.03,.034,.034,0),(.03,.034,.034,0)],8)
    body=loft('fuselage',[(-6.7,.025,.025,0),(-5.7,.38,.27,0),(-4.1,.72,.45,.02),(-2.4,.88,.53,.03),(-.2,1.12,.55,.02),(2.3,1.12,.47,0),(4.4,.85,.34,-.05)])
    item('Fuselage',body,'body')
    nose=loft('nose',[(-6.73,.025,.025,0),(-5.7,.385,.273,0),(-5.45,.44,.315,0)])
    item('Radar nose',nose,'dark')
    canopy=loft('canopy',[(-4.55,.015,.03,.30),(-3.8,.45,.53,.42),(-2.65,.53,.69,.46),(-1.65,.46,.50,.49),(-1.12,.025,.03,.53)])
    item('Canopy frame',canopy,'gold',pos=(0,0,.27),scale=(1.08,1,.35))
    item('Smoked canopy',canopy,'canopy',pos=(0,-.03,.06))
    for side in (-1,1):
        wing=prism(f'wing-{side}',[(side*.65,-2.0,.05),(side*5.7,1.95,-.06),(side*5.9,3.05,-.08),(side*1.1,2.3,.03)],.15)
        item('Swept wing',wing,'wing')
        flap=prism(f'flap-{side}',[(side*1.6,1.4,.13),(side*4.8,2.7,.01),(side*3.6,2.54,.01),(side*1.6,1.95,.13)],.025)
        item('Trailing control surface',flap,'body')
        stripe=prism(f'stripe-{side}',[(side*3.7,.68,.045),(side*4.0,.92,.04),(side*4.05,2.54,.035),(side*3.75,2.43,.04)],.015)
        item('Wing accent',stripe,'gold')
        tail=prism(f'tailplane-{side}',[(side*.6,2.6,.14),(side*2.9,4.55,.08),(side*2.75,5.25,.06),(side*.7,4.53,.05)],.11)
        item('Horizontal tail',tail,'wing')
        fin=prism(f'fin-{side}',[(side*.85,2.0,.22),(side*1.65,3.1,2.55),(side*1.73,4.25,2.4),(side*.97,4.55,.14)],.09)
        item('Canted vertical tail',fin,'body')
        tip=prism(f'fin-tip-{side}',[(side*1.59,3.025,2.37),(side*1.65,3.1,2.56),(side*1.73,4.25,2.41),(side*1.665,4.276,2.22)],.096)
        item('Tail accent',tip,'gold')
        engine=loft(f'engine-{side}',[(-.9,.51,.44,-.25),(1.5,.60,.52,-.23),(3.6,.55,.46,-.22),(4.68,.47,.42,-.2)])
        item('Engine housing',engine,'body',pos=(side*.68,0,0))
        inlet=loft(f'inlet-{side}',[(-2.32,.49,.34,-.20),(-1.2,.51,.38,-.21)])
        item('Intake surround',inlet,'metal',pos=(side*.89,0,0))
        item('Intake shadow',box,'rubber',pos=(side*.89,-2.33,-.20),scale=(.78,.03,.43))
        ring=annulus('exhaust-ring',.48,.09,.55)
        item('Exhaust shroud',ring,'dark',pos=(side*.68,4.75,-.20))
        item('Exhaust inner ring',ring,'metal',pos=(side*.68,4.83,-.20),scale=(.86,.8,.86))
        inner=loft('exhaust-core',[(0,.34,.34,0),(.02,.34,.34,0)],32)
        item('Exhaust darkness',inner,'rubber',pos=(side*.68,4.63,-.20))
        for j in range(20):
            a=j*math.tau/20
            item('Nozzle petal',box,'metal' if j%2 else 'dark',pos=(side*.68+.445*math.cos(a),4.83,-.20+.445*math.sin(a)),scale=(.065,.50,.07),rot=(0,-a,0))
        for j in range(22):
            t=j/21
            x=side*(1.2+4.13*t);y=-1.35+3.24*t
            item('Leading edge fastener',rivet,'metal',pos=(x,y,.15-.14*t),rot=(math.pi/2,0,0))
        for row in range(2):
            for j in range(20):
                y=-1.3+j*.25
                item('Engine fastener',rivet,'metal',pos=(side*(.77+row*.16),y,.53),rot=(math.pi/2,0,0),scale=(.72,.72,.72))
        for j in range(9):
            item('Engine vent',box,'dark',pos=(side*.97,.3+j*.14,.555),scale=(.22,.055,.012),rot=(0,0,side*.1))
        item('Wingtip navigation light',box,'red' if side<0 else 'light',pos=(side*5.77,2.43,-.03),scale=(.08,.38,.06))
        item('Intake splitter',box,'dark',pos=(side*.65,-1.78,-.10),scale=(.055,.92,.65))
    for j in range(14):
        item('Dorsal panel seam',box,'dark',pos=(0,-.9+j*.36,.579),scale=(.72,.019,.012))
    # No weapon systems or engineering internals are modeled.
    return {'title':'Jet fighter study','palette':PALETTE,'meshes':meshes,'items':items,
            'scope':'Original decorative aircraft concept, not a replica or functional aircraft design.'}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(make_spec(),separators=(',',':'))+'\n')
    print(len(make_spec()['items']))
