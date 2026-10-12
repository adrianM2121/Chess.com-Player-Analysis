import sys
from fetch import get_games
from parse import games_table, moves_table
from engine_eval import evaluate_games
from features import player_features
from baseline import pick_baseline_players, build_baseline
from style import zscores
from report import write_report

def scout(username, time_class="rapid", max_games=200):
    username = username.lower()
    games = get_games(username, months=6)
    gdf = games_table(games, username)
    gdf = gdf[gdf["time_class"] == time_class].tail(max_games)
    moves = moves_table(gdf)
    evals = evaluate_games(moves, username, depth=10)

    rating = int(gdf["rating"].iloc[-1])
    peers = pick_baseline_players(gdf, rating, n=20)
    baseline = build_baseline(peers, time_class=time_class)
    baseline.to_csv(f"data/processed/{username}_baseline.csv")

    feats = player_features(gdf, evals)
    z = zscores(baseline, feats)
    return write_report(username, gdf, moves, z, feats, baseline.mean())

if __name__ == "__main__":
    name = sys.argv[1]
    tc = sys.argv[2] if len(sys.argv) > 2 else "rapid"
    print(scout(name, time_class=tc))