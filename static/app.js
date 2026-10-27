/**
 * Hangman Client Application
 * Communicates exclusively via REST API endpoints (/api/games).
 * The hidden word is NEVER stored or known client-side until game completion.
 */

(() => {
  "use strict";

  // Body part element IDs corresponding to 1..6 incorrect guesses
  const BODY_PARTS = [
    "part-head",       // 1
    "part-torso",      // 2
    "part-arm-left",   // 3
    "part-arm-right",  // 4
    "part-leg-left",   // 5
    "part-leg-right",  // 6
  ];

  const ALPHABET = "abcdefghijklmnopqrstuvwxyz".split("");

  // DOM Elements
  const difficultySelect = document.getElementById("difficulty-select");
  const newGameBtn = document.getElementById("new-game-btn");
  const wordPatternEl = document.getElementById("word-pattern");
  const remainingGuessesEl = document.getElementById("remaining-guesses");
  const incorrectLettersEl = document.getElementById("incorrect-letters");
  const gameMessageEl = document.getElementById("game-message");
  const keyboardContainer = document.getElementById("keyboard");

  // Application State
  let currentGameId = null;
  let gameStatus = "idle"; // "idle", "playing", "won", "lost"
  let guessedLetters = new Set();
  let incorrectLetters = [];

  /**
   * Initialize on-screen alphabet keyboard
   */
  function initKeyboard() {
    keyboardContainer.innerHTML = "";
    ALPHABET.forEach((letter) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "key-btn";
      button.textContent = letter;
      button.id = `key-${letter}`;
      button.setAttribute("aria-label", `Guess letter ${letter.toUpperCase()}`);
      button.disabled = true; // disabled until game starts

      button.addEventListener("click", () => {
        handleGuess(letter);
      });

      keyboardContainer.appendChild(button);
    });
  }

  /**
   * Update visual Hangman figure based on incorrect guess count
   */
  function updateHangmanGraphic(incorrectCount) {
    BODY_PARTS.forEach((partId, index) => {
      const el = document.getElementById(partId);
      if (!el) return;
      if (index < incorrectCount) {
        el.classList.remove("part-hidden");
        el.classList.add("part-visible");
      } else {
        el.classList.remove("part-visible");
        el.classList.add("part-hidden");
      }
    });
  }

  /**
   * Reset the game board and UI elements
   */
  function resetBoard() {
    guessedLetters.clear();
    incorrectLetters = [];
    updateHangmanGraphic(0);
    remainingGuessesEl.textContent = "6";
    incorrectLettersEl.textContent = "-";

    // Enable all keyboard buttons
    ALPHABET.forEach((letter) => {
      const keyBtn = document.getElementById(`key-${letter}`);
      if (keyBtn) {
        keyBtn.disabled = false;
        keyBtn.className = "key-btn";
      }
    });
  }

  /**
   * Display a status or outcome message
   */
  function setMessage(text, type = "playing") {
    gameMessageEl.textContent = text;
    gameMessageEl.className = `game-message message-${type}`;
  }

  /**
   * Start a new game session via REST API
   */
  async function startNewGame() {
    const difficulty = difficultySelect.value;
    setMessage("Starting new game...", "idle");
    newGameBtn.disabled = true;

    try {
      const response = await fetch("/api/games", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ difficulty }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Server responded with ${response.status}`);
      }

      const data = await response.json();

      currentGameId = data.game_id;
      gameStatus = data.status || "playing";

      resetBoard();
      renderGameState(data);
      setMessage("Game in progress. Guess a letter!", "playing");
    } catch (err) {
      console.error("Failed to start new game:", err);
      setMessage(`Error starting game: ${err.message}`, "lost");
    } finally {
      newGameBtn.disabled = false;
    }
  }

  /**
   * Submit a letter guess to the REST API
   */
  async function handleGuess(letter) {
    if (gameStatus !== "playing" || !currentGameId) {
      return;
    }

    const normLetter = letter.toLowerCase();
    if (guessedLetters.has(normLetter)) {
      return; // Already guessed
    }

    // Optimistically disable the button to prevent duplicate clicks
    const keyBtn = document.getElementById(`key-${normLetter}`);
    if (keyBtn) {
      keyBtn.disabled = true;
    }

    try {
      const response = await fetch(`/api/games/${currentGameId}/guess`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ letter: normLetter }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || `Guess failed with status ${response.status}`);
      }

      const data = await response.json();
      renderGameState(data);
    } catch (err) {
      console.error("Guess error:", err);
      setMessage(err.message, "lost");
    }
  }

  /**
   * Render updated game state into DOM
   */
  function renderGameState(data) {
    // 1. Update pattern
    if (data.pattern) {
      wordPatternEl.textContent = data.pattern;
    }

    // 2. Update remaining lives
    if (data.remaining_guesses !== undefined) {
      remainingGuessesEl.textContent = data.remaining_guesses;
    }

    // 3. Update guessed and incorrect letters
    if (data.guessed_letters) {
      data.guessed_letters.forEach((l) => guessedLetters.add(l));
    }
    if (data.incorrect_letters) {
      incorrectLetters = data.incorrect_letters;
      incorrectLettersEl.textContent = incorrectLetters.length > 0
        ? incorrectLetters.join(", ").toUpperCase()
        : "-";
      updateHangmanGraphic(incorrectLetters.length);
    }

    // 4. Update keyboard button classes
    ALPHABET.forEach((letter) => {
      const btn = document.getElementById(`key-${letter}`);
      if (!btn) return;

      if (guessedLetters.has(letter)) {
        btn.disabled = true;
        if (incorrectLetters.includes(letter)) {
          btn.classList.add("key-incorrect");
        } else {
          btn.classList.add("key-correct");
        }
      }
    });

    // 5. Handle win/loss termination
    gameStatus = data.status;
    if (data.status === "won") {
      setMessage(`🎉 Congratulations! You won! The word was "${data.word}".`, "won");
      disableAllKeys();
    } else if (data.status === "lost") {
      setMessage(`💀 Game Over! You lost. The word was "${data.word}".`, "lost");
      disableAllKeys();
    }
  }

  /**
   * Disable all keyboard buttons when game terminates
   */
  function disableAllKeys() {
    ALPHABET.forEach((letter) => {
      const btn = document.getElementById(`key-${letter}`);
      if (btn) btn.disabled = true;
    });
  }

  /**
   * Physical Keyboard listener
   */
  function handlePhysicalKeyDown(e) {
    if (gameStatus !== "playing") return;
    // Ignore key combinations with Ctrl, Alt, Meta
    if (e.ctrlKey || e.altKey || e.metaKey) return;

    const key = e.key.toLowerCase();
    if (/^[a-z]$/.test(key)) {
      handleGuess(key);
    }
  }

  // Event Listeners
  newGameBtn.addEventListener("click", startNewGame);
  window.addEventListener("keydown", handlePhysicalKeyDown);

  // Initialize
  initKeyboard();
  // Automatically start first game on page load
  startNewGame();
})();

