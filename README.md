#Chess Scout:

Project that takes the data of any player on Chess.com and analyzes: opening plays, where they blunder, and other factors:

## Example Report:

# Scouting report: adr_mog

Games analysed: 47 | Overall score: 50%

## What stands out (vs. similar-rated players)

- Blunders in endgames MORE than typical (+1.8 SD)
- Gets into time trouble MORE than typical (+1.7 SD)
- Varies their openings MORE than typical (+1.1 SD)

## Openings

- As Black vs 1.e4: e5 88%, e6 6%, f5 6%
- As Black vs 1.d4: d5 67%, f5 33%
- Weakest opening: Kings Pawn Opening 1...e5 as black (smoothed score 46% over 3 games)

## To run:

pip install -r requirements.txt
python scout.py <username> [rapid|blitz]

Requires Stockfish ("brew install stockfish" on terminal) and its path set in config.py (per your own computer path way)
