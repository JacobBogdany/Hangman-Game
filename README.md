# Hangman Game (Server & Browser Client)

A networked Hangman game featuring an authoritative REST backend and a modern, responsive browser client with real-time SVG Hangman visualization and keyboard interaction.

---

## Architecture Overview

```text
                       +----------------------+
                       |    Hangman Server    |
                       |----------------------|
                       | Game Engine (game.py)|
                       | Word Manager(words.py|
                       | REST API (server.py) |
                       +----------+-----------+
                                  |
                           HTTP / JSON API
                                  |
                       +----------v-----------+
                       |    Browser Client    |
                       |  (static/index.html) |
                       |  (static/style.css)  |
                       |  (static/app.js)     |
                       +----------------------+
```

### Key Principles
- **Authoritative Server:** All game state, word selection, and win/loss logic live on the server.
- **Anti-Cheat Protection:** The hidden word is never leaked to the client during active play (`status: "playing"`). It is only disclosed upon game conclusion (`won` or `lost`).
- **Responsive Web UI:** Playable across desktop and mobile devices with both on-screen buttons and physical keyboard input.

---

## Project Structure

```text
Hangman-Game/
├── README.md               # Project documentation
├── requirements.txt        # Python package dependencies
├── server.py               # Flask REST server & static file host
├── game.py                 # Core Hangman game engine
├── words.py                # Word loader, validator, and selector
├── static/                 # Frontend browser client
│   ├── index.html          # Main web application page
│   ├── style.css           # Styling, animations, and responsive layouts
│   └── app.js              # Client-side API caller & SVG renderer
├── words/                  # Word lists by difficulty
│   ├── easy.txt            # 4-5 letter common words
│   ├── medium.txt          # 6-7 letter moderate words
│   └── hard.txt            # 8+ letter challenging words
└── tests/                  # Automated test suite
    ├── test_game.py        # Core engine unit tests
    ├── test_words.py       # Word management unit tests
    ├── test_server.py      # REST API integration tests
    ├── test_client_integration.py # Browser client asset tests
    └── test_e2e.py         # End-to-end full lifecycle tests
```

---

## Installation & Setup

### Prerequisites
- Python 3.9+ (or Windows `py` launcher)
- `pip` package manager

### 1. Clone or Open the Workspace
```powershell
cd "c:\Users\Jacob\agentic programming\Hangman-Game"
```

### 2. (Optional) Create a Virtual Environment
```powershell
py -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
py -m pip install -r requirements.txt
```

---

## Starting the Server

Start the Flask REST server:

```powershell
py server.py
```

*By default, the server runs on `http://127.0.0.1:5000`.*
*(You can customize the port by setting the `PORT` environment variable, e.g., `$env:PORT=8000; py server.py`).*

---

## Playing via the Browser Client

1. Start the server as shown above.
2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```
3. **Gameplay Controls:**
   - **Difficulty Dropdown:** Select `Easy`, `Medium`, or `Hard`.
   - **New Game Button:** Starts a fresh round immediately.
   - **Guessing Letters:** Click on any letter button on the on-screen keyboard, or simply type letters on your physical keyboard.
   - **Feedback:** Correct letters are highlighted in green and unmask the word pattern. Incorrect letters are marked in red and progressively draw the Hangman figure.

---

## REST API Reference

The server exposes a clean, JSON-based REST API under `/api/games`.

### 1. Create Game

- **Endpoint:** `POST /api/games`
- **Headers:** `Content-Type: application/json`
- **Request Body (Optional):**
  ```json
  {
    "difficulty": "medium"
  }
  ```
  *(Allowed values: `"easy"`, `"medium"`, `"hard"`. Defaults to `"medium"`).*

- **Response (201 Created):**
  ```json
  {
    "game_id": "a1b2c3d4",
    "pattern": "_ _ _ _ _ _",
    "guessed_letters": [],
    "incorrect_letters": [],
    "remaining_guesses": 6,
    "status": "playing"
  }
  ```

---

### 2. Get Game State

- **Endpoint:** `GET /api/games/<game_id>`
- **Response (200 OK):**
  ```json
  {
    "game_id": "a1b2c3d4",
    "pattern": "_ a _ a _ a",
    "guessed_letters": ["a"],
    "incorrect_letters": [],
    "remaining_guesses": 6,
    "status": "playing"
  }
  ```
- **Error (404 Not Found):**
  ```json
  {
    "error": "Game with ID 'unknown_id' not found"
  }
  ```

---

### 3. Submit Guess

- **Endpoint:** `POST /api/games/<game_id>/guess`
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "letter": "e"
  }
  ```

- **Response (200 OK - Active Game):**
  ```json
  {
    "game_id": "a1b2c3d4",
    "pattern": "_ e _ _ e",
    "guessed_letters": ["e"],
    "incorrect_letters": [],
    "remaining_guesses": 6,
    "status": "playing"
  }
  ```

- **Response (200 OK - Game Concluded):**
  When status transitions to `"won"` or `"lost"`, the secret `"word"` field is revealed:
  ```json
  {
    "game_id": "a1b2c3d4",
    "pattern": "a p p l e",
    "guessed_letters": ["a", "p", "l", "e"],
    "incorrect_letters": [],
    "remaining_guesses": 6,
    "status": "won",
    "word": "apple"
  }
  ```

- **Error Responses (400 Bad Request):**
  - Duplicate guess:
    ```json
    { "error": "Letter 'e' has already been guessed." }
    ```
  - Invalid character (numbers, multiple letters, symbols):
    ```json
    { "error": "Guess must be a single alphabetic letter (a-z)." }
    ```
  - Move on finished game:
    ```json
    {
      "error": "Cannot guess on a finished game. Game status: 'won'",
      "status": "won",
      "word": "apple"
    }
    ```

---

## Playing from the Command Line

### Using Windows PowerShell (`Invoke-RestMethod`)

```powershell
# 1. Start a game
$game = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/api/games" -ContentType "application/json" -Body '{"difficulty":"easy"}'
$game | Select-Object game_id, pattern, remaining_guesses, status

# 2. Submit a guess
$result = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/api/games/$($game.game_id)/guess" -ContentType "application/json" -Body '{"letter":"e"}'
$result | Select-Object pattern, remaining_guesses, status, word
```

### Using Windows `curl.exe`

```powershell
# 1. Start a game
curl.exe -s -X POST http://127.0.0.1:5000/api/games -H "Content-Type: application/json" -d "{\`"difficulty\`":\`"medium\`"}"

# 2. Guess a letter (replace YOUR_GAME_ID)
curl.exe -s -X POST http://127.0.0.1:5000/api/games/YOUR_GAME_ID/guess -H "Content-Type: application/json" -d "{\`"letter\`":\`"a\`"}"
```

---

## Running the Automated Tests

The test suite is fully compatible with both `pytest` and Python's standard library `unittest` runner.

### Run with `pytest`:
```powershell
py -m pytest -v
```

### Run with standard `unittest`:
```powershell
py -m unittest discover tests -v
```

All 56 tests across 5 test suites (Game Engine, Word Manager, REST API, Client Integration, and End-to-End Lifecycles) run in under 0.5s.

