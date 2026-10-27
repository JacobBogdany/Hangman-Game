"""Integration tests for the Browser Client (Phase 4).

Verifies that Flask serves static frontend assets (HTML, CSS, JS)
and that required UI elements and API bindings are properly configured.
Compatible with both standard library unittest and pytest.
"""

import os
from pathlib import Path
import unittest

from server import create_app


class TestBrowserClientStaticAssets(unittest.TestCase):
    """Test suite for browser client frontend assets."""

    def setUp(self):
        self.app = create_app(test_config={"TESTING": True})
        self.client = self.app.test_client()
        self.static_dir = Path(__file__).resolve().parent.parent / "static"

    def test_root_serves_index_html(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)
        html = response.get_data(as_text=True)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<title>Hangman Game</title>", html)

    def test_style_css_served(self):
        response = self.client.get("/style.css")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/css", response.content_type)
        css = response.get_data(as_text=True)
        self.assertIn(".hangman-canvas", css)
        self.assertIn("@media", css)

    def test_app_js_served(self):
        response = self.client.get("/app.js")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            "javascript" in response.content_type,
            f"Expected javascript in content-type, got {response.content_type}",
        )
        js = response.get_data(as_text=True)
        self.assertIn("/api/games", js)
        self.assertIn("fetch", js)

    def test_index_html_contains_required_elements(self):
        html_path = self.static_dir / "index.html"
        self.assertTrue(html_path.is_file(), "index.html missing from static/")
        content = html_path.read_text(encoding="utf-8")

        # Required components
        required_selectors = [
            'id="difficulty-select"',
            'id="new-game-btn"',
            'id="hangman-svg"',
            'id="word-pattern"',
            'id="remaining-guesses"',
            'id="incorrect-letters"',
            'id="game-message"',
            'id="keyboard"',
        ]
        for selector in required_selectors:
            with self.subTest(selector=selector):
                self.assertIn(selector, content, f"Selector {selector} missing from index.html")

        # Difficulty levels present
        for diff in ("easy", "medium", "hard"):
            with self.subTest(difficulty=diff):
                self.assertIn(f'value="{diff}"', content)

        # 6 body parts in Hangman graphic
        body_parts = [
            "part-head",
            "part-torso",
            "part-arm-left",
            "part-arm-right",
            "part-leg-left",
            "part-leg-right",
        ]
        for part in body_parts:
            with self.subTest(body_part=part):
                self.assertIn(f'id="{part}"', content)

    def test_style_css_responsiveness_and_classes(self):
        css_path = self.static_dir / "style.css"
        self.assertTrue(css_path.is_file(), "style.css missing from static/")
        content = css_path.read_text(encoding="utf-8")

        expected_rules = [
            "@media",
            ".key-correct",
            ".key-incorrect",
            ".part-hidden",
            ".part-visible",
            ".pattern",
        ]
        for rule in expected_rules:
            with self.subTest(rule=rule):
                self.assertIn(rule, content, f"CSS rule/class {rule} missing from style.css")

    def test_app_js_api_communication_and_security(self):
        js_path = self.static_dir / "app.js"
        self.assertTrue(js_path.is_file(), "app.js missing from static/")
        content = js_path.read_text(encoding="utf-8")

        # Communicates with API endpoints
        self.assertIn("/api/games", content)
        self.assertIn("/guess", content)
        self.assertIn("fetch", content)

        # Keyboard interaction
        self.assertIn("keydown", content)

        # Security: JavaScript does not store any hardcoded secret word list
        self.assertNotIn("easy.txt", content)
        self.assertNotIn("medium.txt", content)
        self.assertNotIn("hard.txt", content)


if __name__ == "__main__":
    unittest.main()
