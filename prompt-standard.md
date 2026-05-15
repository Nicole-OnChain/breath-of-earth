# Breath of Earth — Prompt Standard v3

## Characters
- (Lyra @image 1)
- (Ronan @image 3)
- (Caspian @image 5)
- (Zara @image 6)

## Backdrop References
- Named with image number, e.g. "holding cell @image 7"
- **1 backdrop image max per prompt.** If a scene needs 2 backdrops, split into 2 separate clips.

## Positioning
- `left frame` / `right frame` / `center frame`
- `facing right` / `facing left`
- `foreground` / `background`

## Prompt Template
```
(Character @image #) [position] [action], [backdrop @image #], [camera angle], [lighting], cinematic fantasy illustration — painterly, jewel-tone palette, volumetric light, [specific sound], no music, sound effects only
```

## Example
```
(Lyra @image 1) center frame reaching through iron bars, holding cell @image 7, medium shot, moonlight through bars, cinematic fantasy illustration — painterly, jewel-tone palette, volumetric light, breathing and wind distant, no music, sound effects only
```

## What's IN every prompt
- ✅ Character name + @image reference
- ✅ Positioning (left/right/center, facing direction)
- ✅ Action description
- ✅ Backdrop @image reference (1 max)
- ✅ Camera angle
- ✅ Lighting
- ✅ Style tag: `cinematic fantasy illustration — painterly, jewel-tone palette, volumetric light`
- ✅ Sound direction (always — prevents AI adding music)

## What's NOT in prompts
- ❌ `9:16 vertical`
- ❌ Full character descriptions (hair color, eye color, etc.)
- ❌ Multiple backdrop descriptions (split into 2 clips instead)

## Backdrop Image Descriptions (generated separately in Image tab)
Backdrop images get full visual descriptions — that's where the detail goes, not in the video prompt. Example:

> A rough stone cell carved into rock, iron bars cutting into the stone, no light inside except faint moonlight filtering from outside, dark and cramped, marks scratched into the walls, cinematic fantasy illustration — painterly, atmospheric fog and volumetric light, jewel-tone palette, 9:16 vertical

## Sound Direction Options
- `no music, sound effects only` — default for most scenes
- `ambient [wind/jungle/water] only, no music` — quiet atmospheric scenes
- `heartbeat rising, no music, sound effects only` — tension
- `near silence, just breathing, no music` — intimate/emotional
- `wind picking up then wind roaring, no music, sound effects only` — action

## Positioning Rules (Episode 4 standard)
- **Ronan = LEFT side** (grounded, steady, stays put)
- **Lyra = RIGHT side** (POV character, we see her reactions)
- **When across a fire:** Ronan LEFT, Lyra RIGHT