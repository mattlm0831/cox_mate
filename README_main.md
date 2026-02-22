# COX Mate - Main Driver

The main driver script for processing Chambers of Xeric screenshots and analyzing drops/points.

## Usage

### Basic Usage

```bash
# Process all new screenshots in a directory
poetry run python main.py /path/to/screenshots

# Process all files regardless of previous processing
poetry run python main.py /path/to/screenshots --force

# Use custom database file
poetry run python main.py /path/to/screenshots --db my_custom.db

# Increase logging detail
poetry run python main.py /path/to/screenshots --log-level DEBUG
```

### Quick Runner

For convenience, you can also use the simple runner:

```bash
poetry run python run_cox_mate.py /path/to/screenshots
```

## File Format Requirements

The script expects screenshot files with specific naming patterns:

### Regular Chambers of Xeric

```
Chambers of Xeric(kill_count) YYYY-MM-DD_HH-mm-ss.png
```

Example: `Chambers of Xeric(125) 2024-02-15_14-30-45.png`

### Challenge Mode

```
Chambers of Xeric Challenge Mode(kill_count) YYYY-MM-DD_HH-mm-ss.png
```

Example: `Chambers of Xeric Challenge Mode(67) 2024-02-16_09-15-22.png`

## What the Script Does

1. **File Discovery**: Scans the directory for PNG files containing "Chambers of Xeric"
2. **Filename Parsing**: Extracts raid type (regular/cm), kill count, and completion date
3. **Date Filtering**: Only processes files newer than the most recent entry (unless --force)
4. **User Confirmation**: Shows summary and asks for confirmation before processing
5. **VLM Analysis**: Uses vision-language model to analyze drops and points
6. **Database Storage**: Saves all raid data to SQLite database
7. **Statistics**: Shows comprehensive processing and raid statistics

## Processing Flow

```
Directory Input
      ↓
File Discovery (*.png with "Chambers")
      ↓
Filename Parsing (extract metadata)
      ↓
Date Filtering (skip already processed)
      ↓
User Confirmation Prompt
      ↓
VLM Analysis (drops + points)
      ↓
Database Storage
      ↓
Statistics Report
```

## Example Output

```
COX MATE PROCESSING SUMMARY
============================================================
Directory: /Users/player/screenshots
Total Chambers files found: 15
Files to process: 8
Most recent processed: 2024-02-10 15:30:22
Date range: 2024-02-11 08:15:33 to 2024-02-17 21:45:33
============================================================
Continue with processing? (y/N): y

Processing 8 files...
Processing 1/8: Chambers of Xeric(126) 2024-02-11_08-15-33.png
  ✅ Recorded raid 1: 28500 points, 3 items
Processing 2/8: Chambers of Xeric Challenge Mode(68) 2024-02-12_19-22-15.png
  🟣 Purple drop detected! Items: [{'item': 'Twisted bow', 'quantity': 1, 'confidence': 'high'}]
  ✅ Recorded raid 2: 35200 points, 1 items

============================================================
PROCESSING COMPLETE
============================================================
Files found: 15
Files processed: 8
Successful: 8
Failed: 0

📊 RAID STATISTICS:
  Regular raids: 6
  Challenge Mode raids: 2
  Purple drops: 1 (12.5%)
  Total points: 245,600
  Average points: 30,700
============================================================
```

## Testing

You can test the functionality without real screenshots:

```bash
# Test filename parsing
poetry run python test_parsing.py

# Demo file discovery and parsing
poetry run python demo.py

# Test with sample files
mkdir test_screenshots
touch "test_screenshots/Chambers of Xeric(125) 2024-02-15_14-30-45.png"
poetry run python demo.py
```

## Dependencies

- SQLAlchemy (database)
- PIL/Pillow (image processing)
- Qwen VL model (vision-language inference)
- All other dependencies in pyproject.toml
