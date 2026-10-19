import requests

import main

FAKE_GAMES = [
    {
        "name": "The Legend of Zelda: Ocarina of Time",
        "description": "Link travels through time.",
        "developer": "Nintendo EAD",
        "released_date": " November 23, 1998",
    },
    {
        "name": "The Legend of Zelda",
        "description": "The first game.",
        "developer": "Nintendo R&D 4",
        "released_date": " February 21, 1986",
    },
]

FAKE_BOX_ART = {"The Legend of Zelda": "https://example.com/zelda.jpg"}


class FakeResponse:
    """Stands in for a requests.Response in tests."""

    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_release_year():
    assert main.release_year({"released_date": " February 21, 1986"}) == 1986
    assert main.release_year({"released_date": "TBA"}) is None
    assert main.release_year({}) is None


def test_fetch_box_art_follows_redirects(monkeypatch):
    # "Oracle of Ages" redirects to an article that covers two games.
    wikipedia_data = {
        "query": {
            "redirects": [
                {
                    "from": "The Legend of Zelda: Oracle of Ages",
                    "to": "The Legend of Zelda: Oracle of Seasons and Oracle of Ages",
                }
            ],
            "pages": [
                {
                    "title": "The Legend of Zelda: Oracle of Seasons and Oracle of Ages",
                    "thumbnail": {"source": "https://example.com/oracle.jpg"},
                },
                {"title": "Some Game Without Art"},
            ],
        }
    }
    monkeypatch.setattr(main.requests, "get", lambda *a, **kw: FakeResponse(wikipedia_data))

    box_art = main.fetch_box_art(["The Legend of Zelda: Oracle of Ages", "Some Game Without Art"])

    assert box_art == {"The Legend of Zelda: Oracle of Ages": "https://example.com/oracle.jpg"}


def test_index_lists_games_oldest_first(monkeypatch):
    # Swap out the real API calls so tests do not depend on the network.
    monkeypatch.setattr(main, "fetch_games", lambda: [dict(g) for g in FAKE_GAMES])
    monkeypatch.setattr(main, "fetch_box_art", lambda names: FAKE_BOX_ART)
    client = main.app.test_client()

    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Ocarina of Time" in html
    assert html.index("The first game.") < html.index("Link travels through time.")
    assert "https://example.com/zelda.jpg" in html


def test_index_works_without_box_art(monkeypatch):
    def wikipedia_down(names):
        raise requests.ConnectionError("Wikipedia is down")

    monkeypatch.setattr(main, "fetch_games", lambda: [dict(g) for g in FAKE_GAMES])
    monkeypatch.setattr(main, "fetch_box_art", wikipedia_down)
    client = main.app.test_client()

    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Ocarina of Time" in html
    assert "<img" not in html


def test_index_handles_api_failure(monkeypatch):
    def broken():
        raise requests.ConnectionError("API is down")

    monkeypatch.setattr(main, "fetch_games", broken)
    client = main.app.test_client()

    response = client.get("/")

    assert response.status_code == 502
    assert "Could not reach the Zelda API" in response.get_data(as_text=True)
