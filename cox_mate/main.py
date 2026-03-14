import click
import json
import os
import re
from datetime import date, datetime
from enum import Enum
from pathlib import Path

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
    "purple": dt.Utf8,
    "items_json": dt.Utf8,
    "completion_count": dt.Int64,
    "raid_type": dt.Categorical,
}


PURPLE_ITEMS = {
    "Twisted bow",
    "Kodai insignia",
    "Elder maul",
    "Ancestral hat",
    "Ancestral robe top",
    "Ancestral robe bottom",
    "Dinh's bulwark",
    "Dragon hunter crossbow",
    "Twisted buckler",
    "Dragon claws",
    "Arcane prayer scroll",
    "Dexterous prayer scroll",
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


def normalize_items(items: list[dict] | None) -> dict[str, int]:
    if not items:
        return {}

    normalized: dict[str, int] = {}

    for entry in items:
        if not entry:
            continue

        item_name = str(entry["item_name"]).strip()
        quantity = int(entry["quantity"])

        normalized[item_name] = normalized.get(item_name, 0) + quantity

    return normalized


def extract_purple(items: dict[str, int]) -> str | None:
    found = [item for item in items if item in PURPLE_ITEMS]
    if not found:
        return None
    if len(found) == 1:
        return found[0]
    return ", ".join(sorted(found))


@click.command("cox_mate")
@click.argument("photos_dir", type=click.Path(path_type=Path, exists=True, file_okay=False))
@click.option("--store", default="./data.csv", help="Path to the CSV file for storing data. Defaults to ./data.csv.")
@click.option("--api-key", default=os.getenv("GEMINI_API_KEY"), help="API key for Google Generative AI")
@click.option("--dry-run", is_flag=True, help="Process photos_dir without saving results")
def cox_mate(photos_dir: Path, store: str, api_key: str, dry_run: bool) -> None:
    if not photos_dir.exists():
        raise ValueError("You must define a directory of photos")

    store_path = Path(store)

    if store_path.exists():
        df = pl.read_csv(store_path)
    else:
        df = pl.DataFrame(schema=schema)
        df.write_csv(store_path)

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
            "items": {
                "type": "array",
                "description": "Loot received by the current user.",
                "items": {
                    "type": "object",
                    "properties": {
                        "item_name": {"type": "string"},
                        "quantity": {"type": "integer"},
                    },
                    "required": ["item_name", "quantity"],
                },
            },
        },
        "required": ["points", "items"],
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
        items = normalize_items(payload.get("items"))
        purple = extract_purple(items)
        items_json = json.dumps(items, sort_keys=True)

        new_row = {
            "file_name": photo_name,
            "points": int(payload["points"]),
            "date_completed": file_meta["date_completed"],
            "date_processed": date.today(),
            "purple": purple,
            "items_json": items_json,
            "completion_count": file_meta["completion_count"],
            "raid_type": file_meta["raid_type"],
        }

        row_df = pl.DataFrame([new_row]).cast(schema)
        df = pl.concat([df, row_df], how="vertical")

        print(f"Processed {photo_name}: {payload['points']} points, purple: {purple}, items: {items_json}")
        print(f"Processed photo {i + 1} / {len(processable_photos)}")

        if store:
            df.write_csv(store)

    print(f"{len(processable_photos)} rows processed")
