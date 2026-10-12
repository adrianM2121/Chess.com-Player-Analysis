import io
import chess
import chess.pgn
import pandas as pd

DRAWS = {"agreed", "repetition", "stalemate", "insufficient",
         "50move", "timevsinsufficient"}

def score_from_result(result):
    if result == "win":
        return 1.0
    if result in DRAWS:
        return 0.5
    return 0.0

def parse_time_control(tc):
    """'600' -> (600, 0); '180+2' -> (180, 2); anything else -> (None, None)."""
    try:
        if "+" in tc:
            base, inc = tc.split("+")
            return int(base), int(inc)
        return int(tc), 0
    except ValueError:
        return None, None

def games_table(games, username):
    """One row per game, from the point of view of `username`."""
    username = username.lower()
    rows = []
    for g in games:
        if g.get("rules") != "chess" or "pgn" not in g:
            continue
        is_white = g["white"]["username"].lower() == username
        me, opp = (g["white"], g["black"]) if is_white else (g["black"], g["white"])
        base, inc = parse_time_control(g["time_control"])
        rows.append({
            "game_id": g["url"].split("/")[-1],
            "end_time": pd.to_datetime(g["end_time"], unit="s"),
            "time_class": g["time_class"],
            "base": base, "inc": inc,
            "color": "white" if is_white else "black",
            "rating": me["rating"], "opp_rating": opp["rating"],
            "opponent": opp["username"].lower(),
            "result": me["result"], "opp_result": opp["result"],
            "score": score_from_result(me["result"]),
            "opening": g.get("eco", "").split("/")[-1].replace("-", " "),
            "pgn": g["pgn"],
        })
    return pd.DataFrame(rows).sort_values("end_time").reset_index(drop=True)

def position_key(board):
    """FEN without the move counters, so identical positions match."""
    return " ".join(board.fen().split()[:4])

def moves_table(games_df):
    """One row per move (ply) for every game."""
    rows = []
    for _, g in games_df.iterrows():
        game = chess.pgn.read_game(io.StringIO(g["pgn"]))
        board = game.board()
        last_clock = {chess.WHITE: g["base"], chess.BLACK: g["base"]}
        for ply, node in enumerate(game.mainline(), start=1):
            mover = board.turn
            move = node.move
            clock = node.clock()                 # seconds left AFTER this move
            spent = None
            if clock is not None and last_clock[mover] is not None:
                spent = max(0.0, last_clock[mover] - clock + (g["inc"] or 0))
                last_clock[mover] = clock
            rows.append({
                "game_id": g["game_id"],
                "ply": ply,
                "move_number": (ply + 1) // 2,
                "mover": "white" if mover == chess.WHITE else "black",
                "is_player": (mover == chess.WHITE) == (g["color"] == "white"),
                "san": board.san(move),
                "uci": move.uci(),
                "fen_before": board.fen(),
                "pos_key": position_key(board),
                "is_capture": board.is_capture(move),
                "gives_check": board.gives_check(move),
                "n_legal": board.legal_moves.count(),
                "clock": clock,
                "time_spent": spent,
            })
            board.push(move)
    return pd.DataFrame(rows)