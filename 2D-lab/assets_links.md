# Task 5: Assets (free, top-down 16x16 pixel art, one consistent style)

Style choice: Kenney's Tiny Dungeon (CC0) is a top-down 16x16 pack with characters, tiles and items, and Tiny Creatures (CC0) is an expansion made to match it, so heroes, guardians, demons, floors and items all share one look. Recolour the hero purple and the armoured characters white and gold in any pixel editor.

> **Verification note.** I found these through web search; the cloud session could not open the asset sites directly (network blocked), so I could not read the pages themselves. Contents and licences come from search-result summaries. Open each link, look at the preview, and check the licence before you download. The Kenney Pixel UI Pack licence was not confirmed in what I saw.

| Resource | Source |
|---|---|
| Main character | Kenney Tiny Dungeon (CC0): https://kenney-assets.itch.io/tiny-dungeon (also https://opengameart.org/content/tiny-dungeon). Projectiles: Bullet Collection 1 (CC0, top-down): https://opengameart.org/content/bullet-collection-1-m484 |
| Enemy | Holy guardians: armoured characters from Tiny Dungeon (link above), recoloured white and gold. Demons (Repentance): Tiny Creatures (CC0): https://opengameart.org/content/tiny-creatures |
| Ground and platforms | Tiny Dungeon floors, walls and pillars (link above) |
| Background | Tiny Dungeon repeating floor tiles (link above) |
| Collectibles | Points: Gems, Coins, etc. (CC0, 16x16): https://laredgames.itch.io/gems-coins-free. Hearts: Tiny Dungeon items (link above) |
| Sounds | Kenney Sci-Fi Sounds (CC0): https://kenney.nl/assets/sci-fi-sounds. Kenney Interface Sounds: https://opengameart.org/content/interface-sounds. Freesound, CC0 filter: https://freesound.org/search/?q=hit+impact |
| Music | Boss Fight 2 by ansimuz (CC0): https://opengameart.org/content/boss-fight-2. Dark Cavern Ambient (CC0): https://opengameart.org/content/dark-cavern-ambient |
| Interface (points, lives) | Pixel Healthbars and Hearts (CC0): https://unbreaded.itch.io/pixel-health. Kenney Pixel UI Pack: https://www.kenney.nl/assets/pixel-ui-pack |

Notes:
- Freesound licences vary per sound; check the licence on each sound page (CC0 needs no credit, CC-BY needs credit).
- If Tiny Dungeon's knights do not read as "divine" once recoloured, the white-gold guardian drawn for this document (`images/topdown_sprites.png`) can be redrawn as a custom sprite instead.
- The playable level in `game/` does not use these packs: the asset sites were not reachable from the development sandbox, so its textures and sprites are drawn by `game/tools/gen_assets.py`, and its sounds are Kenney CC0 sounds taken from the Python `arcade` package. To use the real packs, replace the PNGs in `game/assets/textures` and `game/assets/sprites` (same file names and sizes).
