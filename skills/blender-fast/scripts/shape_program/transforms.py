"""Small dependency-free affine matrix utilities; matrices use row-major storage."""
import math


def identity():return [[float(i==j) for j in range(4)] for i in range(4)]


def multiply(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def pose(at=(0,0,0),rotation=(0,0,0),scale=(1,1,1)):
    x,y,z=[math.radians(v) for v in rotation]
    cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    rx=[[1,0,0,0],[0,cx,-sx,0],[0,sx,cx,0],[0,0,0,1]]
    ry=[[cy,0,sy,0],[0,1,0,0],[-sy,0,cy,0],[0,0,0,1]]
    rz=[[cz,-sz,0,0],[sz,cz,0,0],[0,0,1,0],[0,0,0,1]]
    result=multiply(multiply(rz,ry),rx)
    for i in range(3):
        for j in range(3):result[i][j]*=scale[j]
        result[i][3]=at[i]
    return result


def point(matrix,p):return [sum(matrix[i][j]*p[j] for j in range(3))+matrix[i][3] for i in range(3)]
