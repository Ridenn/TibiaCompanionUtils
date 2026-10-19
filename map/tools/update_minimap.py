"""Convert a pinned TibiaMaps gh-pages checkout into immutable Minimap tiles.

Usage: python map/tools/update_minimap.py SOURCE_CHECKOUT
Requires Pillow. Stylized and Satellite catalog entries are left unchanged.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

source = Path(sys.argv[1]).resolve()
world = Path(__file__).resolve().parents[1] / 'world'
revision = subprocess.check_output(
    ['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
version = 'tibiamaps-' + revision
catalog_path = world / 'catalog.json'
catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
current = next(style for style in catalog['styles'] if style['id'] == 'minimap')
if current.get('tileVersion') == version:
    print('Minimap already uses this TibiaMaps revision.')
    sys.exit(0)

ids = json.loads((source / 'mapper' / 'tiles.json').read_text(encoding='utf-8'))
coordinates = set()
for tile_id in ids:
    if not re.fullmatch(r'\d+_\d+_\d+', tile_id):
        raise ValueError(f'Invalid upstream tile ID: {tile_id}')
    x, y, floor = map(int, tile_id.split('_'))
    if x % 256 or y % 256 or not 0 <= floor <= 15:
        raise ValueError(f'Invalid upstream coordinates: {tile_id}')
    coordinates.add((x, y, floor))
if {floor for _, _, floor in coordinates} != set(range(16)):
    raise ValueError('All sixteen floors are required.')
origin_x = min(x for x, _, _ in coordinates)
origin_y = min(y for _, y, _ in coordinates)
width = max(x for x, _, _ in coordinates) + 256 - origin_x
height = max(y for _, y, _ in coordinates) + 256 - origin_y
if width > 32768 or height > 32768:
    raise ValueError('Map dimensions exceed the client limit.')

# Generate everything before publishing the catalog. A missing source file or a
# failed conversion leaves the previously published map intact.
with tempfile.TemporaryDirectory() as temporary:
    output = Path(temporary) / version
    blank = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    digest = hashlib.sha256()
    count = 0
    for floor in range(16):
        target = output / 'minimap' / str(floor) / '0'
        target.mkdir(parents=True)
        for row in range(height // 256):
            for col in range(width // 256):
                x, y = origin_x + col * 256, origin_y + row * 256
                image = blank
                if (x, y, floor) in coordinates:
                    path = source / 'mapper' / f'Minimap_Color_{x}_{y}_{floor}.png'
                    with Image.open(path) as original:
                        if original.size != (256, 256):
                            raise ValueError(f'Unexpected tile size: {path}')
                        image = original.convert('RGBA')
                    # Black means unexplored in Tibia's minimap. Make only those
                    # pixels transparent so the water/lower floors show through.
                    r, g, b, alpha = image.split()
                    known = ImageChops.lighter(ImageChops.lighter(r, g), b).point(
                        lambda value: 255 if value else 0)
                    image.putalpha(ImageChops.multiply(alpha, known))
                tile = target / f'{col}_{row}.webp'
                image.save(tile, 'WEBP', lossless=True, exact=True)
                digest.update(tile.read_bytes())
                count += 1
    metadata = dict(repository='https://github.com/tibiamaps/tibia-map-data',
                    revision=revision, sha256=digest.hexdigest(), tiles=count)
    (output / 'source.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    destination = world / version
    if destination.exists():
        raise ValueError('Refusing to overwrite an immutable map version.')
    import shutil
    shutil.copytree(output, destination)

current.update(width=width, height=height, tileSize=256, zoomLevels=1,
               floors=list(range(16)), originX=origin_x, originY=origin_y,
               pixelsPerCoordinate=1, tileVersion=version)
temporary_catalog = catalog_path.with_suffix('.json.part')
temporary_catalog.write_text(json.dumps(catalog, indent=2) + '\n', encoding='utf-8')
os.replace(temporary_catalog, catalog_path)
print(f'Published {count} lossless Minimap tiles from {revision}.')
