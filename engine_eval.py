import math
import chess
import chess.engine
import pandas as pd
from config import STOCKFISH_PATH, PROCESSED

def win_percent(cp):
    """Centipawns (White's view) -> White's winning chances, 0-100."""
    return 100 / (1 + math.exp(-0.00368208 * cp))

def eval_positions(fens, engine, depth=10):
    """Evaluate a list of FENs; returns centipawns from White's point of view."""
    out = []
    for fen in fens:
        info = engine.analyse(chess.Board(fen), chess.engine.Limit(depth=depth))
        out.append(info["score"].white().score(mate_score=10000))
    return out

def evaluate_games(moves_df, username, depth=10, max_games=None):
    """Adds engine evaluations to every move. Caches results so you never redo work."""
    cache = PROCESSED / f"{username.lower()}_evals.csv"
    done = pd.read_csv(cache, dtype={"game_id": str}) if cache.exists() else pd.DataFrame()
    done_ids = set(done["game_id"]) if len(done) else set()

    todo = [g for g in moves_df["game_id"].unique() if g not in done_ids]
    if max_games:
        todo = todo[:max_games]

    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    try:
        for i, gid in enumerate(todo, 1):
            g = moves_df[moves_df["game_id"] == gid].sort_values("ply")
            board = chess.Board(g["fen_before"].iloc[-1])
            board.push_uci(g["uci"].iloc[-1])
            fens = list(g["fen_before"]) + [board.fen()]       # every position, incl. final
            cps = eval_positions(fens, engine, depth)
            rows = pd.DataFrame({"game_id": gid, "ply": g["ply"].values,
                                 "cp_before": cps[:-1], "cp_after": cps[1:]})
            rows.to_csv(cache, mode="a", header=not cache.exists(), index=False)
            print(f"[{i}/{len(todo)}] evaluated game {gid}")
    finally:
        engine.quit()

    evals = pd.read_csv(cache, dtype={"game_id": str})
    return add_move_quality(moves_df.merge(evals, on=["game_id", "ply"]))

def add_move_quality(df):
    """Win% lost by each move, from the mover's point of view, and labels."""
    wp_before = df["cp_before"].apply(win_percent)
    wp_after = df["cp_after"].apply(win_percent)
    white = df["mover"] == "white"
    df["wp_before"] = wp_before.where(white, 100 - wp_before)   # mover's chances
    df["wp_after"] = wp_after.where(white, 100 - wp_after)
    df["wp_loss"] = (df["wp_before"] - df["wp_after"]).clip(lower=0)
    df["quality"] = pd.cut(df["wp_loss"], [-1, 10, 20, 30, 101],
                           labels=["ok", "inaccuracy", "mistake", "blunder"])
    df["blunder"] = (df["wp_loss"] >= 30).astype(int)
    return df