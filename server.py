"""REST Server for Hangman.

Exposes a RESTful JSON API using Flask for managing and playing Hangman games:
- POST /api/games: Create a new game
- GET  /api/games/<game_id>: Get current game state
- POST /api/games/<game_id>/guess: Submit a letter guess
"""

import os
from typing import Any, Dict, Optional
import uuid

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

from game import (
    HangmanGame,
    InvalidGuessError,
    DuplicateGuessError,
    GameOverError,
)
from words import (
    WordManager,
    InvalidDifficultyError,
    get_default_manager,
)


def create_app(
    word_manager: Optional[WordManager] = None,
    test_config: Optional[Dict[str, Any]] = None,
) -> Flask:
    """Application factory for the Hangman REST Server."""
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    app = Flask(__name__, static_folder=static_dir, static_url_path="")
    CORS(app)

    if test_config:
        app.config.update(test_config)

    # In-memory storage for active games: game_id -> HangmanGame
    games: Dict[str, HangmanGame] = {}
    manager = word_manager or get_default_manager()

    @app.errorhandler(404)
    def not_found(e: Any) -> tuple[Response, int]:
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e: Any) -> tuple[Response, int]:
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e: Any) -> tuple[Response, int]:
        return jsonify({"error": "Internal server error"}), 500

    @app.route("/")
    def index() -> Any:
        """Serve the frontend client if index.html exists, otherwise return a welcome payload."""
        if app.static_folder and os.path.exists(os.path.join(app.static_folder, "index.html")):
            return app.send_static_file("index.html")
        return jsonify({
            "name": "Hangman REST API",
            "version": "1.0.0",
            "endpoints": {
                "create_game": "POST /api/games",
                "get_game": "GET /api/games/{game_id}",
                "guess": "POST /api/games/{game_id}/guess",
            },
        })

    @app.route("/api/games", methods=["POST"])
    def create_game() -> tuple[Response, int]:
        """Create a new game.

        Request JSON (optional):
            {"difficulty": "easy" | "medium" | "hard"} (default: "medium")

        Returns:
            201 Created with initial game state.
        """
        data: Dict[str, Any] = {}
        if request.is_json and request.data:
            parsed = request.get_json(silent=True)
            if parsed is None:
                return jsonify({"error": "Malformed JSON in request body"}), 400
            if isinstance(parsed, dict):
                data = parsed
            else:
                return jsonify({"error": "Request body must be a JSON object"}), 400
        elif request.data:
            # Body provided but not valid application/json
            return jsonify({"error": "Content-Type must be application/json"}), 400

        difficulty = data.get("difficulty", "medium")

        try:
            secret_word = manager.get_random_word(difficulty)
        except InvalidDifficultyError as e:
            return jsonify({
                "error": str(e),
                "allowed_difficulties": list(WordManager.VALID_DIFFICULTIES),
            }), 400

        game_id = uuid.uuid4().hex[:8]
        while game_id in games:
            game_id = uuid.uuid4().hex[:8]

        game = HangmanGame(word=secret_word, game_id=game_id)
        games[game_id] = game

        return jsonify(game.to_dict()), 201

    @app.route("/api/games/<game_id>", methods=["GET"])
    def get_game(game_id: str) -> tuple[Response, int]:
        """Fetch the current state of a game.

        Returns:
            200 OK with game state, or 404 if game_id is unknown.
        """
        game = games.get(game_id)
        if game is None:
            return jsonify({"error": f"Game with ID '{game_id}' not found"}), 404

        return jsonify(game.to_dict()), 200

    @app.route("/api/games/<game_id>/guess", methods=["POST"])
    def guess_letter(game_id: str) -> tuple[Response, int]:
        """Submit a single letter guess for an active game.

        Request JSON:
            {"letter": "e"}

        Returns:
            200 OK with updated game state.
            400 Bad Request on invalid guess, duplicate guess, or finished game.
            404 Not Found if game_id does not exist.
        """
        game = games.get(game_id)
        if game is None:
            return jsonify({"error": f"Game with ID '{game_id}' not found"}), 404

        if game.is_game_over:
            return jsonify({
                "error": f"Cannot guess on a finished game. Game status: '{game.status}'",
                "status": game.status,
                "word": game.word,
            }), 400

        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json(silent=True)
        if data is None or not isinstance(data, dict):
            return jsonify({"error": "Request body must be a valid JSON object"}), 400

        if "letter" not in data:
            return jsonify({"error": "Missing required field 'letter' in request body"}), 400

        raw_letter = data["letter"]

        try:
            state = game.guess(raw_letter)
            return jsonify(state), 200
        except InvalidGuessError as e:
            return jsonify({"error": str(e)}), 400
        except DuplicateGuessError as e:
            return jsonify({"error": str(e)}), 400
        except GameOverError as e:
            return jsonify({"error": str(e)}), 400

    # Store games dict on app for testing inspection if needed
    app.games = games  # type: ignore[attr-defined]

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Hangman Server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)

