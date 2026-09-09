import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/blender-fast/scripts'))
from shape_program.teaching import load_library,suggest,compose,DEFAULT_LIBRARY
from shape_program.expand import expand


class TeachingChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lessons=load_library()
        cls.model=json.loads((DEFAULT_LIBRARY/'selector.json').read_text())

    def test_all_executable_lessons(self):
        self.assertEqual(len(self.lessons),8)
        for row in self.lessons:self.assertGreater(expand(row['program'])['budget']['parts'],0)

    def test_held_out_selector_captions(self):
        for row in self.lessons:
            for caption in row['captions']['test']:
                with self.subTest(caption=caption):self.assertEqual(suggest(caption,self.model,self.lessons)[0]['id'],row['id'])

    def test_unrelated_words_and_stale_model(self):
        self.assertEqual(suggest('quasarabcdef',self.model,self.lessons),[])
        stale=copy.deepcopy(self.lessons);stale[0]['summary']='Changed'
        with self.assertRaisesRegex(ValueError,'stale'):suggest('arch',self.model,stale)

    def test_composition_dependencies_and_override(self):
        p=compose({'title':'Test','definitions':{'garden':{'nodes':[{'op':'call','use':'revolved_bowl'},{'op':'call','use':'branch_crown'}]}},
            'assemblies':[{'id':'one','use':'garden'}],'palette':{'stone':{'color':[.1,.2,.3]}}},self.lessons)
        self.assertEqual(set(p['definitions']),{'garden','revolved_bowl','branch_crown'})
        self.assertEqual(p['palette']['stone']['color'],[.1,.2,.3])
        self.assertGreater(expand(p)['budget']['parts'],3)

    def test_composition_rejects_missing_definitions(self):
        with self.assertRaises(ValueError):compose({'title':'Test','assemblies':[{'id':'one','use':'missing'}]},self.lessons)


if __name__=='__main__':unittest.main()
