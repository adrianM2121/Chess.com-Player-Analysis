import json
import time
import requests
from config import HEADERS, RAW


def get_games(username, months = None, refresh = False):
    #download games and store then as a JSON file
    username = username.lower()
    cache = RAW / f"{username}.jason"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text())

    r = requests.get(f"https://api.chess.com/pub/player/{username}/games/archives", headers = HEADERS)
    r.raise_for_status()
    archives = r.json()["archives"]
    if months:
        archives = archives[ -months:]
    games = []
    for url in archives:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        games.extend(resp.json()["games"])
        time.sleep(0.5)
    cache.write_text(json.dumps(games))
    print(f"{username}: {len(games)} games from {len(archives)} months")
    return games

