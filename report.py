import chess
import chess.svg
from openings import opening_stats, reply_distribution, common_positions, moves_from_position

NICE = {
    "blunder_rate_endgame": "blunders in endgames",
    "blunder_rate_middlegame": "blunders in middlegames",
    "blunder_rate_opening": "blunders in the opening",
    "blunder_rate_low_clock": "blunders when low on time",
    "time_trouble_rate": "gets into time trouble",
    "capture_rate": "trades/captures",
    "draw_rate": "draws",
    "score_after_loss": "scores after a loss",
    "opening_entropy": "varies their openings",
}

def write_report(username, games_df, moves_df, z, path=None):
    lines = [f"# Scouting report: {username}", "",
             f"Games analysed: {len(games_df)}  |  "
             f"Overall score: {games_df['score'].mean():.0%}", ""]

    lines.append("## What stands out (vs. similar-rated players)")
    for feat, val in z.reindex(z.abs().sort_values(ascending=False).index).items():
        if abs(val) < 1.0 or feat not in NICE:
            continue
        word = "MORE than" if val > 0 else "LESS than"
        lines.append(f"- {NICE[feat].capitalize()} {word} typical ({val:+.1f} SD)")

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