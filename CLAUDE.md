# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Cox Mate processes RuneLite "Boss Kills" screenshots from Chambers of Xeric (CoX) raids in Old School RuneScape. It uses the Gemini vision API to extract points and loot data from each screenshot, then stores the results in a CSV for tracking drops over time.

## Commands

```bash
# Install dependencies
poetry install

# Run the process command (scans a directory of screenshots and extracts data)
python -m cox_mate.main process <photos-directory> --api-key <key>

# Open the analysis notebook
poetry run jupyter notebook analysis.ipynb

# Run with env var for api key and photos dir (set GEMINI_API_KEY and PHOTOS_DIR in .env)
python -m cox_mate.main process

# Dry run (preview without writing)
python -m cox_mate.main process <photos-directory> --dry-run

# Print stats from the CSV
python -m cox_mate.main stats

# Run tests
poetry run pytest

# Lint
poetry run flake8 cox_mate/
poetry run black cox_mate/
poetry run isort cox_mate/
```

## Environment Variables (.env)

- `GEMINI_API_KEY` — Google Gemini API key (required unless passed via `--api-key`)
- `PHOTOS_DIR` — Default directory for screenshots (optional)
- `STORE_PATH` — Path to the CSV store file (defaults to `./data.csv`)

## Architecture

All logic lives in `cox_mate/main.py`. There is a single Click CLI group (`cli`) with two subcommands:

- **`process`** — Main pipeline: scans a directory for `*Chambers*.png` files, skips filenames already in the CSV, sends each new image to Gemini (`gemini-2.5-flash`) with `prompt.txt`, parses the structured JSON response, and appends rows to a Polars DataFrame which is written to CSV after each photo.

- **`stats`** — Reads the CSV and prints summary statistics (total raids, points, purple counts, most common loot).

### Key design details

- **`prompt.txt`** is read at module import time (not inside the command function). Editing this file changes the vision prompt without touching Python code. The prompt is carefully tuned to reduce false positives on purple unique detection.
- **Deduplication** is filename-based: `set(photos_in_dir) - already_processed`. Re-running the script on the same directory is safe.
- **`parse_photo_metadata`** extracts `date_completed`, `completion_count`, and `raid_type` (CM vs regular) from the RuneLite filename format: `Chambers of Xeric (Challenge Mode) (42) 2024-01-15_18-30-00.png`.
- The CSV schema (`schema` dict at module level) uses Polars dtypes. Both the DataFrame and new rows must be cast to this schema before concatenation to avoid type errors.
- Data is written to CSV incrementally after each photo, so partial runs are not lost on error.
