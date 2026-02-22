# Validation Images Directory

This directory contains validation screenshots for DSPy prompt optimization.

## Purpose

These images are used to:

- Test and optimize VLM prompts for better accuracy
- Validate COX drop and points recognition
- Benchmark performance improvements
- Train and fine-tune the analysis pipeline

## Required Images

Based on `validation_mapping.json`, you should provide the following screenshots:

### Purple Drops

- `cox_drop_twisted_bow.png` - Twisted bow drop
- `cox_drop_dragon_claws.png` - Dragon claws with regular loot
- `cox_cm_ancestral.png` - Challenge Mode ancestral hat
- `cox_elder_maul.png` - Elder maul drop

### Regular Drops

- `cox_no_drop.png` - No special drops, regular loot only
- `cox_multiple_drops.png` - Multiple items including prayer scrolls
- `cox_low_points.png` - Low points raid
- `cox_cm_high_points.png` - High points Challenge Mode

## Image Guidelines

### Quality Requirements

- Use actual game screenshots in PNG format
- Ensure clear visibility of the loot interface
- Include the points display in the screenshot
- Avoid cropped or edited images when possible

### Naming Convention

- Use descriptive names matching `validation_mapping.json`
- Include raid type prefix: `cox_` for regular, `cox_cm_` for Challenge Mode
- Indicate main drop: `cox_drop_twisted_bow.png`
- Use snake_case formatting

### Screenshot Composition

- Capture the entire loot interface
- Include points display clearly
- Show completion message if present
- Ensure good lighting/contrast

## Expected Results

Each image should have corresponding expected results in `validation_mapping.json`:

```json
{
	"image_path": "validation_images/cox_drop_twisted_bow.png",
	"expected_drops": [
		{
			"item": "Twisted bow",
			"quantity": 1,
			"confidence": "high"
		}
	],
	"expected_points": 35000,
	"raid_type": "regular"
}
```

## Usage

Run DSPy optimization with:

```bash
poetry run python optimize_prompt.py
```

This will:

1. Load validation images and expected results
2. Test current prompts against the validation set
3. Optimize prompts for better accuracy
4. Save improved prompts for use in production

## Adding New Validation Cases

1. Add the screenshot to this directory
2. Update `validation_mapping.json` with expected results
3. Run the optimization script to include in testing
4. Verify the expected results match actual game behavior

## Directory Structure

```
validation_images/
├── README.md
├── cox_drop_twisted_bow.png
├── cox_drop_dragon_claws.png
├── cox_cm_ancestral.png
├── cox_elder_maul.png
├── cox_no_drop.png
├── cox_multiple_drops.png
├── cox_low_points.png
└── cox_cm_high_points.png
```

## Notes

- Keep validation images private/local - don't commit to version control
- Use a diverse set of scenarios for robust testing
- Include edge cases (very low/high points, unusual loot combinations)
- Update expected results if game UI changes
- Consider different screen resolutions and UI scaling
