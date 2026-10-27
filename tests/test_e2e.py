"""End-to-End (E2E) automated test suite for Hangman.

Simulates complete user and browser workflows against the Hangman REST server:
- Full winning game lifecycle with systematic letter guessing
- Full losing game lifecycle with 6 incorrect moves
- Resilience against malformed inputs and duplicates during active gameplay
- Independent concurrent game sessions
- Multi-difficulty game initialization and validation
Compatible with both standard library unittest and pytest.
"""

import json
import unittest

from server import create_app
from words import get_words


class TestHangmanEndToEnd(unittest.TestCase):
    """Full lifecycle End-to-End integration tests."""

    def setUp(self):
        self.app = create_app(test_config={"TESTING": True})
        self.client = self.app.test_client()

    def test_e2e_full_winning_lifecycle(self):
        """Simulate an entire session where a player systematically wins a game."""
        # 1. Player requests a new Easy game
        res = self.client.post("/api/games", json={"difficulty": "easy"})
        self.assertEqual(res.status_code, 201)
        game_data = res.get_json()

        game_id = game_data["game_id"]
        self.assertIsNotNone(game_id)
        self.assertEqual(game_data["status"], "playing")
        self.assertEqual(game_data["remaining_guesses"], 6)
        self.assertNotIn("word", game_data)

        # Get server internal reference to know the target word for simulation
        target_word = self.app.games[game_id].word  # type: ignore[attr-defined]
        unique_letters = list(dict.fromkeys(target_word))

        # 2. Player guesses letters one by one
        for i, letter in enumerate(unique_letters):
            guess_res = self.client.post(
                f"/api/games/{game_id}/guess",
                json={"letter": letter},
            )
            self.assertEqual(guess_res.status_code, 200)
            state = guess_res.get_json()

            # Inspect state after each move
            if i < len(unique_letters) - 1:
                self.assertEqual(state["status"], "playing")
                self.assertNotIn("word", state)
                self.assertEqual(state["remaining_guesses"], 6)
                self.assertIn(letter, state["pattern"])
            else:
                # Last letter triggers win
                self.assertEqual(state["status"], "won")
                self.assertEqual(state["remaining_guesses"], 6)
                self.assertEqual(state["word"], target_word)
                # Every letter in pattern should now be revealed
                unspaced_pattern = state["pattern"].replace(" ", "")
                self.assertEqual(unspaced_pattern, target_word)

        # 3. Verify server state via GET /api/games/{id}
        get_res = self.client.get(f"/api/games/{game_id}")
        self.assertEqual(get_res.status_code, 200)
        final_state = get_res.get_json()
        self.assertEqual(final_state["status"], "won")
        self.assertEqual(final_state["word"], target_word)

        # 4. Attempting another guess after winning is rejected
        post_win_res = self.client.post(f"/api/games/{game_id}/guess", json={"letter": "z"})
        self.assertEqual(post_win_res.status_code, 400)
        self.assertIn("finished", post_win_res.get_json()["error"].lower())

    def test_e2e_full_losing_lifecycle(self):
        """Simulate an entire session where a player exhausts all 6 lives and loses."""
        # 1. Create a Hard game
        res = self.client.post("/api/games", json={"difficulty": "hard"})
        self.assertEqual(res.status_code, 201)
        game_data = res.get_json()
        game_id = game_data["game_id"]

        target_word = self.app.games[game_id].word  # type: ignore[attr-defined]

        # Find 6 letters not present in target word
        wrong_letters = [
            chr(c) for c in range(ord('a'), ord('z') + 1)
            if chr(c) not in target_word
        ][:6]
        self.assertEqual(len(wrong_letters), 6)

        # 2. Submit wrong letters one by one
        for attempt, letter in enumerate(wrong_letters, start=1):
            guess_res = self.client.post(
                f"/api/games/{game_id}/guess",
                json={"letter": letter},
            )
            self.assertEqual(guess_res.status_code, 200)
            state = guess_res.get_json()

            expected_remaining = 6 - attempt
            self.assertEqual(state["remaining_guesses"], expected_remaining)
            self.assertIn(letter, state["incorrect_letters"])

            if attempt < 6:
                self.assertEqual(state["status"], "playing")
                self.assertNotIn("word", state)
            else:
                # 6th incorrect guess triggers loss
                self.assertEqual(state["status"], "lost")
                self.assertEqual(state["remaining_guesses"], 0)
                self.assertEqual(state["word"], target_word)

        # 3. Verify GET state reflects loss and reveals secret word
        get_res = self.client.get(f"/api/games/{game_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.get_json()["status"], "lost")
        self.assertEqual(get_res.get_json()["word"], target_word)

        # 4. Further moves are rejected
        post_loss_res = self.client.post(f"/api/games/{game_id}/guess", json={"letter": "a"})
        self.assertEqual(post_loss_res.status_code, 400)

    def test_e2e_input_resilience_during_game(self):
        """Verify that bad inputs and duplicate moves never corrupt an ongoing game."""
        res = self.client.post("/api/games", json={"difficulty": "medium"})
        game_id = res.get_json()["game_id"]

        # Make one valid guess
        g1 = self.client.post(f"/api/games/{game_id}/guess", json={"letter": "e"})
        self.assertEqual(g1.status_code, 200)
        state_before = g1.get_json()

        # Try duplicate guess
        dup = self.client.post(f"/api/games/{game_id}/guess", json={"letter": "e"})
        self.assertEqual(dup.status_code, 400)

        # Try non-letter inputs
        bad_inputs = [
            {"letter": "12"},
            {"letter": "!"},
            {"letter": " "},
            {"letter": ""},
            {"wrong_key": "a"},
            "not a json object",
        ]
        for bad in bad_inputs:
            with self.subTest(bad_input=bad):
                if isinstance(bad, dict):
                    err_res = self.client.post(f"/api/games/{game_id}/guess", json=bad)
                else:
                    err_res = self.client.post(
                        f"/api/games/{game_id}/guess",
                        data=bad,
                        content_type="text/plain",
                    )
                self.assertEqual(err_res.status_code, 400)

        # Verify state was untouched despite all bad requests
        check = self.client.get(f"/api/games/{game_id}")
        self.assertEqual(check.status_code, 200)
        state_after = check.get_json()
        self.assertEqual(state_before["remaining_guesses"], state_after["remaining_guesses"])
        self.assertEqual(state_before["guessed_letters"], state_after["guessed_letters"])
        self.assertEqual(state_before["incorrect_letters"], state_after["incorrect_letters"])

    def test_e2e_multiple_concurrent_games(self):
        """Verify multiple simultaneous games run independently without cross-talk."""
        res_a = self.client.post("/api/games", json={"difficulty": "easy"})
        res_b = self.client.post("/api/games", json={"difficulty": "hard"})

        id_a = res_a.get_json()["game_id"]
        id_b = res_b.get_json()["game_id"]
        self.assertNotEqual(id_a, id_b)

        # Play moves on game A
        self.client.post(f"/api/games/{id_a}/guess", json={"letter": "a"})
        self.client.post(f"/api/games/{id_a}/guess", json={"letter": "e"})

        # Verify game B was completely untouched
        state_b = self.client.get(f"/api/games/{id_b}").get_json()
        self.assertEqual(state_b["guessed_letters"], [])
        self.assertEqual(state_b["incorrect_letters"], [])
        self.assertEqual(state_b["remaining_guesses"], 6)

        # Play moves on game B
        self.client.post(f"/api/games/{id_b}/guess", json={"letter": "z"})
        state_b_updated = self.client.get(f"/api/games/{id_b}").get_json()
        self.assertEqual(state_b_updated["guessed_letters"], ["z"])

        # Verify game A was not affected by game B's move
        state_a = self.client.get(f"/api/games/{id_a}").get_json()
        self.assertEqual(state_a["guessed_letters"], ["a", "e"])

    def test_e2e_difficulty_selection(self):
        """Verify games generated with different difficulties use appropriate word pools."""
        easy_pool = set(get_words("easy"))
        hard_pool = set(get_words("hard"))

        res_easy = self.client.post("/api/games", json={"difficulty": "easy"})
        id_easy = res_easy.get_json()["game_id"]
        word_easy = self.app.games[id_easy].word  # type: ignore[attr-defined]
        self.assertIn(word_easy, easy_pool)

        res_hard = self.client.post("/api/games", json={"difficulty": "hard"})
        id_hard = res_hard.get_json()["game_id"]
        word_hard = self.app.games[id_hard].word  # type: ignore[attr-defined]
        self.assertIn(word_hard, hard_pool)


if __name__ == "__main__":
    unittest.main()

