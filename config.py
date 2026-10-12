from pathlib import Path

HEADERS = {"User-Agent": "chess-scout project (your_email@example.com)"}
STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
RAW.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)