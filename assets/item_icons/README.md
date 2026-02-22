
# Item Icons Directory

This directory contains reference images for Chambers of Xeric items.

## Structure

- `icon_mapping.json` - Maps icon filenames to item names
- Individual PNG/JPG files for each item icon

## Adding New Icons

1. Save the item icon as a PNG or JPG file with a descriptive name (e.g., `twisted_bow.png`)
2. Update `icon_mapping.json` to map the filename to the correct item name
3. Use the ItemIconManager to validate the mapping

## Icon Guidelines

- Use clear, high-quality icons extracted from the game
- Prefer PNG format for transparency support
- Use snake_case filenames (e.g., `dragon_claws.png`)
- Include multiple variants if items have different appearances

## Example icon_mapping.json

```json
{
  "twisted_bow.png": "Twisted bow",
  "dragon_claws.png": "Dragon claws",
  "ancestral_hat.png": "Ancestral hat"
}
```
