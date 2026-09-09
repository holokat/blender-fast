"""Shared direct-data geometry and materials for the original dungeon scene."""
import bpy
import bmesh
import math
import random
from mathutils import Vector

R = random.Random(2092026)
TAU = math.tau


class Geometry:
    def __init__(self, scene, materials=None):
        self.scene = scene
        self.collection = scene.collection
        self.cache = {}
        self.materials = materials if materials is not None else {}
        self.groups = []
        self.offset = Vector((0, 0, 0))
        if materials is None:
            self._materials()

    def group(self, name, at=(0, 0, 0)):
        self.collection = bpy.data.collections.new(name)
        self.scene.collection.children.link(self.collection)
        self.groups.append(self.collection)
        self.offset = Vector(at)

    def material(self, name, rgb, metal=0, rough=.55, transmission=0, emission=0, bump=0):
        material = bpy.data.materials.new(name)
        material.diffuse_color = (*rgb, 1)
        material.use_nodes = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        shader = nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*rgb, 1)
        shader.inputs['Metallic'].default_value = metal
        shader.inputs['Roughness'].default_value = rough
        shader.inputs['Transmission Weight'].default_value = transmission
        if emission:
            shader.inputs['Emission Color'].default_value = (*rgb, 1)
            shader.inputs['Emission Strength'].default_value = emission
        if bump:
            noise = nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 7
            noise.inputs['Detail'].default_value = 3
            normal = nodes.new('ShaderNodeBump')
            normal.inputs['Strength'].default_value = .28
            normal.inputs['Distance'].default_value = bump
            links.new(noise.outputs['Fac'], normal.inputs['Height'])
            links.new(normal.outputs['Normal'], shader.inputs['Normal'])
        self.materials[name] = material

    def _materials(self):
        for i in range(8):
            v = .18 + i * .024
            self.material(f'stone{i}', (v * .87, v * .99, v), rough=.82, bump=.075)
        self.material('dark', (.035, .045, .05), rough=.85)
        self.material('wood', (.20, .075, .026), rough=.68, bump=.055)
        self.material('woodlight', (.34, .17, .057), rough=.65, bump=.035)
        self.material('iron', (.055, .068, .075), metal=.86, rough=.32)
        self.material('bronze', (.42, .21, .063), metal=.78, rough=.3)
        self.material('silver', (.46, .52, .56), metal=.87, rough=.22)
        self.material('gold', (.72, .40, .075), metal=.86, rough=.26)
        self.material('bone', (.67, .60, .40), rough=.55)
        self.material('cloth', (.23, .023, .038), rough=.94, bump=.025)
        self.material('paper', (.66, .49, .26), rough=.9)
        self.material('glass', (.19, .43, .40), rough=.09, transmission=.86)
        self.material('water', (.015, .10, .10), metal=.18, rough=.085, transmission=.65)
        self.material('flame', (1, .23, .015), rough=.3, emission=6)
        self.material('rune', (.055, .68, .73), rough=.3, emission=3)
        self.material('gem', (.15, .52, .63), metal=.35, rough=.12, transmission=.25)
        self.material('wax', (.67, .56, .28), rough=.5)

    def mesh(self, name, vertices, faces):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        return mesh

    def primitive(self, kind, n=16):
        key = (kind, n)
        if key in self.cache:
            return self.cache[key]
        if kind == 'box':
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1)
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=.04, segments=1, affect='EDGES')
            mesh = bpy.data.meshes.new('Beveled unit box')
            bm.to_mesh(mesh)
            bm.free()
        elif kind in ('cylinder', 'cone'):
            top = 1 if kind == 'cylinder' else .03
            vertices = [(r * math.cos(i * TAU/n), r * math.sin(i*TAU/n), z)
                        for r, z in [(1, -.5), (top, .5)] for i in range(n)]
            faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
            faces += [(i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n)]
            mesh = self.mesh(kind, vertices, faces)
        elif kind == 'sphere':
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1)
            mesh = bpy.data.meshes.new('Faceted sphere')
            bm.to_mesh(mesh)
            bm.free()
        else:
            raise ValueError(kind)
        self.cache[key] = mesh
        return mesh

    def object(self, name, mesh, at, size, material, rotation=None):
        key = (mesh.name, material)
        if key not in self.cache:
            data = mesh.copy()
            data.materials.append(self.materials[material])
            self.cache[key] = data
        obj = bpy.data.objects.new(name, self.cache[key])
        self.collection.objects.link(obj)
        obj.location = self.offset + Vector(at)
        obj.scale = size
        if rotation is not None:
            obj.rotation_euler = rotation
        return obj

    def box(self, name, at, size, material=None, rotation=None):
        material = material or f'stone{R.randrange(8)}'
        return self.object(name, self.primitive('box'), at, size, material, rotation)

    def cylinder(self, name, at, radius, height, material, n=24):
        return self.object(name, self.primitive('cylinder', n), at, (radius, radius, height), material)

    def cone(self, name, at, radius, height, material, n=12):
        return self.object(name, self.primitive('cone', n), at, (radius, radius, height), material)

    def sphere(self, name, at, size, material):
        return self.object(name, self.primitive('sphere'), at, size, material)

    def beam(self, name, a, b, radius, material, n=12):
        a, b = Vector(a), Vector(b)
        obj = self.cylinder(name, (a+b)/2, radius, (b-a).length, material, n)
        obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
        return obj

    def ring(self, name, at, radius, tube, material, rotation=None, n=48):
        key = ('ring', round(radius, 5), round(tube, 5), n)
        if key not in self.cache:
            vertices = [((radius+tube*math.cos(j*TAU/8))*math.cos(i*TAU/n),
                         (radius+tube*math.cos(j*TAU/8))*math.sin(i*TAU/n), tube*math.sin(j*TAU/8))
                        for i in range(n) for j in range(8)]
            faces = [(i*8+j, ((i+1) % n)*8+j, ((i+1) % n)*8+(j+1) % 8, i*8+(j+1) % 8)
                     for i in range(n) for j in range(8)]
            self.cache[key] = self.mesh('Ring', vertices, faces)
        return self.object(name, self.cache[key], at, (1, 1, 1), material, rotation)

    def light(self, name, at, energy, color, size=1, target=None):
        data = bpy.data.lights.new(name, 'AREA' if target is not None else 'POINT')
        data.energy, data.color = energy, color
        if target is None:
            data.shadow_soft_size = size
        else:
            data.shape, data.size = 'DISK', size
        obj = bpy.data.objects.new(name, data)
        self.collection.objects.link(obj)
        obj.location = self.offset + Vector(at)
        if target is not None:
            obj.rotation_euler = (Vector(target)-Vector(at)).to_track_quat('-Z', 'Y').to_euler()
        return obj

    def candle(self, at, height=.4):
        x, y, z = at
        self.cylinder('Candle holder', (x,y,z+.035), .13, .07, 'bronze')
        self.cylinder('Wax candle', (x,y,z+height/2), .075, height, 'wax')
        self.sphere('Candle flame', (x,y,z+height+.075), (.037,.037,.10), 'flame')

    def chain(self, a, b, links=18):
        a, b = Vector(a), Vector(b)
        for i in range(links):
            at = a+(b-a)*i/max(links-1,1)
            self.ring('Forged chain link', at, .073, .022, 'iron',
                      (math.pi/2, 0, (i % 2)*math.pi/2), n=12)

    def bottle(self, at, radius=.11, height=.45, material='glass'):
        x, y, z = at
        self.cylinder('Bottle body', (x,y,z+height*.34), radius, height*.68, material, 12)
        self.sphere('Bottle shoulder', (x,y,z+height*.68), (radius,radius,height*.16), material)
        self.cylinder('Bottle neck', (x,y,z+height*.84), radius*.42, height*.26, material, 12)
        self.cylinder('Bottle stopper', (x,y,z+height), radius*.5, height*.09, 'wood', 12)

    def brick_wall(self, x, y, width, height, along='x', thickness=.55):
        for row in range(round(height/.38)):
            for col in range(round(width/.78)):
                u = (col+.5)*.78-width/2 + (.19 if row % 2 else -.19)
                at = (x+u,y,(row+.5)*.38) if along == 'x' else (x,y+u,(row+.5)*.38)
                size = (.745,thickness,.345) if along == 'x' else (thickness,.745,.345)
                self.box('Dressed stone block', at, size)

    def arch(self, at, radius, spring, depth=.65):
        x,y,z = at
        for side in [-1,1]:
            for row in range(round(spring/.35)):
                self.box('Arch pier block',(x+side*radius,y,z+(row+.5)*.35),(.46,depth,.32))
        for i in range(19):
            angle = (i+.5)*math.pi/19
            self.box('Arch voussoir',(x+radius*math.cos(angle),y,z+spring+radius*math.sin(angle)),
                     (.46,depth,radius*math.pi/19*.92),rotation=(0,math.pi/2-angle,0))
