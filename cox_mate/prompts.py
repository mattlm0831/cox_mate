
"""
Prompts for Chambers of Xeric (COX) drop and score recognition
"""

# All possible COX drops with simplified purple/common classification
COX_ITEMS = {
    # Purple drops (the ones that matter!)
    "Twisted bow": {"is_purple": True},
    "Elder maul": {"is_purple": True},
    "Kodai insignia": {"is_purple": True},
    "Dragon claws": {"is_purple": True},
    "Ancestral hat": {"is_purple": True},
    "Ancestral robe top": {"is_purple": True},
    "Ancestral robe bottom": {"is_purple": True},
    "Dragon hunter crossbow": {"is_purple": True},
    "Dinh's bulwark": {"is_purple": True},
    "Twisted buckler": {"is_purple": True},
    
    # Prayer scrolls (purple drops from CM)
    "Dexterous prayer scroll": {"is_purple": True},
    "Arcane prayer scroll": {"is_purple": True},
    
    # Pets (purple drops)
    "Olmlet": {"is_purple": False},

    # Twisted kit
    "Twisted ancestral colour kit": {'is_purple': False},
    
    # Metamorphic dust (for pet recoloring)
    "Metamorphic dust": {"is_purple": False},
    
    # Common drops (only included for context, but focus is on purples)
    "Teak plank": {"is_purple": False},
    "Mahogany plank": {"is_purple": False},
    "Dynamite": {"is_purple": False},
    "Dark relic": {"is_purple": False},
    "Soul rune": {'is_purple': False},
    "Blood rune": {'is_purple': False},
    "Death rune": {'is_purple': False},
    "Rune arrow": {'is_purple': False},
    "Dragon Arrow": {'is_purple': False},
    "Runite ore": {'is_purple': False},
    "Adamantite ore": {'is_purple': False},
}

def create_item_reference_list():
    """Create a formatted list of all possible COX items for the VLM"""
    purple_items = []
    common_items = []
    
    for item_name, item_info in COX_ITEMS.items():
        if item_info["is_purple"]:
            purple_items.append(item_name)
        else:
            common_items.append(item_name)
    
    context = "POSSIBLE COX DROPS TO LOOK FOR:\n\n"
    context += "🟣 RARE DROPS (THESE ARE WHAT MATTER!): " + ", ".join(purple_items) + "\n\n"
    context += "⚪ Common drops (for reference): " + ", ".join(common_items) + "\n\n"
    context += "NOTE: Visual reference icons will be provided alongside this prompt for accurate identification.\n"
    
    return context

def get_icon_reference_images():
    """Get list of icon image paths for visual reference"""
    from pathlib import Path
    from .item_icons import ItemIconManager
    
    icon_manager = ItemIconManager()
    icon_paths = []
    
    # Get icon paths for all COX items
    for item_name in COX_ITEMS.keys():
        icon_path = icon_manager.get_icon_path(item_name)
        if icon_path and icon_path.exists():
            icon_paths.append({
                "item_name": item_name,
                "icon_path": str(icon_path),
                "is_purple": COX_ITEMS[item_name]["is_purple"]
            })
    
    return icon_paths

chambers_drop_recognition_prompt = """
You are an expert at identifying OSRS item icons from Chambers of Xeric loot interfaces.

{item_reference}

VISUAL REFERENCE: You are provided with reference images of all possible COX item icons alongside this prompt. Use these reference images to accurately identify items in the loot interface.

VISUAL INTERFACE GUIDE:
- The LOOT INTERFACE appears in the CENTER/MIDDLE of the screen after completing a raid
- Focus ONLY on the central loot interface - ignore player inventory on the right side
- Items appear as small square icons in a grid layout within this central interface
- Quantity numbers appear in YELLOW text in the TOP-LEFT corner of icons
- No number = quantity of 1

IMPORTANT: Only analyze items in the central loot interface, NOT the player's inventory!

TASK: Analyze this loot interface screenshot and identify visible item icons in the central loot window by comparing them to the provided reference icons.

PRIORITY FOCUS:
1. 🟣 RARE DROPS (is_purple: true) - These are the most important! Check the reference list above.
2. Common drops can be noted but rare drops are the main priority

INSTRUCTIONS:
1. Focus exclusively on the central loot interface (ignore inventory on the right)
2. Scan the central loot interface systematically
3. Compare each visible icon to the provided reference images
4. Look for yellow quantity numbers in the top-left corner of each icon
5. Only report items you can clearly match to the reference icons
6. If an icon is unclear or doesn't match any reference, skip it rather than guess
7. Check if identified items match the rare drop list (is_purple: true)

RESPONSE FORMAT (MUST BE VALID JSON):
You MUST respond with ONLY valid JSON - no additional text before or after. Format:
{{
  "drops": [
    {{"item": "Twisted bow", "quantity": 1, "confidence": "high", "is_purple": true}},
    {{"item": "Teak plank", "quantity": 15, "confidence": "medium", "is_purple": false}}
  ],
  "interface_detected": true,
  "rare_drops_found": 0,
  "total_items_visible": 0,
  "notes": "any additional observations"
}}

IMPORTANT: Return ONLY the JSON object, no markdown formatting, no explanations, no additional text.

Remember: Use the provided reference icon images for accurate identification. Only analyze the central loot interface, and rare drops (is_purple: true) are what matter most!
"""

chambers_score_prompt = """
You are being tasked with extracting very important information out of a video game screenshot.
Users are completely unaware of how many points they have in the chambers of xeric, and you
are the only thing that can help them!

TASK: Extract the player's current points from this Chambers of Xeric interface.

POINTS LOCATION GUIDE:
- Points display is typically in the TOP-RIGHT area of the interface, but may appear elsewhere
- Look for text that says "Total" followed by a player name
- The points you want are the number UNDER the "Total" text
- Points are usually displayed as a number with commas (e.g., "66,241")

INSTRUCTIONS:
1. Scan the interface for "Total" text (usually top-right but not always)
2. Find the player name that appears after "Total"
3. Look for the points number directly below the "Total" line, it looks like {player_name}: {points}
4. Extract the numerical value (ignore any formatting like commas)

RESPONSE FORMAT (MUST BE VALID JSON):
You MUST respond with ONLY valid JSON - no additional text before or after. Format:
{{
  "points": 0,
  "confidence": "high",
  "points_text_found": "exact text seen in image"
}}

IMPORTANT: Return ONLY the JSON object, no markdown formatting, no explanations, no additional text.
If no "Total" or points are visible, set points to 0 and confidence to "low".
"""