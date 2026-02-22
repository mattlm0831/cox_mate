"""
Item icons management for visual recognition
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ItemIconManager:
    """Manages item icon references for visual recognition"""
    
    def __init__(self, icons_dir: str = "assets/item_icons"):
        self.icons_dir = Path(icons_dir)
        # No need for icon mapping - we use naming convention
    
    def get_icon_filename(self, item_name: str) -> str:
        """Convert item name to expected icon filename"""
        return item_name.lower().replace(' ', '_') + '.png'
    
    def get_icon_path(self, item_name: str) -> Optional[Path]:
        """Get full path to icon file for an item"""
        icon_filename = self.get_icon_filename(item_name)
        icon_path = self.icons_dir / icon_filename
        return icon_path if icon_path.exists() else None
    
    def get_item_name(self, icon_filename: str) -> str:
        """Convert icon filename back to item name"""
        # Remove .png extension and convert back to title case
        base_name = icon_filename.replace('.png', '').replace('_', ' ')
        return base_name.title()
    
    def get_available_icons(self) -> List[str]:
        """Get list of available icon files in the directory"""
        if not self.icons_dir.exists():
            return []
        
        icon_files = []
        for file_path in self.icons_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                icon_files.append(file_path.name)
        
        return sorted(icon_files)
    
    def validate_icons(self) -> Dict[str, List[str]]:
        """Validate that expected icons exist and report issues"""
        from cox_mate.prompts import COX_ITEMS
        
        available_icons = set(self.get_available_icons())
        expected_icons = set()
        
        # Generate expected icon filenames from COX_ITEMS
        for item_name in COX_ITEMS.keys():
            expected_filename = self.get_icon_filename(item_name)
            expected_icons.add(expected_filename)
        
        missing_files = expected_icons - available_icons
        extra_files = available_icons - expected_icons
        valid_icons = expected_icons & available_icons
        
        return {
            "missing_files": list(missing_files),
            "extra_files": list(extra_files),
            "valid_icons": list(valid_icons)
        }
    
    def load_icon_image(self, item_name: str) -> Optional[Image.Image]:
        """Load an icon image file for the given item name"""
        icon_filename = self.get_icon_filename(item_name)
        icon_path = self.icons_dir / icon_filename
        
        if not icon_path.exists():
            logger.warning(f"Icon file not found: {icon_path}")
            return None
        
        try:
            return Image.open(icon_path)
        except Exception as e:
            logger.error(f"Failed to load icon {icon_path}: {e}")
            return None
    
    def create_icon_reference_prompt(self) -> str:
        """Create a prompt section describing available icons for VLM"""
        from cox_mate.prompts import COX_ITEMS
        
        validation_result = self.validate_icons()
        valid_icons = validation_result["valid_icons"]
        
        if not valid_icons:
            return "No valid item icons available for reference."
        
        icon_descriptions = []
        for icon_filename in valid_icons:
            item_name = self.get_item_name(icon_filename)
            is_purple = COX_ITEMS.get(item_name, {}).get('is_purple', False)
            purple_indicator = "🟣" if is_purple else "⚪"
            icon_descriptions.append(f"- {purple_indicator} {item_name} (icon: {icon_filename})")
        
        prompt = f"""
Available item reference icons ({len(valid_icons)} items):
{chr(10).join(icon_descriptions)}

When analyzing screenshots, compare detected items against these known icons for accurate identification.
"""
        
        return prompt


def setup_item_icons_directory():
    """Initialize the item icons directory with README"""
    icons_dir = Path("assets/item_icons")
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    readme_path = icons_dir / "README.md"
    if not readme_path.exists():
        readme_content = """
# Item Icons Directory

This directory contains reference images for Chambers of Xeric items.

## Naming Convention

Icon files should follow the naming convention:
- Convert item name to lowercase
- Replace spaces with underscores
- Add .png extension

Examples:
- "Twisted bow" → `twisted_bow.png`
- "Dragon claws" → `dragon_claws.png`
- "Ancestral hat" → `ancestral_hat.png`

## Adding New Icons

1. Save the item icon as a PNG file using the naming convention
2. No mapping file needed - the system automatically detects icons

## Icon Guidelines

- Use clear, high-quality icons extracted from the game
- Prefer PNG format for transparency support
- Follow the exact naming convention for automatic detection

## Purple vs Common Items

The system automatically knows which items are purple (rare) based on the COX_ITEMS dictionary in prompts.py.
Focus on purple items as they are the most valuable to track.
"""
        
        with open(readme_path, 'w') as f:
            f.write(readme_content)
    
    # Initialize the icon manager
    manager = ItemIconManager(str(icons_dir))
    
    return manager


if __name__ == "__main__":
    # Initialize the icons directory
    manager = setup_item_icons_directory()
    
    # Show validation results
    validation = manager.validate_icons()
    print(f"Icon validation results:")
    print(f"  Valid icons: {len(validation['valid_icons'])}")
    print(f"  Missing files: {len(validation['missing_files'])}")
    print(f"  Extra files: {len(validation['extra_files'])}")
    
    if validation['missing_files']:
        print(f"\nMissing icon files (use naming convention):")
        for f in validation['missing_files']:
            print(f"  - {f}")
    
    if validation['extra_files']:
        print(f"\nExtra icon files (not in COX_ITEMS):")
        for f in validation['extra_files']:
            print(f"  - {f}")
    
    # Show naming convention examples
    print(f"\nNaming convention examples:")
    from cox_mate.prompts import COX_ITEMS
    purple_items = [name for name, info in COX_ITEMS.items() if info['is_purple']]
    for item in purple_items[:5]:
        filename = manager.get_icon_filename(item)
        print(f"  '{item}' → {filename}")
