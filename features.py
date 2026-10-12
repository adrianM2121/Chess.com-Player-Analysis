import math
import numpy as np
import pandas as pd

def game_phase(fen, ply):
    """Opening = first 20 plies; endgame = 6 or fewer queens/rooks/bishops/knights left."""
    pieces = sum(fen.split()[0].lower().count(p) for p in "qrbn")
    if pieces <= 6:
        return "endgame"
    return "opening" if ply <= 20 else "middlegame"

def entropy(counts):
    """Shannon entropy in bits: 0 = always the same choice, higher = more varied."""
    p = np.array(counts, dtype=float)
    p = p / p.sum()
    return float(-(p * np.log2(p)).sum())

def player_features(games_df, evals_df):
    """Summarise one player as a dictionary of numbers (their 'style vector')."""
    mine = evals_df[evals_df["is_player"]].copy()
    mine["phase"] = [game_phase(f, p) for f, p in zip(mine["fen_before"], mine["ply"])]
    g = games_df.set_index("game_id")
    base = mine["game_id"].map(g["base"])
    mine["clock_frac"] = mine["clock"] / base                 # share of clock left

    f = {}
    # --- accuracy ---
    f["avg_wp_loss"] = mine["wp_loss"].mean()
    for ph in ["opening", "middlegame", "endgame"]:
        sub = mine[mine["phase"] == ph]
        f[f"blunder_rate_{ph}"] = sub["blunder"].mean() if len(sub) else np.nan
    low = mine[mine["clock_frac"] < 0.10]
    f["blunder_rate_low_clock"] = low["blunder"].mean() if len(low) else np.nan

    # --- time management ---
    f["avg_time_per_move"] = (mine["time_spent"] / base).mean()   # as share of base time
    min_clock = mine.groupby("game_id")["clock_frac"].min()
    f["time_trouble_rate"] = (min_clock < 0.10).mean()
    f["timeout_loss_rate"] = (games_df["result"] == "timeout").mean()

    # --- style ---
    f["capture_rate"] = mine["is_capture"].mean()
    f["check_rate"] = mine["gives_check"].mean()
    f["avg_game_length"] = evals_df.groupby("game_id")["ply"].max().mean()
    f["draw_rate"] = (games_df["score"] == 0.5).mean()
    losses = games_df[games_df["score"] == 0]
    f["resign_share_of_losses"] = ((losses["result"] == "resigned").mean()
                                   if len(losses) else np.nan)
    first = evals_df[(evals_df["ply"] == 1) & evals_df["is_player"]]["san"].value_counts()
    f["opening_entropy"] = entropy(first) if len(first) else 0.0

    # --- tilt: score in the game right after a loss vs overall ---
    after_loss = games_df["score"].shift(1) == 0
    f["score_overall"] = games_df["score"].mean()
    f["score_after_loss"] = games_df.loc[after_loss, "score"].mean()
    return f