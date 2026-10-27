"""Integration and API tests for the Hangman REST Server (server.py).

Compatible with both standard library unittest and pytest.
"""

import json
import unittest

from server import create_app
from words import WordManager


class TestServerAPI(unittest.TestCase):
    """Test suite for the REST API endpoints."""

    def setUp(self):
        # Create an app instance with testing config
        self.app = create_app(test_config={"TESTING": True})
        self.client = self.app.test_client()

    def test_index_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_404_handler_returns_json(self):
        response = self.client.get("/api/nonexistent_endpoint")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn("error", data)

    def test_405_handler_returns_json(self):
        # PUT method is not allowed on /api/games
        response = self.client.put("/api/games", json={})
        self.assertEqual(response.status_code, 405)
        data = response.get_json()
        self.assertIn("error", data)

    def test_create_game_default_difficulty(self):
        response = self.client.post("/api/games", json={})
        self.assertEqual(response.status_code, 201)
        data = response.get_json()

        self.assertIn("game_id", data)
        self.assertIn("pattern", data)
        self.assertEqual(data["remaining_guesses"], 6)
        self.assertEqual(data["status"], "playing")
        self.assertEqual(data["guessed_letters"], [])
        self.assertEqual(data["incorrect_letters"], [])
        # Word must NOT be disclosed during active play
        self.assertNotIn("word", data)

    def test_create_game_with_specific_difficulties(self):
        for diff in ("easy", "medium", "hard"):
            with self.subTest(difficulty=diff):
                response = self.client.post(
                    "/api/games",
                    data=json.dumps({"difficulty": diff}),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 201)
                data = response.get_json()
                self.assertIn("game_id", data)
                self.assertEqual(data["status"], "playing")

    def test_create_game_invalid_difficulty(self):
        response = self.client.post("/api/games", json={"difficulty": "super_extreme"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn("allowed_difficulties", data)

    def test_create_game_malformed_json_or_headers(self):
        # Non-JSON content type with body
        response = self.client.post("/api/games", data="invalid plain text", content_type="text/plain")
        self.assertEqual(response.status_code, 400)

        # JSON array instead of object
        response2 = self.client.post("/api/games", data="[1, 2, 3]", content_type="application/json")
        self.assertEqual(response2.status_code, 400)

    def test_get_game_state(self):
        # First create a game
        create_res = self.client.post("/api/games", json={"difficulty": "easy"})
        game_id = create_res.get_json()["game_id"]

        # Fetch state
        get_res = self.client.get(f"/api/games/{game_id}")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.get_json()

        self.assertEqual(data["game_id"], game_id)
        self.assertEqual(data["status"], "playing")
        self.assertNotIn("word", data)

    def test_get_nonexistent_game_returns_404(self):
        response = self.client.get("/api/games/non_existent_id")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn("error", data)

    def test_guess_letter_success(self):
        create_res = self.client.post("/api/games", json={"difficulty": "easy"})
        game_id = create_res.get_json()["game_id"]
        game_obj = self.app.games[game_id]  # type: ignore[attr-defined]
        secret = game_obj.word

        # Guess a letter known to be in the secret word
        correct_letter = secret[0]
        guess_res = self.client.post(
            f"/api/games/{game_id}/guess",
            json={"letter": correct_letter.upper()},  # test case insensitivity
        )
        self.assertEqual(guess_res.status_code, 200)
        data = guess_res.get_json()

        self.assertIn(correct_letter, data["guessed_letters"])
        self.assertEqual(data["remaining_guesses"], 6)
        self.assertEqual(data["incorrect_letters"], [])
        self.assertIn(correct_letter, data["pattern"])

    def test_guess_incorrect_letter(self):
        create_res = self.client.post("/api/games", json={"difficulty": "easy"})
        game_id = create_res.get_json()["game_id"]
        game_obj = self.app.games[game_id]  # type: ignore[attr-defined]
        secret = game_obj.word

        # Pick a letter that is NOT in the secret word
        wrong_letter = next(chr(c) for c in range(ord('a'), ord('z') + 1) if chr(c) not in secret)

        guess_res = self.client.post(
            f"/api/games/{game_id}/guess",
            json={"letter": wrong_letter},
        )
        self.assertEqual(guess_res.status_code, 200)
        data = guess_res.get_json()

        self.assertIn(wrong_letter, data["guessed_letters"])
        self.assertIn(wrong_letter, data["incorrect_letters"])
        self.assertEqual(data["remaining_guesses"], 5)
        self.assertEqual(data["status"], "playing")

    def test_guess_duplicate_letter_returns_400(self):
        create_res = self.client.post("/api/games", json={"difficulty": "easy"})
        game_id = create_res.get_json()["game_id"]

        self.client.post(f"/api/games/{game_id}/guess", json={"letter": "e"})
        dup_res = self.client.post(f"/api/games/{game_id}/guess", json={"letter": "E"})

        self.assertEqual(dup_res.status_code, 400)
        data = dup_res.get_json()
        self.assertIn("error", data)
        self.assertIn("already been guessed", data["error"].lower())

    def test_guess_invalid_input_returns_400(self):
        create_res = self.client.post("/api/games", json={"difficulty": "easy"})
        game_id = create_res.get_json()["game_id"]

        invalid_payloads = [
            {},                     # missing letter key
            {"letter": ""},         # empty
            {"letter": "ab"},       # multiple letters
            {"letter": "1"},        # digit
            {"letter": "!"},        # punctuation
            {"letter": None},       # None
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                res = self.client.post(f"/api/games/{game_id}/guess", json=payload)
                self.assertEqual(res.status_code, 400)
                data = res.get_json()
                self.assertIn("error", data)

    def test_guess_on_nonexistent_game_returns_404(self):
        res = self.client.post("/api/games/unknown_id/guess", json={"letter": "a"})
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertIn("error", data)

    def test_full_win_playthrough_and_disclosure(self):
        create_res = self.client.post("/api/games", json={"difficulty": "easy"})
        game_id = create_res.get_json()["game_id"]
        game_obj = self.app.games[game_id]  # type: ignore[attr-defined]
        secret = game_obj.word

        # Guess every unique letter in secret
        unique_letters = list(dict.fromkeys(secret))
        for letter in unique_letters[:-1]:
            res = self.client.post(f"/api/games/{game_id}/guess", json={"letter": letter})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["status"], "playing")
            self.assertNotIn("word", data)

        # Final winning guess
        winning_res = self.client.post(
            f"/api/games/{game_id}/guess",
            json={"letter": unique_letters[-1]},
        )
        self.assertEqual(winning_res.status_code, 200)
        win_data = winning_res.get_json()
        self.assertEqual(win_data["status"], "won")
        self.assertEqual(win_data["word"], secret)

        # Further guesses on completed game are rejected
        post_win_res = self.client.post(f"/api/games/{game_id}/guess", json={"letter": "z"})
        self.assertEqual(post_win_res.status_code, 400)
        self.assertIn("finished", post_win_res.get_json()["error"].lower())

    def test_full_loss_playthrough_and_disclosure(self):
        create_res = self.client.post("/api/games", json={"difficulty": "easy"})
        game_id = create_res.get_json()["game_id"]
        game_obj = self.app.games[game_id]  # type: ignore[attr-defined]
        secret = game_obj.word

        # Pick 6 letters guaranteed not in secret
        wrong_candidates = [
            chr(c) for c in range(ord('a'), ord('z') + 1)
            if chr(c) not in secret
        ]

        for i in range(5):
            res = self.client.post(f"/api/games/{game_id}/guess", json={"letter": wrong_candidates[i]})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["status"], "playing")
            self.assertEqual(data["remaining_guesses"], 6 - (i + 1))
            self.assertNotIn("word", data)

        # 6th and final wrong guess
        final_res = self.client.post(
            f"/api/games/{game_id}/guess",
            json={"letter": wrong_candidates[5]},
        )
        self.assertEqual(final_res.status_code, 200)
        loss_data = final_res.get_json()
        self.assertEqual(loss_data["status"], "lost")
        self.assertEqual(loss_data["remaining_guesses"], 0)
        self.assertEqual(loss_data["word"], secret)

        # Post-loss guess rejected
        post_loss_res = self.client.post(f"/api/games/{game_id}/guess", json={"letter": "a"})
        self.assertEqual(post_loss_res.status_code, 400)
        self.assertIn("finished", post_loss_res.get_json()["error"].lower())


if __name__ == "__main__":
    unittest.main()

