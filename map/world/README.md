# World map tiles

Static assets consumed by TibiaCompanion. No calls to the old app API are needed.

- `catalog.json` describes style dimensions, game-coordinate origins, pixels per
  coordinate, floors, zoom levels and the immutable asset version.
- `{version}/{style}/{floor}/{zoom}/{column}_{row}.webp` is an original tile.
- Styles: `minimap`, `stylized`, `satellite`. Satellite covers floors 0–7;
  the other two cover floors 0–15. All currently have one zoom level (0).

The client fetches visible tiles through jsDelivr, with raw GitHub as a fallback:

`https://cdn.jsdelivr.net/gh/Ridenn/TibiaCompanionUtils@main/map/world/catalog.json`

Keep old version directories while installed app versions may still reference
them. Publish the complete version directory before changing the catalog.
An update uses a new version directory, never changes existing tiles in place.

To prepare a complete extraction: `python map/tools/prepare_world_map.py PATH_TO_DOWNLOAD`.
The tool copies only validated WebP tiles and writes the public catalog. It does
not copy keys, session data, the original APK, or decompiled code.
