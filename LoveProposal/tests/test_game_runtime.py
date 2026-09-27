"""Headless smoke tests for scene rendering and Escape handling."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from main import ProposalGame, STORY


class ProposalGameRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = ProposalGame()

    def tearDown(self) -> None:
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.quit()

    def test_every_story_beat_renders(self) -> None:
        for index, beat in enumerate(STORY):
            with self.subTest(beat=beat.key):
                self.game.beat_index = index
                self.game.beat_elapsed = min(1.2, beat.duration / 2)
                self.game.draw()
                self.game.update(1 / 60)

    def test_escape_leaves_fullscreen_without_crashing(self) -> None:
        self.assertTrue(self.game.fullscreen)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        # SDL's dummy video backend cannot safely switch modes, so assert the
        # game requests the windowed mode without asking that backend to apply it.
        with patch("main.pygame.display.set_mode", return_value=self.game.screen) as set_mode:
            self.game.handle_event(event)
        set_mode.assert_called_once()
        self.assertEqual(set_mode.call_args.args[1], pygame.SCALED | pygame.RESIZABLE)
        self.assertFalse(self.game.fullscreen)
        self.assertTrue(self.game.running)
        self.game.draw()

    def test_proposal_choices_are_interactive(self) -> None:
        choices_index = next(i for i, beat in enumerate(STORY) if beat.key == "choices")
        self.game.beat_index = choices_index
        self.game.beat_elapsed = 3
        self.game.draw()
        self.assertEqual([label for _, label in self.game.choice_hotspots], ["YES", "ABSOLUTELY"])
        self.game.choose("YES")
        self.assertEqual(self.game.beat.key, "accept")

    def test_run_loop_starts_and_handles_escape(self) -> None:
        escape = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        quit_event = pygame.event.Event(pygame.QUIT)
        with patch("main.pygame.display.set_mode", return_value=self.game.screen) as set_mode:
            with patch("main.pygame.event.get", side_effect=[[escape], [quit_event]]):
                self.game.run()
        set_mode.assert_called_once()
        self.assertFalse(self.game.fullscreen)
        self.assertFalse(self.game.running)


if __name__ == "__main__":
    unittest.main(verbosity=2)
