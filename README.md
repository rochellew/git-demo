# Zelda Games

[![CI](https://github.com/rochellew/git-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/rochellew/git-demo/actions/workflows/ci.yml)

A small Flask app that lists every Legend of Zelda game, using the free [Zelda API](https://docs.zelda.fanapis.com) for game data and the [Wikipedia API](https://www.mediawiki.org/wiki/API:Main_page) for box art.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```
uv sync
```

## Run

```
uv run main.py
```

Then open http://127.0.0.1:5000

## Test

```
uv run pytest
uv run ruff check .
```

## CI

GitHub Actions runs the linter and tests on every pull request into `main` and every push to `main` (including merged pull requests). See the **Actions** tab for results.
