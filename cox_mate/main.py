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

prompt = """
This is an image from a Chambers of Xeric completion in Old School RuneScape.

Your job is to extract:
1. The current user's PERSONAL points.
2. The loot the current user received.

Important points rules:
- The points interface is in the top right.
- It contains a "Total:" row and a row for the current player beneath it.
- Use the CURRENT PLAYER'S personal points, not the total.

Important loot rules:
- First use the chat box text to identify loot whenever possible.
- If chat text clearly identifies an item, trust the chat.
- If chat text does not identify the loot, inspect the reward interface carefully.

Critical visual rule for purple detection:
- In the reward interface, ordinary stackable loot often has a quantity number shown above the item icon.
- Purple uniques should only be identified when the item icon itself clearly matches a known purple unique.
- Do NOT identify an item as a purple unique just because it is dark, red, blue, rectangular, or vaguely similar.
- Do NOT guess.
- If an item has a visible quantity number over it, treat it as ordinary loot unless the icon is unmistakably a known unique confirmed by the item art.
- If the icon is ambiguous, unknown, partially obscured, too small, or not clearly one of the listed uniques, do NOT call it a purple.

Very important:
- Individual reward items do NOT have numbers in the top-right corner of the item icon area unless they are stackable loot quantities.
- A visible quantity on the item strongly suggests normal loot, not a purple unique.
- If chat does not validate the item and the reward icon is not unmistakably one of the listed purple items, return no item for that slot.

Allowed special loot names:
- Twisted bow
- Kodai insignia
- Elder maul
- Ancestral hat
- Ancestral robe top
- Ancestral robe bottom
- Dinh's bulwark
- Dragon hunter crossbow
- Twisted buckler
- Dragon claws
- Arcane prayer scroll
- Dexterous prayer scroll

Purple identification guidance:
- Twisted bow: long green/white/black bow
- Kodai insignia: blue geometric insignia, not a dark blob, not a potion-like item
- Elder maul: large black maul
- Ancestral hat: wizard hat
- Ancestral robe top: robe torso
- Ancestral robe bottom: robe legs
- Dinh's bulwark: very large rectangular shield
- Dragon hunter crossbow: crossbow with dragon-head styling
- Twisted buckler: smaller green circular shield
- Dragon claws: a pair of large red claws, not arrows, not a dark relic, not a stackable item
- Arcane prayer scroll: pale scroll/paper
- Dexterous prayer scroll: darker scroll/paper

Decision order:
1. Read personal points from the top-right panel.
2. Check chat for explicit loot text.
3. If chat does not confirm loot, only identify a purple if the icon is unmistakable.
4. If not unmistakable, return no purple item.

Return ONLY valid JSON in this exact shape:
{
  "points": 64553,
  "items": []
}

or for identified items:
{
  "points": 64553,
  "items": [
    {"item_name": "Twisted bow", "quantity": 1}
  ]
}

Rules:
- "points" must be an integer.
- "items" must be an array of objects with keys "item_name" and "quantity".
- If loot is not confidently identifiable, return an empty items array.
- Confidence must be conservative.
- Do not include markdown fences.
- Do not include extra keys.
""".strip()

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
@click.argument("photos", type=click.Path(path_type=Path, exists=True, file_okay=False))
@click.argument("store", type=click.Path(path_type=Path), required=False)
@click.option("--api-key", default=os.getenv("GEMINI_API_KEY"), help="API key for Google Generative AI")
def cox_mate(photos: Path, store: Path | None, api_key: str) -> None:
    if not photos.exists():
        raise ValueError("You must define a directory of photos")

    if store and store.exists():
        df = pl.read_csv(
            store,
            try_parse_dates=True,
            schema_overrides=schema
        )
    else:
        df = pl.DataFrame(schema=schema)

    photos_in_dir = [png.name for png in photos.glob("*.png")]
    already_processed = set(df.get_column("file_name").to_list()) if "file_name" in df.columns else set()
    processable_photos = set(photos_in_dir) - already_processed

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

    for photo_name in sorted(processable_photos):
        image_path = photos / photo_name
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

        print(
            json.dumps(
                {
                    "file_name": photo_name,
                    "parsed_model_output": payload,
                    "stored_row": new_row,
                },
                indent=2,
                default=str,
            )
        )

    print(f"{len(processable_photos)} rows processed")

    if store:
        df.write_csv(store)