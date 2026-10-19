# World map tiles

Static assets consumed by TibiaCompanion. No calls to the old app API are needed.

- `catalog.json` describes style dimensions, game-coordinate origins, pixels per
  coordinate, floors, zoom levels and the immutable asset version.
- `{version}/{style}/{floor}/{zoom}/{column}_{row}.webp` is an original tile.
- An optional `tileVersion` on a style overrides the catalog version for its
  tile paths. This allows Minimap updates without duplicating the other styles.
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

## Minimap source and updates

Minimap is sourced directly from [TibiaMaps](https://github.com/tibiamaps/tibia-map-data),
using the coordinate-named `mapper/Minimap_Color_*.png` tiles on `gh-pages`.
The daily `Update Minimap from TibiaMaps` workflow (also manually dispatchable)
converts a consistent checkout into lossless WebP tiles. Black unexplored pixels
become transparent; other colors are preserved. Missing tiles within the bounds
are transparent. All sixteen floors share bounds derived from the upstream index.

`python map/tools/update_minimap.py SOURCE_CHECKOUT` publishes the complete
immutable `tibiamaps-{commit}` directory before updating the Minimap catalog entry.
`source.json` records the source repository, revision and output digest.
Stylized and Satellite keep their existing sources and versions. Older versions
remain available for clients with cached catalogs. The app caches the catalog
for 24 hours and keeps downloaded tiles available offline.
