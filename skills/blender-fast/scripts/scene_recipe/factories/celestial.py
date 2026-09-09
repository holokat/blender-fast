"""Three procedural scientific instruments for the celestial vault example."""
import math
from .geometry import TAU


def orrery(g):
    g.group('Armillary orrery')
    for z, r, h in [(.18, 1.7, .36), (.5, 1.4, .24), (1.1, .45, 1.1)]:
        g.cylinder('Orrery pedestal', (0, 0, z), r, h, 'stone4', 64)
    g.sphere('Orrery sun', (0, 0, 2.8), (.42, .42, .42), 'gold')
    for i, r in enumerate([.8, 1.2, 1.6, 2.0]):
        rotation = (.35 + i * .27, i * .36, i * .5)
        g.ring('Celestial meridian', (0, 0, 2.8), r, .045, 'bronze', rotation, 96)
        a = i * 1.9
        g.sphere('Orbiting planet', (r * math.cos(a), r * math.sin(a), 2.8),
                 (.13 + i * .025,) * 3, ['rune', 'silver', 'gem', 'gold'][i])
        g.beam('Planet support', (0, 0, 2.8), (r * math.cos(a), r * math.sin(a), 2.8), .021, 'iron')
    g.ring('Graduated equator', (0, 0, 2.8), 2.13, .075, 'gold', n=128)
    for i in range(96):
        a = i * TAU / 96
        g.box('Equator tick', (2.13 * math.cos(a), 2.13 * math.sin(a), 2.89),
              (.022, .14 if i % 4 else .25, .02), 'dark', (0, 0, a - math.pi / 2))
    g.light('Orrery glow', (0, 0, 2.8), 100, (.2, .55, 1), .5)


def reactor(g):
    g.group('Crystal containment engine')
    for z, r, h in [(.16, 1.55, .32), (.5, 1.3, .3), (3.9, 1.15, .18)]:
        g.cylinder('Reactor foundation', (0, 0, z), r, h, 'iron', 64)
    for i in range(6):
        a = i * TAU / 6
        x, y = math.cos(a), math.sin(a)
        g.beam('Containment column', (x, y, .65), (x, y, 3.9), .085, 'bronze')
        for z in [1.1, 2, 2.9, 3.6]:
            g.sphere('Column insulator', (x, y, z), (.15, .15, .12), 'bone')
    for z in [1, 1.8, 2.6, 3.4]:
        g.ring('Containment coil', (0, 0, z), 1.05, .06, 'gold', n=64)
    for i in range(7):
        a = i * TAU / 7
        x, y = .42 * math.cos(a), .42 * math.sin(a)
        g.cone('Crystal shard', (x, y, 2.4), .28, 2.2 + .1 * i, 'rune', 6)
        g.cone('Crystal lower point', (x, y, 1.45), .28, .65, 'gem', 6).rotation_euler = (math.pi, 0, 0)
    for i in range(12):
        a = i * TAU / 12
        g.box('Reactor dial', (1.4 * math.cos(a), 1.4 * math.sin(a), .72), (.12, .25, .08), 'silver', (0, 0, a))
    g.light('Reactor illumination', (0, 0, 2.5), 250, (.16, .8, 1), .6)


def telescope(g):
    g.group('Astral telescope')
    for i in range(3):
        a = i * TAU / 3
        g.beam('Telescope tripod', (1.1 * math.cos(a), 1.1 * math.sin(a), .15), (0, 0, 1.85), .085, 'wood')
        g.sphere('Tripod shoe', (1.1 * math.cos(a), 1.1 * math.sin(a), .15), (.16, .16, .11), 'bronze')
    g.ring('Elevation wheel', (0, 0, 2.0), .55, .07, 'bronze', (math.pi / 2, 0, 0), 64)
    a, b = (-1.2, 0, 1.85), (1.1, 0, 3.4)
    g.beam('Telescope tube', a, b, .32, 'bronze', 48)
    from mathutils import Vector
    direction = (Vector(b) - Vector(a)).normalized()
    orientation = direction.to_track_quat('Z', 'Y').to_euler()
    for i in range(9):
        p = Vector(a).lerp(Vector(b), i / 8)
        g.ring('Tube reinforcing band', p, .33, .035, 'gold', orientation, 48)
    lens = g.cylinder('Objective lens', Vector(b) + direction * .025, .30, .025, 'glass', 64)
    lens.rotation_euler = orientation
    g.beam('Eyepiece', Vector(a) - direction * .3, a, .11, 'iron', 24)
    for i in range(24):
        angle = i * TAU / 24
        g.sphere('Elevation wheel rivet', (.5 * math.cos(angle), -.075, 2 + .5 * math.sin(angle)), (.026,) * 3, 'gold')
