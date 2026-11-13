# DMV v0.5 — Character artwork batch

This branch is the v0.5 artwork workstream, not an approved release.

## Replaced in source
- Dame Floss full-size 64x64 trainer front portrait and 64x320 five-frame back battle art.
- DJ early, late, and champion 64x64 battle trainer portraits, each with separate poses.
- Dame Floss and DJ 64x96 Oak opening portraits.
- Matching indexed image palettes for these seven graphics resources.
- DJ overworld silhouette from the v0.4d draft; overworld revisions not yet confirmed on Xbox.

## Prepared, not yet connected to game events
- `graphics/dmv/portraits/dame_talk.png`
- `graphics/dmv/portraits/dj_talk.png`
- `graphics/dmv/portraits/dame_win.png`
- `graphics/dmv/portraits/dj_win.png`

**The portrait images alone do not make dialogue or victory overlays work.**
A proper code/UI integration and in-game testing are required before these can be called complete.

## v0.5 build policy
No ROM rebuild after every image. Compile `DMV-v05.gba` only after changes are ready for the combined test.
Do not overwrite the previous working test builds.

## Planned tests
1. DJ overworld walking poses, front/back/left/right.
2. Dame Floss walking, biking, running and common animation variants.
3. DJ early, late and champion battle poses.
4. Dame Floss front battle pic and five-frame back throw animation.
5. Both 64x96 Oak opening portraits.
6. Dialogue and win portrait behavior **only after integrated in code**.
7. Existing starter randomizer and rival Pokémon selection.
8. Saving and loading.
9. No palette, alignment, or transparency glitches.

## Automated validation
Run `python3 tools/check_dmv_v05_art.py` in Codespaces to check PNG structure, dimensions, palettes and transparency.
