"""A small Flask app that lists every Legend of Zelda game.

Game data comes from the free Zelda API: https://docs.zelda.fanapis.com
Box art comes from the Wikipedia API: https://www.mediawiki.org/wiki/API:Main_page
"""

import re

import requests
from flask import Flask, render_template, request

API_URL = "https://zelda.fanapis.com/api/games"
WIKIPEDIA_URL = "https://en.wikipedia.org/w/api.php"

# Wikipedia asks API clients to identify themselves.
HEADERS = {"User-Agent": "zelda-games-demo/0.1 (classroom git demo)"}

app = Flask(__name__)


def fetch_games(limit=100):
    """Return a list of game dicts from the Zelda API."""
    response = requests.get(API_URL, params={"limit": limit}, timeout=10)
    response.raise_for_status()
    return response.json()["data"]


def fetch_box_art(names):
    """Return a dict mapping each game name to a box art image URL.

    Looks up all names in one Wikipedia request (the API allows up to 50).
    Games without an image are left out of the result.
    """
    params = {
        "action": "query",
        "format": "json",
        "formatversion": 2,
        "prop": "pageimages",
        "piprop": "thumbnail",
        "pithumbsize": 300,
        "pilicense": "any",  # box art is fair use, not freely licensed
        "redirects": 1,
        "titles": "|".join(names),
    }
    response = requests.get(WIKIPEDIA_URL, params=params, headers=HEADERS, timeout=10)
    response.raise_for_status()
    query = response.json()["query"]

    # Wikipedia may rename a title (normalize it) and then follow a redirect,
    # so track where each name we sent ends up.
    renamed = {}
    for step in ("normalized", "redirects"):
        for change in query.get(step, []):
            renamed[change["from"]] = change["to"]

    images = {
        page["title"]: page["thumbnail"]["source"]
        for page in query["pages"]
        if "thumbnail" in page
    }

    box_art = {}
    for name in names:
        title = name
        while title in renamed:
            title = renamed[title]
        if title in images:
            box_art[name] = images[title]
    return box_art


def release_year(game):
    """Pull the four-digit year out of a game's release date, or None."""
    match = re.search(r"\d{4}", game.get("released_date", ""))
    return int(match.group()) if match else None


@app.route("/")
def index():
    try:
        games = fetch_games()
    except requests.RequestException:
        return render_template("index.html", games=[], error=True), 502

    query = request.args.get("q", "").strip()
    if query:
        games = [g for g in games if query.lower() in g["name"].lower()]

    # Box art is a nice extra, so the page still works if Wikipedia is down.
    try:
        box_art = fetch_box_art([game["name"] for game in games])
    except requests.RequestException:
        box_art = {}

    for game in games:
        game["year"] = release_year(game)
        game["box_art"] = box_art.get(game["name"])
    games.sort(key=lambda g: g["year"] or 0, reverse=True)

    return render_template("index.html", games=games, error=False, query=query)


if __name__ == "__main__":
    app.run(debug=True)
