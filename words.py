"""Word Management Module for Hangman.

Handles loading, validating, deduplicating, and randomly selecting words
by difficulty level (easy, medium, hard).
"""

import os
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Sequence, Union


class WordManagerError(Exception):
    """Base exception for word management errors."""
    pass


class InvalidDifficultyError(WordManagerError, ValueError):
    """Raised when an invalid difficulty level is requested."""
    pass


class WordListError(WordManagerError, ValueError):
    """Raised when a word file is missing, empty, or contains invalid characters."""
    pass


class WordManager:
    """Manages word lists and random selection across difficulties."""

    VALID_DIFFICULTIES: Sequence[str] = ("easy", "medium", "hard")

    def __init__(
        self,
        words_dir: Optional[Union[str, Path]] = None,
        preload: bool = True,
        rng: Optional[random.Random] = None,
    ) -> None:
        """Initialize WordManager.

        Args:
            words_dir: Directory containing easy.txt, medium.txt, and hard.txt.
                       Defaults to the 'words' directory in the project root.
            preload: If True, loads and validates all word lists immediately.
            rng: Optional random.Random instance for deterministic testing.
        """
        if words_dir is None:
            self.words_dir = Path(__file__).resolve().parent / "words"
        else:
            self.words_dir = Path(words_dir)

        self._rng = rng or random.Random()
        self._cache: Dict[str, List[str]] = {}

        if preload:
            self.load_all()

    def normalize_difficulty(self, difficulty: Any) -> str:
        """Normalize and validate a difficulty string.

        Args:
            difficulty: Difficulty identifier (e.g., 'easy', 'Medium', ' HARD ').

        Returns:
            Normalized lowercase string ('easy', 'medium', or 'hard').

        Raises:
            InvalidDifficultyError: If difficulty is not recognized or not a string.
        """
        if not isinstance(difficulty, str):
            raise InvalidDifficultyError(
                f"Difficulty must be a string, got {type(difficulty).__name__}."
            )

        normalized = difficulty.strip().lower()
        if normalized not in self.VALID_DIFFICULTIES:
            raise InvalidDifficultyError(
                f"Invalid difficulty '{difficulty}'. Allowed values: {list(self.VALID_DIFFICULTIES)}."
            )

        return normalized

    def load_words(self, difficulty: str) -> List[str]:
        """Load, validate, and deduplicate words for a specific difficulty.

        Args:
            difficulty: 'easy', 'medium', or 'hard'.

        Returns:
            List of unique, valid lowercase words.

        Raises:
            InvalidDifficultyError: If difficulty is invalid.
            WordListError: If the file does not exist, is empty, or contains non-alphabetic words.
        """
        diff = self.normalize_difficulty(difficulty)

        file_path = self.words_dir / f"{diff}.txt"
        if not file_path.is_file():
            raise WordListError(f"Word file not found for difficulty '{diff}': {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as e:
            raise WordListError(f"Error reading word file {file_path}: {e}") from e

        seen = set()
        words: List[str] = []

        for line_num, line in enumerate(lines, start=1):
            cleaned = line.strip().lower()
            if not cleaned:
                continue  # skip blank lines

            if not cleaned.isalpha():
                raise WordListError(
                    f"Invalid word '{cleaned}' at line {line_num} in {file_path.name}: "
                    "words must contain alphabetic characters only."
                )

            if cleaned not in seen:
                seen.add(cleaned)
                words.append(cleaned)

        if not words:
            raise WordListError(f"Word file for difficulty '{diff}' contains no valid words.")

        self._cache[diff] = words
        return words

    def load_all(self) -> None:
        """Load and validate all standard difficulty word lists."""
        for diff in self.VALID_DIFFICULTIES:
            self.load_words(diff)

    def get_words(self, difficulty: str) -> List[str]:
        """Get the cached list of words for a given difficulty.

        Args:
            difficulty: 'easy', 'medium', or 'hard'.

        Returns:
            List of words for that difficulty.
        """
        diff = self.normalize_difficulty(difficulty)
        if diff not in self._cache:
            return self.load_words(diff)
        return list(self._cache[diff])

    def get_random_word(self, difficulty: str) -> str:
        """Select a random word from the specified difficulty.

        Args:
            difficulty: 'easy', 'medium', or 'hard'.

        Returns:
            A randomly selected word.
        """
        words = self.get_words(difficulty)
        return self._rng.choice(words)

    def reload(self) -> None:
        """Clear cache and reload word files."""
        self._cache.clear()
        self.load_all()


# Global default instance for convenience
_default_manager: Optional[WordManager] = None


def get_default_manager() -> WordManager:
    """Retrieve or initialize the default global WordManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = WordManager()
    return _default_manager


def get_random_word(difficulty: str) -> str:
    """Convenience function to get a random word using the default WordManager."""
    return get_default_manager().get_random_word(difficulty)


def get_words(difficulty: str) -> List[str]:
    """Convenience function to get cached words for a difficulty."""
    return get_default_manager().get_words(difficulty)


def load_words(difficulty: str, words_dir: Optional[Union[str, Path]] = None) -> List[str]:
    """Convenience function to load word list for a difficulty."""
    if words_dir is not None:
        manager = WordManager(words_dir=words_dir, preload=False)
        return manager.load_words(difficulty)
    return get_default_manager().get_words(difficulty)
