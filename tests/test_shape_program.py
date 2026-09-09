import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/blender-fast/scripts'))
from shape_program.expressions import evaluate
from shape_program.expand import expand
from shape_program.transforms import point


def program():
    return {'version':1,'title':'Validation fixture','palette':{'stone':{'color':[.3,.4,.5]}},
        'definitions':{'block':{'params':{'w':2},'anchors':{'top':[0,0,'=w']},'nodes':[{'op':'box','size':['=w',1,1]}]}},
        'assemblies':[{'id':'base','use':'block'}]}


class ShapeChecks(unittest.TestCase):
    def test_expressions(self):
        self.assertAlmostEqual(evaluate('=2*sin(pi/2)+x',{'x':3}),5)
        for x in [True,float('nan'),1e8,'=__import__("os")','=x.real','=x[0]','=2**8','=1/0','=sqrt(-1)','=unknown']:
            with self.subTest(x=x),self.assertRaises(ValueError):evaluate(x,{'x':2})

    def test_expansion_and_attachments(self):
        p=program();p['assemblies'][0].update(rotation=[0,0,90],scale=[2,1,1],at=[10,0,0])
        p['assemblies'].insert(0,{'id':'cap','use':'block','attach':{'to':'base.top'},'at':[1,0,0]})
        graph=expand(p);by_id={r['id']:r for r in graph['assemblies']}
        self.assertEqual(by_id['base']['parts'][0]['size'],[2,1,1])
        for actual,want in zip(point(by_id['cap']['matrix'],[0,0,0]),[10,2,2]):self.assertAlmostEqual(actual,want)

    def test_transform_excluded_from_shape_hash(self):
        p=program();a=expand(p);p['assemblies'][0]['at']=[3,4,5];b=expand(p)
        self.assertEqual(a['assemblies'][0]['shape_hash'],b['assemblies'][0]['shape_hash'])
        self.assertNotEqual(a['program_sha256'],b['program_sha256'])

    def test_nested_repetition(self):
        p=program();p['definitions']['block']['nodes']=[{'op':'repeat','count':4,'turn':[0,0,90],'children':[{'op':'box','at':[3,0,0],'size':[1,1,'=i+1']}]}]
        rows=expand(p)['assemblies'][0]['parts'];self.assertEqual(len(rows),4)
        self.assertEqual([r['size'][2] for r in rows],[1,2,3,4])
        self.assertAlmostEqual(rows[1]['matrix'][1][3],3)

    def test_cycles_and_unknowns(self):
        for mutation in ('calls','attachments','missing_anchor','unknown_field','unknown_op','bad_camera'):
            p=program()
            if mutation=='calls':p['definitions']['block']['nodes']=[{'op':'call','use':'block'}]
            elif mutation=='attachments':p['assemblies'][0]['attach']={'to':'base.top'}
            elif mutation=='missing_anchor':p['assemblies'].append({'id':'cap','use':'block','attach':{'to':'base.nope'}})
            elif mutation=='unknown_field':p['execute']='anything'
            elif mutation=='unknown_op':p['definitions']['block']['nodes'][0]['op']=[]
            else:p['camera']={'at':['=0',0,0],'target':[0,0,0]}
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):expand(p)

    def test_empty_repeat_fuel(self):
        p=program();node={'op':'group','children':[]}
        for _ in range(4):node={'op':'repeat','count':512,'children':[node]}
        p['definitions']['block']['nodes']=[node]
        with self.assertRaisesRegex(ValueError,'expansion budget'):expand(p)

    def test_surface_and_sweep_rejected(self):
        for node in [{'op':'surface','vertices':[[0,0,0],[1,0,0],[1,1,0]],'faces':[[0,1,3]]},
            {'op':'sweep','path':[[0,0,0],[0,0,0]],'radii':1},
            {'op':'lathe','profile':[[0,0],[1,1]]}]:
            p=program();p['definitions']['block']['nodes']=[node]
            with self.assertRaises(ValueError):expand(p)

    def test_numeric_materials(self):
        p=program();p['palette']['stone']['roughness']='=.5';p['lighting']={'key':'=2/2'}
        graph=expand(p);self.assertEqual(graph['palette']['stone']['roughness'],.5)
        self.assertEqual(graph['lighting']['key'],1)


if __name__=='__main__':unittest.main()
