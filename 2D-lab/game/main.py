"""PERFORATED, Level 1 (Pride). Run:  python main.py

Controls: WASD / arrows move, SHIFT or SPACE dash, shooting is automatic,
ESC / P pause, M music, L language (title screen).
"""
import os
import sys

# make the game runnable from any folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import settings as S  # noqa: E402
from game import Game  # noqa: E402


def read_move():
    keys = pygame.key.get_pressed()
    x = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
    y = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
    return float(x), float(y)


def main():
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    pygame.display.set_caption(S.TITLE)
    flags = pygame.SCALED | pygame.RESIZABLE
    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H), flags)
    game = Game(screen)
    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(S.FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif game.handle_key(ev.key) == "quit":
                    running = False
            elif ev.type == pygame.MOUSEMOTION:
                game.handle_mouse(ev.pos, False)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                game.handle_mouse(ev.pos, True)
        game.update(dt, read_move())
        game.draw(screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
