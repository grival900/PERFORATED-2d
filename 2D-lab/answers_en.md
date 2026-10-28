# Lab 1 answers (English version of the PDF)

The submission PDF is `Laboratoriska_vezba_1_PERFORATED.pdf` (Macedonian, filled into the original layout). Task 6 feedback is invented, as requested; replace it with real feedback if you collect some.

## Task 1: Idea
PERFORATED is a top-down 2D game in the style of Vampire Survivors: with automatic shooting and fast movement the player survives waves of holy guardians, and each kill fills the bar of the level's sin (for example Pride), so that he commits the seven sins. Then, cursed into Limbo, he undoes the sins in reverse order while fleeing demons, and in the end dissolves into the world and cleanses it of hatred.

## Task 2: Story
- **Beginning:** A nameless man, drunk on his own greatness, decides to take whatever he wants and commits the seven sins one by one: Pride, Greed, Lust, Envy, Gluttony, Wrath, Sloth. The holy guardians, radiant sentinels of the world, hunt him in waves to punish him. Each sin leaves a glowing hole in his body.
- **Middle:** After the last sin he is cursed and sent to Limbo, where each sin becomes a world he must undo in reverse order, from Sloth to Pride. Now demons hunt him, and each wrong he repairs fills the matching hole with light.
- **End:** On the final level, undoing Pride, he realises the world's hatred can only be cleansed if he sacrifices himself. He dissolves into the world as the light from the holes takes over his whole body.

## Task 3: Characters
| | Main character | Enemy | NPC |
|---|---|---|---|
| Name | The Nameless | Holy Guardian (in Repentance: demon) | The Ferryman |
| Role | Player: first a sinner, then a sinner seeking redemption | Sentinel that hunts the player in waves | Guide: offers upgrades and heals, via a lantern |
| Personality | Arrogant and reckless at first, later quiet and guilty | Cold, merciless, faceless; follows orders | Calm, ironic, tired |
| Motivation | First: take everything. Then: undo the sins and save the world | Punish the sinner by decree of the world (demons: keep him in Limbo) | Wants out of Limbo, possible only if someone redeems himself |
| Abilities | Fast momentum movement, automatic piercing shots at the nearest enemy, dash with invulnerability (2 charges), upgrades | Chases without stopping, arrives in big groups; stronger ones are faster and throw light spears | At 25%, 50%, 75% offers a choice of 3 upgrades; heals 1 heart |
| Limitations | 3 hearts; dash recharges in 3 s; no manual aiming; shots are slow at first | Low health (1-2 hits); cannot pass walls; turns slowly | Cannot leave the lantern; does not fight |
| Appearance | Lean, torn purple hooded coat, ash-grey skin, teal scarf, glowing teal holes in the body | Hovering armour of white and gold light, orbiting gold shards, glowing core, faceless; no wings, halo or symbols | Tall, tattered blue hood with no face, teal lantern on a staff |

Images: `images/main_character_side.png` (side profile, used in the PDF), `images/characters_sheet.png` (all four characters), `images/topdown_sprites.png` (how hero and guardian look in the top-down game).

## Task 4: Level
Level 1, Pride: one square arena seen from above. The player starts in the middle, guardians arrive from all edges, kills give points that fill the Pride bar, and when the bar is full the exit at the top opens. Sketch: `images/level1_pride_sketch.png`.

Difficulty rises in four stages of the bar: 1) a few slow guardians; 2) faster groups, first upgrade at 25%; 3) guardians with light spears (ranged), second upgrade at 50%; 4) a swarm plus an elite guardian, third upgrade at 75%.

Mandatory for the first version: top-down movement (WASD or arrows) with acceleration and inertia; automatic piercing shots at the nearest enemy; dash (Shift, 2 charges, 3 s refill, brief invulnerability); holy guardians spawning in waves from the edges and chasing the player, touch = -1 heart (3 hearts); kills give points that fill the Pride bar, with an upgrade pick at 25/50/75%; win when the bar is full, lose when hearts run out; title screen, pause and end screen; 3 levels: Pride, Greed and Limbo (Repentance of Pride).

## Task 5: Assets
See `assets_links.md`.

## Task 6: Feedback (invented)
Colleagues like the fast movement with the dash and that every kill visibly fills the Pride bar, so progress is always visible. They would change one thing: at the start of the level there should be fewer guardians on screen, to leave time to learn the movement.

## Task 7: Summary
| Part | Answer |
|---|---|
| Title | PERFORATED |
| Idea in one sentence | A Vampire Survivors-style top-down game: kill waves of holy guardians to commit the seven sins, then undo them in Limbo. |
| Target audience | Players 14+ who like fast action games (Vampire Survivors, Hades) and dark stories |
| Story | Start: a man commits the seven sins, hunted by holy guardians. Middle: cursed to Limbo, he undoes them in reverse order, hunted by demons. End: undoing Pride, he sacrifices himself and dissolves into the world, cleansing it of hatred. |
| Main character | The Nameless: lean, purple coat, teal holes; arrogant, then remorseful |
| Enemies / NPC | Holy guardians (Sins), demons (Repentance). NPC: the Ferryman, offers upgrades and heals |
| Core mechanic and controls | WASD/arrows: move; Shift: dash; shooting is automatic. Kills = points = the sin's bar fills; upgrade pick at 25/50/75% |
| Win condition | The Pride bar reaches 100% and the exit opens; after the last level the character dissolves |
| Lose condition | All 3 hearts lost (touch of a guardian or spear); the level restarts |
| Level sketch | `images/level1_pride_sketch.png` |
| What makes it fun? | Fast movement and dashing through a swarm, visible progress on the bar, upgrades and short levels |
| Change after feedback | Stage 1 now starts with only a few slow guardians; bigger groups come later |
| LLM conversations used | https://claude.ai/code/session_015REauJjEStJtMwV1bMRQav (make the chat shareable before submitting) |

## Task 8
Implemented: Level 1 (Pride) is playable in `game/` (Python + pygame). See `game/README.md` to run it: `pip install pygame-ce` then `python main.py`.
