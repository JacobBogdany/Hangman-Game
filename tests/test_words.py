"""Unit tests for the Word Management module (words.py).

Compatible with both standard library unittest and pytest.
"""

import os
from pathlib import Path
import random
import tempfile
import unittest

from words import (
    WordManager,
    InvalidDifficultyError,
    WordListError,
    get_random_word,
    get_words,
    load_words,
)


class TestWordLoading(unittest.TestCase):
    """Tests for loading and validating word lists."""

    def setUp(self):
        self.manager = WordManager()

    def test_load_standard_difficulties(self):
        for diff in ("easy", "medium", "hard"):
            words = self.manager.get_words(diff)
            self.assertIsInstance(words, list)
            self.assertGreater(len(words), 20)
            for word in words:
                self.assertTrue(word.isalpha(), f"Word '{word}' is not alphabetic.")
                self.assertEqual(word, word.lower(), f"Word '{word}' is not lowercase.")
                self.assertGreater(len(word), 0)

    def test_case_and_whitespace_insensitivity_in_difficulty(self):
        easy_standard = self.manager.get_words("easy")
        easy_variant1 = self.manager.get_words("  Easy  ")
        easy_variant2 = self.manager.get_words("EASY")
        self.assertEqual(easy_standard, easy_variant1)
        self.assertEqual(easy_standard, easy_variant2)

    def test_duplicates_removed_on_load(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # Create an easy.txt with duplicates and mixed case
            (tmp_path / "easy.txt").write_text("Apple\napple\nAPPLE\nbanana\nBanana\n", encoding="utf-8")
            (tmp_path / "medium.txt").write_text("orange\n", encoding="utf-8")
            (tmp_path / "hard.txt").write_text("strawberry\n", encoding="utf-8")

            manager = WordManager(words_dir=tmp_path)
            easy_words = manager.get_words("easy")
            self.assertEqual(easy_words, ["apple", "banana"])
            self.assertEqual(len(easy_words), 2)


class TestDifficultyValidation(unittest.TestCase):
    """Tests for rejecting invalid difficulty values."""

    def setUp(self):
        self.manager = WordManager()

    def test_invalid_difficulty_strings_raise_error(self):
        invalid_difficulties = ["extreme", "expert", "nightmare", "", "   ", "easy-peasy", "1"]
        for diff in invalid_difficulties:
            with self.subTest(difficulty=diff):
                with self.assertRaises(InvalidDifficultyError):
                    self.manager.get_words(diff)
                with self.assertRaises(InvalidDifficultyError):
                    self.manager.get_random_word(diff)

    def test_invalid_difficulty_types_raise_error(self):
        invalid_types = [None, 123, 4.5, ["easy"], {"difficulty": "easy"}]
        for diff in invalid_types:
            with self.subTest(difficulty=diff):
                with self.assertRaises(InvalidDifficultyError):
                    self.manager.normalize_difficulty(diff)  # type: ignore


class TestRandomWordSelection(unittest.TestCase):
    """Tests for selecting random words."""

    def test_random_word_in_correct_list(self):
        for diff in ("easy", "medium", "hard"):
            word_list = set(get_words(diff))
            for _ in range(10):
                chosen = get_random_word(diff)
                self.assertIn(chosen, word_list)

    def test_deterministic_selection_with_seeded_rng(self):
        rng1 = random.Random(42)
        rng2 = random.Random(42)

        manager1 = WordManager(rng=rng1)
        manager2 = WordManager(rng=rng2)

        picks1 = [manager1.get_random_word("medium") for _ in range(5)]
        picks2 = [manager2.get_random_word("medium") for _ in range(5)]
        self.assertEqual(picks1, picks2)


class TestFileValidationAndErrorHandling(unittest.TestCase):
    """Tests for handling malformed or missing word files."""

    def test_missing_file_raises_word_list_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # Create only easy.txt, omitting medium and hard
            (tmp_path / "easy.txt").write_text("hello\n", encoding="utf-8")

            manager = WordManager(words_dir=tmp_path, preload=False)
            self.assertEqual(manager.get_words("easy"), ["hello"])

            with self.assertRaises(WordListError):
                manager.get_words("medium")

    def test_non_alphabetic_word_in_file_raises_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "easy.txt").write_text("valid\ninvalid123\nanother\n", encoding="utf-8")

            manager = WordManager(words_dir=tmp_path, preload=False)
            with self.assertRaises(WordListError) as ctx:
                manager.get_words("easy")
            self.assertIn("alphabetic", str(ctx.exception).lower())

    def test_empty_word_file_raises_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "easy.txt").write_text("\n   \n\n", encoding="utf-8")

            manager = WordManager(words_dir=tmp_path, preload=False)
            with self.assertRaises(WordListError) as ctx:
                manager.get_words("easy")
            self.assertIn("no valid words", str(ctx.exception).lower())

    def test_reload_clears_cache_and_updates(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            file_path = tmp_path / "easy.txt"
            file_path.write_text("initial\n", encoding="utf-8")
            (tmp_path / "medium.txt").write_text("mediumword\n", encoding="utf-8")
            (tmp_path / "hard.txt").write_text("hardword\n", encoding="utf-8")

            manager = WordManager(words_dir=tmp_path)
            self.assertEqual(manager.get_words("easy"), ["initial"])

            # Modify file on disk
            file_path.write_text("updated\nanother\n", encoding="utf-8")

            # Before reload, cache persists
            self.assertEqual(manager.get_words("easy"), ["initial"])

            # After reload, cache updates
            manager.reload()
            self.assertEqual(manager.get_words("easy"), ["updated", "another"])


if __name__ == "__main__":
    unittest.main()

