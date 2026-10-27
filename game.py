"""Core Game Engine for Hangman.

This module is completely independent from Flask, HTTP servers, and user interfaces.
All game logic, input validation, win/loss determination, and state tracking
are encapsulated within the HangmanGame class.
"""

from typing import Any, Dict, List, Optional


class HangmanError(Exception):
    """Base exception for Hangman game errors."""
    pass


class InvalidGuessError(HangmanError, ValueError):
    """Raised when a guess is invalid (not a single alphabetic character)."""
    pass


class DuplicateGuessError(HangmanError, ValueError):
    """Raised when a letter has already been guessed in the current game."""
    pass


class GameOverError(HangmanError, ValueError):
    """Raised when an action is attempted on a game that has already concluded."""
    pass


class HangmanGame:
    """Encapsulates the state and rules for a single Hangman game."""

    DEFAULT_MAX_INCORRECT_GUESSES = 6

    def __init__(
        self,
        word: str,
        max_incorrect_guesses: int = DEFAULT_MAX_INCORRECT_GUESSES,
        game_id: Optional[str] = None,
    ) -> None:
        """Initialize a new Hangman game.

        Args:
            word: The hidden word to be guessed.
            max_incorrect_guesses: Number of allowed incorrect guesses (default: 6).
            game_id: Optional unique identifier for the game session.

        Raises:
            ValueError: If the word is empty, not a string, or contains non-alphabetic characters.
            ValueError: If max_incorrect_guesses is less than 1.
        """
        if not isinstance(word, str):
            raise ValueError("Word must be a string.")

        cleaned_word = word.strip().lower()
        if not cleaned_word:
            raise ValueError("Word must not be empty.")

        if not cleaned_word.isalpha():
            raise ValueError("Word must contain alphabetic characters only.")

        if not isinstance(max_incorrect_guesses, int) or max_incorrect_guesses < 1:
            raise ValueError("max_incorrect_guesses must be a positive integer.")

        self._word: str = cleaned_word
        self.max_incorrect_guesses: int = max_incorrect_guesses
        self.game_id: Optional[str] = game_id

        self.guessed_letters: List[str] = []
        self.incorrect_letters: List[str] = []
        self.status: str = "playing"  # "playing", "won", or "lost"

    @property
    def word(self) -> str:
        """Internal access to the hidden word."""
        return self._word

    @property
    def remaining_guesses(self) -> int:
        """Number of incorrect guesses remaining before the game is lost."""
        return max(0, self.max_incorrect_guesses - len(self.incorrect_letters))

    @property
    def is_won(self) -> bool:
        """Return True if the game has been won."""
        return self.status == "won"

    @property
    def is_lost(self) -> bool:
        """Return True if the game has been lost."""
        return self.status == "lost"

    @property
    def is_game_over(self) -> bool:
        """Return True if the game has ended (either won or lost)."""
        return self.status in ("won", "lost")

    def get_pattern(self) -> str:
        """Generate the masked representation of the word.

        Returns:
            A space-separated string where unguessed letters are represented by '_'
            and guessed letters are displayed (e.g., '_ e _ _ e').
        """
        guessed_set = set(self.guessed_letters)
        return " ".join(letter if letter in guessed_set else "_" for letter in self._word)

    def validate_guess(self, letter: Any) -> str:
        """Validate that a guess is a single alphabetic letter.

        Args:
            letter: The guessed character.

        Returns:
            The normalized lowercase single-letter string.

        Raises:
            InvalidGuessError: If the input is not a single alphabetic character.
        """
        if not isinstance(letter, str):
            raise InvalidGuessError("Guess must be a string.")

        cleaned = letter.strip().lower()
        if len(cleaned) != 1 or not cleaned.isalpha():
            raise InvalidGuessError("Guess must be a single alphabetic letter (a-z).")

        return cleaned

    def guess(self, letter: Any) -> Dict[str, Any]:
        """Process a letter guess.

        Args:
            letter: The character being guessed.

        Returns:
            The updated client-safe game-state dictionary.

        Raises:
            GameOverError: If the game has already finished.
            InvalidGuessError: If the input is not a valid single letter.
            DuplicateGuessError: If the letter has already been guessed.
        """
        if self.is_game_over:
            raise GameOverError(f"Cannot guess on a finished game. Current status: '{self.status}'.")

        normalized = self.validate_guess(letter)

        if normalized in self.guessed_letters:
            raise DuplicateGuessError(f"Letter '{normalized}' has already been guessed.")

        self.guessed_letters.append(normalized)

        if normalized in self._word:
            # Check win condition: all unique letters in hidden word have been guessed
            if all(char in self.guessed_letters for char in self._word):
                self.status = "won"
        else:
            self.incorrect_letters.append(normalized)
            # Check loss condition: maximum incorrect guesses reached
            if len(self.incorrect_letters) >= self.max_incorrect_guesses:
                self.status = "lost"

        return self.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        """Return a client-safe dictionary representation of the game state.

        CRITICAL SECURITY RULE:
        The hidden word is NEVER included in this dictionary while the game is
        active (status is 'playing'). It is only revealed after the game concludes
        ('won' or 'lost').
        """
        state: Dict[str, Any] = {
            "pattern": self.get_pattern(),
            "guessed_letters": list(self.guessed_letters),
            "incorrect_letters": list(self.incorrect_letters),
            "remaining_guesses": self.remaining_guesses,
            "status": self.status,
        }

        if self.game_id is not None:
            state["game_id"] = self.game_id

        # Only reveal the secret word once the game has ended
        if self.is_game_over:
            state["word"] = self._word

        return state

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        word: Optional[str] = None,
        max_incorrect_guesses: int = DEFAULT_MAX_INCORRECT_GUESSES,
    ) -> "HangmanGame":
        """Reconstruct a HangmanGame instance from serialized state.

        Args:
            data: State dictionary (as produced by to_dict).
            word: The hidden word (required if not present in data).
            max_incorrect_guesses: Number of allowed incorrect guesses.

        Returns:
            A restored HangmanGame instance.
        """
        secret = data.get("word") or word
        if not secret:
            raise ValueError("Hidden word must be provided to reconstruct game state.")

        game = cls(
            word=secret,
            max_incorrect_guesses=data.get("max_incorrect_guesses", max_incorrect_guesses),
            game_id=data.get("game_id"),
        )
        game.guessed_letters = list(data.get("guessed_letters", []))
        game.incorrect_letters = list(data.get("incorrect_letters", []))
        game.status = data.get("status", "playing")
        return game

