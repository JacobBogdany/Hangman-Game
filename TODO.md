# TODO — Hangman Client/Server Project

This file is the implementation roadmap for the Hangman project.

The authoritative system requirements are defined in `Specification.md`.

## Implementation Rules

- Implement one phase at a time.
- Complete and test all items in the current phase before moving to the next phase.
- Do not change the architecture or REST API defined in `Specification.md` unless necessary.
- If a deviation is necessary, document it in the README and update the specification.
- Keep the game engine independent from Flask and the browser UI.
- The server must remain authoritative.
- Never expose the hidden word before a game ends.
- Add tests as each phase is implemented rather than postponing testing until the end.

---

## Phase 1 — Project Skeleton and Core Game Engine

### Tasks

- [x] Create the project directory structure.
- [x] Add `words/easy.txt`.
- [x] Add `words/medium.txt`.
- [x] Add `words/hard.txt`.
- [x] Create `game.py`.
- [x] Implement a `HangmanGame` class.
- [x] Store the hidden word internally.
- [x] Track guessed letters.
- [x] Track incorrect letters.
- [x] Track the maximum number of incorrect guesses.
- [x] Implement single-letter guess validation.
- [x] Detect duplicate guesses.
- [x] Implement masked-word generation.
- [x] Implement win detection.
- [x] Implement loss detection.
- [x] Implement game status values such as `playing`, `won`, and `lost`.
- [x] Implement a method that returns a client-safe game-state dictionary.
- [x] Reveal the answer only after the game ends.
- [x] Add unit tests for the game engine.

### Completion Criteria

The game engine can be tested entirely without running a web server.

All core rules are covered by unit tests.

---

## Phase 2 — Word Management

### Tasks

- [ ] Create a word-loading module or helper functions.
- [ ] Load Easy, Medium, and Hard word lists.
- [ ] Validate that loaded words contain only alphabetic characters.
- [ ] Remove accidental duplicates when loading.
- [ ] Support random word selection by difficulty.
- [ ] Return an error for an invalid difficulty.
- [ ] Add tests for word loading and word selection.

### Completion Criteria

The program can request a random word from each difficulty level reliably.

Invalid difficulty values are rejected cleanly.

---

## Phase 3 — Basic REST Server

### Tasks

- [ ] Create `server.py`.
- [ ] Configure Flask or FastAPI.
- [ ] Add in-memory storage for active games.
- [ ] Generate unique game IDs.
- [ ] Implement `POST /api/games`.
- [ ] Implement `GET /api/games/{game_id}`.
- [ ] Implement `POST /api/games/{game_id}/guess`.
- [ ] Validate difficulty input.
- [ ] Validate guess input.
- [ ] Return JSON responses consistently.
- [ ] Return appropriate HTTP status codes.
- [ ] Handle unknown game IDs.
- [ ] Handle malformed requests.
- [ ] Ensure the hidden word is never leaked during an active game.
- [ ] Add API tests.

### Completion Criteria

A complete Hangman game can be played using only `curl` or another HTTP client.

The browser client is not required for this phase.

---

## Phase 4 — Browser Client

### Tasks

- [ ] Create `static/index.html`.
- [ ] Create `static/style.css`.
- [ ] Create `static/app.js`.
- [ ] Add a difficulty selector.
- [ ] Add a New Game button.
- [ ] Display the masked word.
- [ ] Display guessed letters.
- [ ] Display incorrect letters.
- [ ] Display remaining guesses.
- [ ] Add an on-screen alphabet keyboard.
- [ ] Disable already-guessed letters.
- [ ] Use `fetch()` to communicate with the REST API.
- [ ] Draw the Hangman state visually.
- [ ] Update the drawing after incorrect guesses.
- [ ] Display win and loss messages.
- [ ] Provide a restart/new-game flow.
- [ ] Make the interface usable on common desktop and mobile browser sizes.

### Completion Criteria

A human player can play the same server-hosted game from a browser.

No hidden word is stored in browser-side JavaScript.

---

## Phase 5 — Testing

### Tasks

- [ ] Complete unit tests for `HangmanGame`.
- [ ] Complete tests for word loading.
- [ ] Complete REST API tests.
- [ ] Test duplicate guesses.
- [ ] Test invalid letters.
- [ ] Test invalid difficulty.
- [ ] Test missing game IDs.
- [ ] Test win paths.
- [ ] Test loss paths.
- [ ] Test answer disclosure rules.
- [ ] Test browser-client integration.
- [ ] Add an end-to-end automated test.

### Completion Criteria

The major user flows and failure cases are covered by automated tests.

---

## Phase 6 — Documentation and Packaging

### Tasks

- [ ] Create or update `README.md`.
- [ ] Document installation.
- [ ] Document how to start the server.
- [ ] Document how to use the browser client.
- [ ] Document the REST API.
- [ ] Provide example requests and responses.
- [ ] Add dependency information such as `requirements.txt` or `pyproject.toml`.
- [ ] Verify that a fresh installation works from the documented instructions.

### Completion Criteria

A new user can clone the project, install dependencies, start the server, and play from the browser using only the documentation.

---

# Optional Future Phases

These should not be implemented until the core project is stable.

## Persistent Storage

- [ ] Store games in a database.

## Accounts and Authentication

- [ ] User accounts and stats.

## Multiplayer

- [ ] Human-vs-human modes.
- [ ] Custom words.

---

# Recommended Development Order

Use this order unless there is a compelling reason to change it:

1. Core Game Engine
2. Word Management
3. REST Server
4. Browser Client
5. Full Testing
6. Documentation and Packaging

The project should remain runnable after every completed phase.
