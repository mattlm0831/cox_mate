import click
import json
import os
import re
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
import polars as pl
from polars import datatypes as dt
from google import genai
from google.genai import types


class RaidType(Enum):
    CM = "cm"
    REGULAR = "regular"

with open('prompt.txt', 'r+') as f:
    prompt = f.read().strip()

schema = {
    "file_name": dt.Utf8,
    "points": dt.Int64,
    "date_completed": dt.Date,
    "date_processed": dt.Date,
    "completion_count": dt.Int64,
    "raid_type": dt.Categorical,
}


def parse_photo_metadata(file_name: str) -> dict:
    stem = Path(file_name).stem

    date_match = re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})$", stem)
    if not date_match:
        raise ValueError(f"Could not parse completion date from filename: {file_name}")

    completed_dt = datetime.strptime(
        f"{date_match.group(1)} {date_match.group(2).replace('-', ':')}",
        "%Y-%m-%d %H:%M:%S",
    )

    cc_match = re.search(r"\((\d+)\)", stem)
    if not cc_match:
        raise ValueError(f"Could not parse completion count from filename: {file_name}")

    lowered = stem.lower()
    raid_type = RaidType.CM.value if "challenge mode" in lowered else RaidType.REGULAR.value

    return {
        "date_completed": completed_dt.date(),
        "completion_count": int(cc_match.group(1)),
        "raid_type": raid_type,
    }



@click.group()
def cli():
    """COX Mate CLI: process images and view stats."""
    pass

@cli.command("process")
@click.argument("photos_dir", type=click.Path(path_type=Path, exists=True, file_okay=False), default=Path(os.getenv("PHOTOS_DIR", '')), nargs=1)
@click.option("--store", default=os.getenv('STORE_PATH', './data.csv'), help="Path to the CSV file for storing data. Defaults to ./data.csv.")
@click.option("--api-key", default=os.getenv("GEMINI_API_KEY"), help="API key for Google Generative AI")
@click.option("--dry-run", is_flag=True, help="Process photos_dir without saving results")
def process(photos_dir: Path, store: str, api_key: str, dry_run: bool) -> None:
    if not photos_dir or not photos_dir.exists():
        raise ValueError("You must define a directory of photos")

    store_path = Path(store).expanduser().resolve()
    print(f"[INFO] Using store path: {store_path}")

    if store and store_path.exists():
        df = pl.read_csv(str(store_path), separator=",", encoding="utf8")
        print("Existing data file found, loaded into DataFrame.")
    elif store:
        raise ValueError(f"No data file found at {store_path}, please create an empty CSV with the correct schema or run without the store argument")
    else:
        df = pl.DataFrame(schema=schema)
        print("No existing data file found, starting with an empty DataFrame.")

    photos_in_dir = [png.name for png in photos_dir.glob("*Chambers*.png")]
    already_processed = set(df.get_column("file_name").to_list()) if "file_name" in df.columns else set()

    processable_photos = set(photos_in_dir) - already_processed
    if dry_run:
        print(f"Found {len(photos_in_dir)} photos in directory, sample: {photos_in_dir[:5]}")
        print(f"{len(already_processed)} already processed photos, would have processed {len(processable_photos)} new photos")
        return

    client = genai.Client(api_key=api_key)

    response_schema = {
        "type": "object",
        "properties": {
            "points": {
                "type": "integer",
                "description": "The personal points for the current user, not the total team points.",
            },
        },
        "required": ["points"],
    }

    for i, photo_name in enumerate(processable_photos):
        image_path = photos_dir / photo_name
        file_meta = parse_photo_metadata(photo_name)

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_text(text=prompt),
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            ],
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )

        payload = json.loads(response.text)

        new_row = {
            "file_name": photo_name,
            "points": int(payload["points"]),
            "date_completed": file_meta["date_completed"],
            "date_processed": date.today(),
            "completion_count": file_meta["completion_count"],
            "raid_type": file_meta["raid_type"],
        }

        row_df = pl.DataFrame([new_row]).cast(schema)
        # Ensure both date_completed and date_processed columns are the same type in both DataFrames
        df = df.with_columns([
            pl.col("date_completed").cast(pl.Date),
            pl.col("date_processed").cast(pl.Date),
            pl.col("raid_type").cast(pl.Categorical)
        ])
        row_df = row_df.with_columns([
            pl.col("date_completed").cast(pl.Date),
            pl.col("date_processed").cast(pl.Date),
            pl.col("raid_type").cast(pl.Categorical)
        ])
        df = pl.concat([df, row_df], how="vertical")

        print(f"Processed {photo_name}: {payload['points']} points")
        print(f"Processed photo {i + 1} / {len(processable_photos)}")


        if store:
            try:
                df.write_csv(str(store_path))
                print(f"[INFO] DataFrame written to {store_path}")
            except Exception as e:
                print(f"[ERROR] Failed to write DataFrame to {store_path}: {e}")

    print(f"{len(processable_photos)} rows processed")

@cli.command("stats")
@click.option("--store", default=os.getenv('STORE_PATH', './data.csv'), help="Path to the CSV file for storing data. Defaults to ./data.csv.")
def stats(store: str):
    """Print rough statistics from the data store CSV."""
    store_path = Path(store).expanduser().resolve()
    print(f"[INFO] Using store path: {store_path}")
    if not store_path.exists():
        print(f"No data file found at {store_path}")
        return
    df = pl.read_csv(str(store_path), separator=",", encoding="utf8")
    print(f"Loaded {len(df)} rows from {store_path}")
    total_raids = len(df)
    total_points = df["points"].sum()
    avg_points = df["points"].mean()
    print(f"Total raids: {total_raids:,}")
    print(f"Total points: {total_points:,}")
    print(f"Average points per raid: {avg_points:,.2f}")