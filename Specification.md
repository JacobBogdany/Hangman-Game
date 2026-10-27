# Hangman Client/Server Project Specification

## Overview

This project implements a networked Hangman game with a server and a
browser-based client.

The goal of the project is to provide an enjoyable, interactive Hangman
game playable directly in a web browser, powered by a backend REST API.

The server contains all game logic. Clients never know the hidden word
until the game has ended.

------------------------------------------------------------------------

# System Architecture

                       +----------------------+
                       |    Hangman Server    |
                       |----------------------|
                       | Game Engine          |
                       | Word Manager         |
                       | REST API             |
                       +----------+-----------+
                                  |
                           HTTP / JSON API
                                  |
                       +----------v-----------+
                       |    Browser Client    |
                       |    HTML / CSS / JS   |
                       +----------------------+

------------------------------------------------------------------------

# Components

## 1. Game Engine

Responsible for:

-   Selecting a random word
-   Tracking guessed letters
-   Tracking incorrect guesses
-   Determining win/loss
-   Producing the masked word
-   Serializing game state

The game engine must not depend on Flask or any user interface.

------------------------------------------------------------------------

## 2. REST Server

Recommended implementation:

-   Python
-   Flask (or FastAPI)

Responsibilities:

-   Create games
-   Process guesses
-   Return JSON responses
-   Store active games

------------------------------------------------------------------------

## 3. Browser Client

Features:

-   Difficulty selection
-   Graphical Hangman
-   Keyboard input
-   Remaining guesses
-   Previous guesses
-   New game button

Communication uses the REST API only.

------------------------------------------------------------------------

# REST API

## Create Game

POST

    /api/games

Request

``` json
{
    "difficulty":"medium"
}
```

Response

``` json
{
    "game_id":"abc123",
    "pattern":"_ _ _ _ _",
    "remaining_guesses":6,
    "status":"playing"
}
```

------------------------------------------------------------------------

## Guess Letter

POST

    /api/games/{game_id}/guess

Request

``` json
{
    "letter":"e"
}
```

Response

``` json
{
    "pattern":"_ e _ _ e",
    "guessed_letters":["e"],
    "incorrect_letters":[],
    "remaining_guesses":6,
    "status":"playing"
}
```

------------------------------------------------------------------------

## Get Current State

GET

    /api/games/{game_id}

------------------------------------------------------------------------

# Game Rules

-   One letter per guess
-   Duplicate guesses are ignored or rejected
-   Six incorrect guesses allowed
-   Word is revealed only after the game ends
-   Server is authoritative

------------------------------------------------------------------------

# Word Lists

Three difficulty levels:

-   Easy
-   Medium
-   Hard

Stored as

    words/
        easy.txt
        medium.txt
        hard.txt

------------------------------------------------------------------------

# Suggested Project Structure

    hangman/
    │
    ├── README.md
    ├── requirements.txt
    ├── server.py
    ├── game.py
    ├── static/
    │   ├── index.html
    │   ├── style.css
    │   └── app.js
    └── words/
        ├── easy.txt
        ├── medium.txt
        └── hard.txt

------------------------------------------------------------------------

# Future Extensions

-   Multiplayer / Versus mode
-   User accounts and stats
-   Persistent database
-   Sound effects and animations
-   Custom word lists / categories
-   Daily challenge
