import pandas as pd
from scipy.stats import beta


def smoothed_rate(total_score, n, prior_mean=0.5, prior_strength=10):
    """Bayesian (Beta-prior) estimate of a score rate.

    Acts like adding `prior_strength` imaginary games scored at
    `prior_mean`.
    """
    return (total_score + prior_mean * prior_strength) / (n + prior_strength)


def credible_interval(
    total_score, n, prior_mean=0.5, prior_strength=10, level=0.80
):
    a = total_score + prior_mean * prior_strength
    b = (n - total_score) + (1 - prior_mean) * prior_strength

    lo, hi = beta.ppf(
        [(1 - level) / 2, (1 + level) / 2],
        a,
        b,
    )
    return lo, hi


def opening_stats(games_df, min_games=3):
    """Win rate by named opening and colour, with smoothing."""
    prior = games_df["score"].mean()

    grp = games_df.groupby(["color", "opening"])["score"].agg(
        ["count", "sum"]
    )
    grp = grp[grp["count"] >= min_games].reset_index()

    grp["raw_rate"] = grp["sum"] / grp["count"]
    grp["smoothed"] = smoothed_rate(
        grp["sum"],
        grp["count"],
        prior_mean=prior,
    )

    grp[["ci_low", "ci_high"]] = grp.apply(
        lambda r: pd.Series(
            credible_interval(
                r["sum"],
                r["count"],
                prior,
            )
        ),
        axis=1,
    )

    return grp.sort_values("smoothed")


def opening_tree(games_df, moves_df, color, depth=4):
    """Most common move sequences (first `depth` plies) when the player has `color`."""
    first = (
        moves_df[moves_df["ply"] <= depth]
        .groupby("game_id")["san"]
        .apply(" ".join)
        .rename("line")
    )

    df = games_df[games_df["color"] == color].join(
        first,
        on="game_id",
    )

    prior = games_df["score"].mean()

    tree = (
        df.groupby("line")["score"]
        .agg(["count", "sum"])
        .reset_index()
    )

    tree["smoothed"] = smoothed_rate(
        tree["sum"],
        tree["count"],
        prior_mean=prior,
    )
    tree["share"] = tree["count"] / tree["count"].sum()

    return tree.sort_values("count", ascending=False)


def reply_distribution(moves_df, games_df, prefix):
    """Given the moves so far (e.g. ['e4']), how does the player respond?"""
    prefix = list(prefix)
    k = len(prefix)

    color = "white" if k % 2 == 0 else "black"

    ids = games_df.loc[
        games_df["color"] == color,
        "game_id",
    ]

    m = moves_df[
        moves_df["game_id"].isin(ids)
        & (moves_df["ply"] <= k + 1)
    ]

    seqs = (
        m.sort_values("ply")
        .groupby("game_id")["san"]
        .apply(list)
    )

    replies = [
        s[k]
        for s in seqs
        if len(s) > k and s[:k] == prefix
    ]

    return pd.Series(replies).value_counts(normalize=True)


def common_positions(
    moves_df,
    games_df,
    min_ply=8,
    max_ply=24,
    min_count=3,
):
    """Positions the player reaches again and again, with their score from them."""
    m = moves_df[
        (moves_df["ply"] >= min_ply)
        & (moves_df["ply"] <= max_ply)
    ]

    m = m.drop_duplicates(
        ["game_id", "pos_key"]
    )

    m = m.merge(
        games_df[["game_id", "score"]],
        on="game_id",
    )

    pos = (
        m.groupby("pos_key")
        .agg(
            count=("game_id", "nunique"),
            avg_score=("score", "mean"),
            example_ply=("ply", "min"),
        )
        .reset_index()
    )

    return pos[
        pos["count"] >= min_count
    ].sort_values(
        "count",
        ascending=False,
    )


def moves_from_position(moves_df, pos_key):
    """What does the player usually play in this exact position?"""
    here = moves_df[
        (moves_df["pos_key"] == pos_key)
        & (moves_df["is_player"])
    ]

    return here["san"].value_counts()
