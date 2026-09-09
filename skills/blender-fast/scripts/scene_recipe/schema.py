"""Pure-Python validation. A recipe selects trusted functions, never Python code."""
import math
import re

FACTORIES = ('chamber', 'portal', 'staircase', 'forge', 'throne', 'ritual',
             'waterwell', 'collapsed_passage', 'alchemy', 'library', 'armory',
             'supplies', 'hoist', 'organ', 'cage', 'sarcophagus', 'treasure',
             'map_table', 'ossuary', 'chandelier', 'orrery', 'reactor', 'telescope')
MATERIALS = tuple(f'stone{i}' for i in range(8)) + (
    'dark', 'wood', 'woodlight', 'iron', 'bronze', 'silver', 'gold', 'bone',
    'cloth', 'paper', 'glass', 'water', 'flame', 'rune', 'gem', 'wax')


def fields(value, allowed, where):
    if not isinstance(value, dict) or set(value) - set(allowed):
        raise ValueError(f'{where}: expected an object with fields {allowed}')


def number(value, low, high, where):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{where}: expected a number')
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{where}: expected {low} through {high}')


def vector(value, low, high, where):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f'{where}: expected three numbers')
    for v in value:
        number(v, low, high, where)


def validate(recipe):
    fields(recipe, ('version', 'title', 'seed', 'assemblies', 'materials', 'camera', 'lighting'), 'recipe')
    if recipe.get('version') != 1 or isinstance(recipe.get('version'), bool):
        raise ValueError('recipe.version must be 1')
    if not isinstance(recipe.get('title'), str) or not 1 <= len(recipe['title']) <= 120:
        raise ValueError('recipe.title must contain 1–120 characters')
    if not isinstance(recipe.get('seed'), int) or isinstance(recipe['seed'], bool):
        raise ValueError('recipe.seed must be an integer')
    rows = recipe.get('assemblies')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError('recipe.assemblies must contain 1–100 entries')
    seen = set()
    for row in rows:
        fields(row, ('id', 'type', 'at', 'yaw', 'scale', 'seed'), 'assembly')
        identifier = row.get('id')
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', identifier):
            raise ValueError('assembly.id must be a short lowercase identifier')
        if identifier in seen:
            raise ValueError(f'duplicate assembly id: {identifier}')
        seen.add(identifier)
        if row.get('type') not in FACTORIES:
            raise ValueError(f'unknown assembly type: {row.get("type")}')
        vector(row.get('at'), -1000, 1000, identifier + '.at')
        vector(row.get('scale', [1, 1, 1]), .1, 10, identifier + '.scale')
        number(row.get('yaw', 0), -3600, 3600, identifier + '.yaw')
        if 'seed' in row and (not isinstance(row['seed'], int) or isinstance(row['seed'], bool)):
            raise ValueError('assembly.seed must be an integer')
    mats = recipe.get('materials', {})
    fields(mats, MATERIALS, 'materials')
    for name, properties in mats.items():
        fields(properties, ('color', 'roughness', 'metallic', 'emission'), name)
        if 'color' in properties:
            vector(properties['color'], 0, 1, name + '.color')
        for prop in ('roughness', 'metallic'):
            if prop in properties:
                number(properties[prop], 0, 1, name + '.' + prop)
        if 'emission' in properties:
            number(properties['emission'], 0, 100, name + '.emission')
    camera = recipe.get('camera', {})
    fields(camera, ('at', 'target', 'ortho_scale'), 'camera')
    for key in ('at', 'target'):
        if key in camera:
            vector(camera[key], -1000, 1000, 'camera.' + key)
    number(camera.get('ortho_scale', 47), 1, 1000, 'camera.ortho_scale')
    lighting = recipe.get('lighting', {})
    fields(lighting, ('key', 'fill', 'rim', 'world', 'exposure'), 'lighting')
    for key in ('key', 'fill', 'rim', 'world'):
        if key in lighting:
            number(lighting[key], 0, 10, 'lighting.' + key)
    number(lighting.get('exposure', .5), -10, 10, 'lighting.exposure')
    return recipe
