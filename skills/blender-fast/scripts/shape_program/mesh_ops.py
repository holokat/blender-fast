"""Blender backend for the language's geometry primitives."""
import math
import bpy
from mathutils import Vector, Matrix
from .expand import digest


def strips(rows, segments, caps=True):
    faces = [(r*segments+j, r*segments+(j+1)%segments,
              (r+1)*segments+(j+1)%segments, (r+1)*segments+j)
             for r in range(rows-1) for j in range(segments)]
    if caps:
        faces += [tuple(reversed(range(segments))), tuple(range((rows-1)*segments, rows*segments))]
    return faces


def lathe(spec):
    n = spec['segments']
    vertices = [(r*math.cos(i*math.tau/n), r*math.sin(i*math.tau/n), z)
                for r,z in spec['profile'] for i in range(n)]
    return vertices, strips(len(spec['profile']), n)


def sweep(spec):
    path = [Vector(p) for p in spec['path']]
    vertices, normal = [], None
    n = spec['segments']
    for i,p in enumerate(path):
        tangent = (path[min(i+1,len(path)-1)]-path[max(0,i-1)])
        if tangent.length < 1e-7:
            tangent = path[i]-path[i-1]
        tangent.normalize()
        if normal is not None:
            normal = normal - tangent*normal.dot(tangent)
        if normal is None or normal.length < 1e-7:
            axis = min((Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))), key=lambda a:abs(a.dot(tangent)))
            normal = tangent.cross(axis)
        normal.normalize()
        binormal = tangent.cross(normal).normalized()
        for j in range(n):
            a = j*math.tau/n
            vertices.append(tuple(p + spec['radii'][i]*(normal*math.cos(a)+binormal*math.sin(a))))
    return vertices, strips(len(path),n,spec['caps'])


def create(geometry, spec, root):
    op, name, material = spec['op'], spec['name'], spec['material']
    if op in ('box','sphere'):
        obj = getattr(geometry,op)(name,(0,0,0),spec['size'],material)
    elif op in ('cylinder','cone'):
        obj = getattr(geometry,op)(name,(0,0,0),spec['radius'],spec['height'],material,n=spec['segments'])
    elif op == 'ring':
        obj = geometry.ring(name,(0,0,0),spec['radius'],spec['tube'],material,n=spec['segments'])
    elif op == 'beam':
        obj = geometry.beam(name,spec['a'],spec['b'],spec['radius'],material,n=spec['segments'])
    elif op == 'text':
        data = bpy.data.curves.new(name,'FONT')
        data.body, data.size, data.extrude = spec['text'],spec['size'],spec['depth']
        data.align_x = 'CENTER'
        data.materials.append(geometry.materials[material])
        obj = bpy.data.objects.new(name,data)
        geometry.collection.objects.link(obj)
    else:
        shape = {k:v for k,v in spec.items() if k not in ('name','matrix','material')}
        key = ('shape',digest(shape))
        if key not in geometry.cache:
            vertices, faces = (spec['vertices'],spec['faces']) if op=='surface' else globals()[op](spec)
            geometry.cache[key] = geometry.mesh(op,vertices,faces)
        obj = geometry.object(name,geometry.cache[key],(0,0,0),(1,1,1),material)
    # Store full affine matrices without decomposing shear into location/scale.
    intrinsic = obj.matrix_basis.copy()
    obj.parent = root
    obj.matrix_parent_inverse = Matrix(spec['matrix']) @ intrinsic
    obj.matrix_basis = Matrix.Identity(4)
    return obj
