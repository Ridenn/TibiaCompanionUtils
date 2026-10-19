"""Publish a complete extraction as immutable static tiles and a small catalog.

Usage: python prepare_world_map.py PATH_TO_DOWNLOAD
No API credentials, session data, scripts or APK files are copied.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

source = Path(sys.argv[1]).resolve()
destination = Path(__file__).resolve().parents[1] / 'world'
info_bytes = (source / 'map-info.json').read_bytes()
info = json.loads(info_bytes)
extraction = json.loads((source / 'all-maps.json').read_text(encoding='utf-8'))
if not extraction.get('complete') or extraction['version'] != info['version']:
    raise ValueError('A complete, consistent extraction is required.')
version = 'v1-' + hashlib.sha256(info_bytes).hexdigest()[:12]
styles = []
tile_count = 0
for style in info['styles']:
    if style['name'] not in ('Minimap', 'Stylized', 'Satellite'):
        continue
    name = style['name'].lower()
    styles.append(dict(id=name, width=style['fullWidth'], height=style['fullHeight'],
                       tileSize=style['tileSize'], zoomLevels=style['zoomLevels'],
                       floors=style['levels'], originX=style['bounds']['minX'],
                       originY=style['bounds']['minY'], pixelsPerCoordinate=style['meterSize']))
    for entry in extraction['maps']:
        if entry['style'] != name:
            continue
        # Locate by relative directory name so the extraction can be moved.
        tile_source = source / Path(entry['directory']).name
        tile_destination = destination / version / name / str(entry['floor']) / str(entry['zoom'])
        tile_destination.mkdir(parents=True, exist_ok=True)
        for row in range(entry['rows']):
            for col in range(entry['columns']):
                name_on_disk = f'{col}_{row}.webp'
                tile = tile_source / name_on_disk
                with tile.open('rb') as stream:
                    header = stream.read(12)
                if header[:4] != b'RIFF' or header[8:12] != b'WEBP':
                    raise ValueError(f'Invalid WebP tile: {tile}')
                shutil.copyfile(tile, tile_destination / name_on_disk)
                tile_count += 1
if tile_count != extraction['tiles']:
    raise ValueError('Tile count differs from extraction manifest.')
catalog = dict(version=version, styles=styles)
destination.mkdir(parents=True, exist_ok=True)
(destination / 'catalog.json').write_text(json.dumps(catalog, indent=2) + '\n', encoding='utf-8')
print(f'Prepared {tile_count} tiles in {destination / version}')
