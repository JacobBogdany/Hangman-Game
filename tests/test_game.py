"""Unit tests for the HangmanGame core game engine.

Compatible with both standard library unittest and pytest.
"""

import unittest
from game import (
    HangmanGame,
    HangmanError,
    InvalidGuessError,
    DuplicateGuessError,
    GameOverError,
)


class TestHangmanGameInitialization(unittest.TestCase):
    """Tests for game instantiation and initial state."""

    def test_initial_state_defaults(self):
        game = HangmanGame("apple")
        self.assertEqual(game.word, "apple")
        self.assertEqual(game.max_incorrect_guesses, 6)
        self.assertEqual(game.remaining_guesses, 6)
        self.assertEqual(game.guessed_letters, [])
        self.assertEqual(game.incorrect_letters, [])
        self.assertEqual(game.status, "playing")
        self.assertFalse(game.is_won)
        self.assertFalse(game.is_lost)
        self.assertFalse(game.is_game_over)
        self.assertEqual(game.get_pattern(), "_ _ _ _ _")

    def test_case_and_whitespace_normalization(self):
        game = HangmanGame("  BaNaNa  ")
        self.assertEqual(game.word, "banana")
        self.assertEqual(game.get_pattern(), "_ _ _ _ _ _")

    def test_custom_max_incorrect_guesses_and_game_id(self):
        game = HangmanGame("cat", max_incorrect_guesses=4, game_id="game_123")
        self.assertEqual(game.max_incorrect_guesses, 4)
        self.assertEqual(game.remaining_guesses, 4)
        self.assertEqual(game.game_id, "game_123")

    def test_invalid_word_raises_value_error(self):
        invalid_words = [
            "",
            "   ",
            "hello world",  # contains space
            "cat123",       # contains digits
            "dog!",         # contains punctuation
            None,           # non-string
            12345,          # non-string
        ]
        for word in invalid_words:
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    HangmanGame(word)  # type: ignore

    def test_invalid_max_incorrect_guesses_raises_value_error(self):
        invalid_maxes = [0, -1, -5, "6", None]
        for max_val in invalid_maxes:
            with self.subTest(max_val=max_val):
                with self.assertRaises(ValueError):
                    HangmanGame("valid", max_incorrect_guesses=max_val)  # type: ignore


class TestGuessValidation(unittest.TestCase):
    """Tests for input validation on guesses."""

    def test_valid_lowercase_and_uppercase_guess(self):
        game = HangmanGame("python")
        state1 = game.guess("P")
        self.assertIn("p", game.guessed_letters)
        self.assertEqual(state1["pattern"], "p _ _ _ _ _")

        state2 = game.guess("  Y  ")
        self.assertIn("y", game.guessed_letters)
        self.assertEqual(state2["pattern"], "p y _ _ _ _")

    def test_invalid_guess_raises_invalid_guess_error(self):
        invalid_guesses = [
            "",
            "   ",
            "ab",
            "python",
            "1",
            "!",
            " ",
            None,
            12,
        ]
        for guess in invalid_guesses:
            with self.subTest(guess=guess):
                game = HangmanGame("python")
                with self.assertRaises(InvalidGuessError):
                    game.guess(guess)
                # Verify state was not modified
                self.assertEqual(game.guessed_letters, [])
                self.assertEqual(game.remaining_guesses, 6)


class TestDuplicateGuesses(unittest.TestCase):
    """Tests for handling repeated guesses."""

    def test_duplicate_correct_guess_rejected(self):
        game = HangmanGame("apple")
        game.guess("a")
        self.assertEqual(game.guessed_letters, ["a"])

        with self.assertRaises(DuplicateGuessError):
            game.guess("a")

        with self.assertRaises(DuplicateGuessError):
            game.guess("A")  # Case insensitive duplicate

        # State remains unchanged
        self.assertEqual(game.guessed_letters, ["a"])
        self.assertEqual(game.remaining_guesses, 6)

    def test_duplicate_incorrect_guess_rejected_without_penalty(self):
        game = HangmanGame("apple")
        game.guess("z")
        self.assertEqual(game.remaining_guesses, 5)
        self.assertEqual(game.incorrect_letters, ["z"])

        with self.assertRaises(DuplicateGuessError):
            game.guess("z")

        # Must not penalize again for duplicate
        self.assertEqual(game.remaining_guesses, 5)
        self.assertEqual(game.incorrect_letters, ["z"])


class TestGameRulesAndOutcomes(unittest.TestCase):
    """Tests for correct and incorrect moves, winning, and losing."""

    def test_multiple_occurrences_revealed(self):
        game = HangmanGame("banana")
        state = game.guess("a")
        self.assertEqual(state["pattern"], "_ a _ a _ a")
        self.assertEqual(game.remaining_guesses, 6)
        self.assertEqual(game.incorrect_letters, [])
        self.assertEqual(game.status, "playing")

    def test_incorrect_guess_reduces_remaining_guesses(self):
        game = HangmanGame("tree")
        state = game.guess("z")
        self.assertEqual(state["pattern"], "_ _ _ _")
        self.assertEqual(state["remaining_guesses"], 5)
        self.assertEqual(state["incorrect_letters"], ["z"])
        self.assertEqual(state["guessed_letters"], ["z"])
        self.assertEqual(state["status"], "playing")

    def test_win_condition(self):
        game = HangmanGame("cat")
        game.guess("c")
        game.guess("a")
        final_state = game.guess("t")

        self.assertTrue(game.is_won)
        self.assertFalse(game.is_lost)
        self.assertTrue(game.is_game_over)
        self.assertEqual(game.status, "won")
        self.assertEqual(final_state["status"], "won")
        self.assertEqual(final_state["pattern"], "c a t")
        self.assertEqual(final_state["word"], "cat")

    def test_loss_condition(self):
        game = HangmanGame("cat", max_incorrect_guesses=3)
        game.guess("x")
        game.guess("y")
        final_state = game.guess("z")

        self.assertTrue(game.is_lost)
        self.assertFalse(game.is_won)
        self.assertTrue(game.is_game_over)
        self.assertEqual(game.status, "lost")
        self.assertEqual(game.remaining_guesses, 0)
        self.assertEqual(final_state["status"], "lost")
        self.assertEqual(final_state["remaining_guesses"], 0)
        self.assertEqual(final_state["word"], "cat")

    def test_guess_after_game_over_raises_error(self):
        game = HangmanGame("ox", max_incorrect_guesses=1)
        game.guess("z")  # Lost
        self.assertTrue(game.is_game_over)

        with self.assertRaises(GameOverError):
            game.guess("o")


class TestAnswerDisclosureSecurity(unittest.TestCase):
    """Verify that the secret word is never exposed prematurely."""

    def test_word_not_in_state_during_active_play(self):
        game = HangmanGame("secret", game_id="test_game")
        state = game.to_dict()
        self.assertNotIn("word", state)
        self.assertEqual(state["status"], "playing")
        self.assertEqual(state["game_id"], "test_game")

        state_after_guess = game.guess("e")
        self.assertNotIn("word", state_after_guess)
        self.assertNotIn("word", game.to_dict())

        state_after_wrong = game.guess("z")
        self.assertNotIn("word", state_after_wrong)
        self.assertNotIn("word", game.to_dict())

    def test_word_revealed_only_on_win_or_loss(self):
        # Won game reveals word
        game_win = HangmanGame("go")
        game_win.guess("g")
        state_win = game_win.guess("o")
        self.assertEqual(state_win["word"], "go")
        self.assertEqual(game_win.to_dict()["word"], "go")

        # Lost game reveals word
        game_loss = HangmanGame("go", max_incorrect_guesses=1)
        state_loss = game_loss.guess("x")
        self.assertEqual(state_loss["word"], "go")
        self.assertEqual(game_loss.to_dict()["word"], "go")


class TestStateSerialization(unittest.TestCase):
    """Test serializing to dict and deserializing via from_dict."""

    def test_roundtrip_active_game(self):
        game = HangmanGame("puzzle", game_id="abc")
        game.guess("p")
        game.guess("x")

        state = game.to_dict()
        restored = HangmanGame.from_dict(state, word="puzzle")

        self.assertEqual(restored.word, "puzzle")
        self.assertEqual(restored.game_id, "abc")
        self.assertEqual(restored.guessed_letters, ["p", "x"])
        self.assertEqual(restored.incorrect_letters, ["x"])
        self.assertEqual(restored.remaining_guesses, 5)
        self.assertEqual(restored.status, "playing")
        self.assertEqual(restored.get_pattern(), "p _ _ _ _ _")

    def test_roundtrip_completed_game(self):
        game = HangmanGame("dog", game_id="xyz")
        game.guess("d")
        game.guess("o")
        game.guess("g")

        state = game.to_dict()
        # Word is already present in serialized dict for completed games
        restored = HangmanGame.from_dict(state)
        self.assertEqual(restored.word, "dog")
        self.assertEqual(restored.status, "won")
        self.assertTrue(restored.is_game_over)


if __name__ == "__main__":
    unittest.main()

