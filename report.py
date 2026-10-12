import numpy as np
import pandas as pd
import chess
import chess.svg
from openings import opening_stats, reply_distribution, common_positions, moves_from_position

# feature name -> (plain-English description, how to display the number)
STATS = {
    "score_overall": ("Overall score (win = 1, draw = 1/2, loss = 0)", "pct"),
    "score_after_loss": ("Score in the game right after a loss (tilt check)", "pct"),
    "avg_wp_loss": ("Average winning chances lost per move (percentage points)", "num"),
    "blunder_rate_opening": ("Share of moves that are blunders in the opening (first 10 moves)", "pct"),
    "blunder_rate_middlegame": ("Share of moves that are blunders in the middlegame", "pct"),
    "blunder_rate_endgame": ("Share of moves that are blunders in the endgame", "pct"),
    "blunder_rate_low_clock": ("Share of moves that are blunders with under 10% of the clock left", "pct"),
    "avg_time_per_move": ("Average time spent per move, as a share of the starting clock", "pct"),
    "time_trouble_rate": ("Share of games where their clock fell below 10%", "pct"),
    "timeout_loss_rate": ("Share of games lost on time", "pct"),
    "capture_rate": ("Share of moves that capture a piece", "pct"),
    "check_rate": ("Share of moves that give check", "pct"),
    "avg_game_length": ("Average game length", "plies"),
    "draw_rate": ("Share of games drawn", "pct"),
    "resign_share_of_losses": ("Share of losses that ended by resigning", "pct"),
    "opening_entropy": ("Opening variety as White (0 = always the same first move)", "num"),
}

def fmt(value, unit):
    if pd.isna(value):
        return "n/a"
    if unit == "pct":
        return f"{value:.1%}"
    if unit == "plies":
        return f"{value / 2:.0f} moves"
    return f"{value:.2f}"

def compare(z):
    if pd.isna(z):
        return "not enough data"
    if z >= 2:
        return f"much higher ({z:+.1f} SD)"
    if z >= 1:
        return f"higher ({z:+.1f} SD)"
    if z <= -2:
        return f"much lower ({z:+.1f} SD)"
    if z <= -1:
        return f"lower ({z:+.1f} SD)"
    return f"about average ({z:+.1f} SD)"

def write_report(username, games_df, moves_df, z, feats, typical, path=None):
    lines = [f"# Scouting report: {username}", "",
             f"Games analysed: {len(games_df)}  |  "
             f"Overall score: {games_df['score'].mean():.0%}", ""]

    # --- full profile, most unusual first ---
    lines += ["## Full profile (vs. similar-rated players)", "",
              "| What's measured | This player | Typical | Compared to typical |",
              "|---|---|---|---|"]
    def unusualness(key):
        val = z.get(key, np.nan)
        return abs(val) if pd.notna(val) else -1
    for key in sorted(STATS, key=unusualness, reverse=True):
        desc, unit = STATS[key]
        lines.append(f"| {desc} | {fmt(feats.get(key), unit)} | "
                     f"{fmt(typical.get(key), unit)} | {compare(z.get(key, np.nan))} |")

    # --- openings ---
    lines += ["", "## Openings"]
    for first in (["e4"], ["d4"]):
        dist = reply_distribution(moves_df, games_df, first)
        if len(dist):
            top = ", ".join(f"{m} {p:.0%}" for m, p in dist.head(3).items())
            lines.append(f"- As Black vs 1.{first[0]}: {top}")
    stats = opening_stats(games_df)
    if len(stats):
        worst = stats.iloc[0]
        lines.append(f"- Weakest opening: {worst['opening']} as {worst['color']} "
                     f"(smoothed score {worst['smoothed']:.0%} over {worst['count']} games)")

    # --- common positions ---
    lines += ["", "## Positions they keep reaching"]
    for i, (_, row) in enumerate(common_positions(moves_df, games_df).head(3).iterrows(), 1):
        usual = moves_from_position(moves_df, row["pos_key"]).head(2)
        lines.append(f"- Position {i} (seen {row['count']}x, score {row['avg_score']:.0%}); "
                     f"they usually play: {', '.join(usual.index)}")
        board = chess.Board(row["pos_key"] + " 0 1")
        with open(f"{username}_position_{i}.svg", "w") as f:
            f.write(chess.svg.board(board, size=300))

    text = "\n".join(lines)
    with open(path or f"{username}_report.md", "w") as f:
        f.write(text)
    return text