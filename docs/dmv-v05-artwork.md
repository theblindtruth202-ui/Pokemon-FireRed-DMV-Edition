# DMV v0.5 character artwork — development audit

## Goal
Combine multiple visual fixes into one Xbox test ROM. Do not build a ROM for one sprite change.

## Source artwork ready on this branch
- DJ's 16x32 overworld animation: `graphics/object_events/pics/people/blue.png` — silhouette-preserving draft from v0.4d; not yet Xbox approved.
- Dame Floss's existing overworld art: `graphics/object_events/pics/people/red_normal.png` — unchanged, retest.
- DJ's existing battle portraits: `graphics/trainers/front_pics/rival_early_front_pic.png`, `rival_late_front_pic.png`, and `champion_rival_front_pic.png` — unchanged, retest.
- Dame Floss's existing trainer front and back art: `graphics/trainers/front_pics/red_front_pic.png`, `graphics/trainers/back_pics/red_back_pic.png` — unchanged, retest.
- Opening introduction full-body portraits: `graphics/oak_speech/red/pic.png` and `graphics/oak_speech/rival/pic.png` — new 64x96 art based on existing trainer artwork; matching 32-color palettes changed; not yet Xbox tested.

## Remaining artwork tasks
- Implement in-dialogue face-to-face portraits for selected important conversations (requires new UI/code, not just PNG replacement).
- Audit movement variants, trainer card, and celebration/victory art; only count a feature completed if gameplay confirms it.
- Do not enlarge walking sprites for full-size trainer art.

## One-ROM Xbox verification
1. DJ's front/back/side walking poses and distortion regression.
2. Dame Floss's overworld and movement animation.
3. Player and rival battle-introduction full-size portraits.
4. Oak's opening character portraits.
5. Battle-ending presentation/celebration and any newly implemented dialogue portraits.
6. Starter randomizer, rival battle, and save/load regression.

## Safety
Previous ROMs remain separate. Never use a failed or untested artwork version as the production baseline. Name the next combined test ROM `DMV-v05.gba`.
