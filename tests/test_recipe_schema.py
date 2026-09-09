import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/blender-fast/scripts'))
from scene_recipe.schema import validate


class RecipeSchemaTests(unittest.TestCase):
    def setUp(self):
        self.recipe = {'version': 1, 'title': 'Validation scene', 'seed': 42,
                       'assemblies': [{'id': 'instrument', 'type': 'telescope', 'at': [0, 0, 0]}]}

    def test_valid_recipe(self):
        self.assertIs(validate(self.recipe), self.recipe)

    def test_duplicate_id_is_rejected(self):
        self.recipe['assemblies'].append(copy.deepcopy(self.recipe['assemblies'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            validate(self.recipe)

    def test_code_and_paths_are_not_a_factory(self):
        for value in ('../geometry.py', '__import__("os")', 'unavailable'):
            self.recipe['assemblies'][0]['type'] = value
            with self.assertRaises(ValueError):
                validate(self.recipe)

    def test_nonfinite_and_negative_scale_are_rejected(self):
        for value in ([1, float('nan'), 1], [1, -1, 1], [1, float('inf'), 1]):
            self.recipe['assemblies'][0]['scale'] = value
            with self.assertRaises(ValueError):
                validate(self.recipe)

    def test_malformed_and_unknown_properties_are_rejected(self):
        for updates in ({'materials': {'absent': {'color': [1, 0, 0]}}},
                        {'lighting': {'world': 'bright'}}, {'execute': 'code'},
                        {'seed': True}, {'camera': {'at': [0, 1]}}):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                validate(self.recipe | updates)


if __name__ == '__main__':
    unittest.main()
