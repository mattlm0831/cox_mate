"""
Visual Item Recognition System for COX Drops
Handles multi-image input for better visual reference matching
"""

import json
import torch
from typing import List, Dict, Any, Optional
from PIL import Image
from cox_mate.models.qwen_vl_setup import download_qwen25_vl
from cox_mate.prompts import chambers_drop_recognition_prompt, create_item_reference_list

class VisualItemRecognizer:
    def __init__(self):
        self.model = None
        self.processor = None
        self.item_reference_images = {}  # Will store reference images
    
    def load_model(self):
        """Load the Qwen VL model (cached after first load)"""
        if self.model is None:
            print("Loading Qwen 2.5 VL model...")
            self.model, self.processor = download_qwen25_vl()
            print("Model loaded and ready!")
    
    def load_item_references(self, reference_dir: str):
        """
        Load reference images for COX items
        
        Expected structure:
        reference_dir/
            twisted_bow.png
            elder_maul.png
            dragon_claws.png
            teak_plank.png
            etc.
        """
        import os
        from cox_mate.prompts import COX_ITEMS
        
        if not os.path.exists(reference_dir):
            print(f"Warning: Reference directory {reference_dir} not found")
            return
        
        loaded_count = 0
        for item_name in COX_ITEMS.keys():
            # Convert item name to filename (replace spaces with underscores, lowercase)
            filename = item_name.lower().replace(" ", "_").replace("'", "") + ".png"
            filepath = os.path.join(reference_dir, filename)
            
            if os.path.exists(filepath):
                try:
                    self.item_reference_images[item_name] = Image.open(filepath)
                    loaded_count += 1
                except Exception as e:
                    print(f"Error loading {filepath}: {e}")
        
        print(f"Loaded {loaded_count} reference images out of {len(COX_ITEMS)} possible items")
    
    def analyze_with_references(self, loot_screenshot_path: str, use_reference_images: bool = True) -> Dict[str, Any]:
        """
        Analyze loot screenshot with optional visual references
        
        Args:
            loot_screenshot_path: Path to the loot interface screenshot
            use_reference_images: Whether to include reference images in context
            
        Returns:
            Dict with identified items and metadata
        """
        self.load_model()
        
        # Prepare the prompt with item list
        item_reference = create_item_reference_list()
        full_prompt = chambers_drop_recognition_prompt.format(item_reference=item_reference)
        
        if use_reference_images and self.item_reference_images:
            # Multi-image approach: include reference images
            response = self._analyze_with_visual_references(loot_screenshot_path, full_prompt)
        else:
            # Single image approach: text-only references
            response = self._analyze_single_image(loot_screenshot_path, full_prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"Failed to parse VLM response: {response}")
            return {
                "drops": [],
                "interface_detected": False,
                "total_items_visible": 0,
                "notes": "Failed to parse response"
            }
    
    def _analyze_single_image(self, image_path: str, prompt: str) -> str:
        """Analyze using single image (loot screenshot only)"""
        image = Image.open(image_path)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=text, images=image, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=512)
        
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        response = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]
        
        return response
    
    def _analyze_with_visual_references(self, loot_screenshot_path: str, prompt: str) -> str:
        """Analyze using multiple images (loot + reference images)"""
        # Load main loot screenshot
        loot_image = Image.open(loot_screenshot_path)
        
        # Create enhanced prompt with reference context
        enhanced_prompt = prompt + "\n\nREFERENCE IMAGES PROVIDED:\n"
        enhanced_prompt += "Compare the loot interface icons with these reference images to make accurate identifications.\n"
        
        # Prepare images list (loot screenshot + reference images)
        images = [loot_image]
        for item_name, ref_image in list(self.item_reference_images.items())[:10]:  # Limit to prevent context overflow
            images.append(ref_image)
            enhanced_prompt += f"- {item_name} reference image included\n"
        
        messages = [
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": enhanced_prompt}
                ] + [{"type": "image", "image": img} for img in images]
            }
        ]
        
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=text, images=images, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=512)
        
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        response = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]
        
        return response

# Usage example
if __name__ == "__main__":
    recognizer = VisualItemRecognizer()
    
    # Load reference images (optional but recommended)
    # recognizer.load_item_references("./reference_images/cox_items/")
    
    # Analyze a loot screenshot
    result = recognizer.analyze_with_references(
        "path/to/loot_screenshot.png", 
        use_reference_images=True
    )
    
    print(f"Found {len(result['drops'])} items:")
    for drop in result['drops']:
        print(f"- {drop['item']} x{drop['quantity']} (confidence: {drop['confidence']})")


def multi_image_vision_language_inference(
    model, processor, main_image_path: str, reference_images: List[str], 
    prompt_text: str, max_tokens: int = 2000
) -> str:
    """
    Run vision-language model inference with multiple images (main + references)
    
    Args:
        model: The loaded VLM model
        processor: The model's processor
        main_image_path: Path to the main screenshot to analyze
        reference_images: List of paths to reference icon images
        prompt_text: The text prompt
        max_tokens: Maximum tokens to generate
    
    Returns:
        Model's text response
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Load main image and resize to reduce memory
        main_image = Image.open(main_image_path).convert('RGB')
        
        # Load ALL reference images with aggressive size reduction
        ref_images = []
        for ref_path in reference_images:
            if Path(ref_path).exists():
                ref_img = Image.open(ref_path).convert('RGB')
                # Very small reference icons to minimize memory usage
                ref_img.thumbnail((48, 48), Image.Resampling.LANCZOS)
                ref_images.append(ref_img)
        
        # Resize main image more aggressively to accommodate all reference images
        if main_image.width > 600 or main_image.height > 450:
            main_image.thumbnail((600, 450), Image.Resampling.LANCZOS)
        
        # Combine all images (main first, then references)
        all_images = [main_image] + ref_images
        
        logger.info(f"Processing {len(all_images)} images (1 main + {len(ref_images)} icons)")
        
        # Create multi-image prompt
        multi_prompt = f"""Main Screenshot (analyze this):
[IMAGE 1]

Reference Icons for comparison (all {len(ref_images)} COX items):
{chr(10).join([f'[IMAGE {i+2}] - Reference icon {i+1}' for i in range(len(ref_images))])}

{prompt_text}"""
        
        # Process inputs
        inputs = processor(
            text=multi_prompt,
            images=all_images,
            return_tensors="pt",
            padding=True
        )
        
        # Move to device if available
        device = next(model.parameters()).device
        inputs = {k: v.to(device) if torch.is_tensor(v) else v for k, v in inputs.items()}
        
        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                temperature=0.1
            )
        
        # Decode response
        response = processor.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the generated part (after the prompt)
        if multi_prompt in response:
            response = response.split(multi_prompt)[-1].strip()
        
        return response
        
    except Exception as e:
        logger.error(f"Multi-image VLM inference failed: {e}")
        return f'{{"error": "Failed to process images: {str(e)}"}}'