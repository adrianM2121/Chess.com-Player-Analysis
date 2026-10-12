import pandas as pd
from fetch import get_games
from parse import games_table, moves_table
from engine_eval import evaluate_games
from features import player_features

def pick_baseline_players(games_df, rating, window=100, n=30):
    """Use the target's own past opponents who are rated close to them."""
    near = games_df[(games_df["opp_rating"] - rating).abs() <= window]
    return list(near["opponent"].drop_duplicates().head(n))

def features_for(username, time_class="rapid", months=3, max_games=40, depth=10):
    games = get_games(username, months=months)
    gdf = games_table(games, username)
    gdf = gdf[gdf["time_class"] == time_class].tail(max_games)
    if len(gdf) < 10:
        return None                                   # too few games to trust
    moves = moves_table(gdf)
    evals = evaluate_games(moves, username, depth=depth)
    feats = player_features(gdf, evals)
    feats["username"] = username
    return feats

def build_baseline(usernames, **kwargs):
    rows = []
    for u in usernames:
        try:
            f = features_for(u, **kwargs)
            if f:
                rows.append(f)
        except Exception as e:                        # closed accounts, network hiccups...
            print(f"skipping {u}: {e}")
    return pd.DataFrame(rows).set_index("username")