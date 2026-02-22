"""
Qwen 2.5 VL Model Setup and Usage Example

This script demonstrates how to download and use Qwen 2.5 VL model
for vision-language tasks in your project.
"""

from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from PIL import Image
import torch

def download_qwen25_vl():
    """
    Downloads and loads the Qwen 2.5 VL model from Hugging Face.
    The model will be automatically downloaded on first use.
    """
    
    # Available model sizes:
    # - "Qwen/Qwen2-VL-2B-Instruct" (smaller, faster)
    # - "Qwen/Qwen2-VL-7B-Instruct" (larger, better performance)
    
    model_name = "Qwen/Qwen2-VL-2B-Instruct"  # Change to 7B if you have more resources
    
    print(f"Loading {model_name}...")
    print("This will download the model on first run (may take several minutes)")
    
    # Load the model and processor with numerical stability optimizations
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=torch.float32,  # Use float32 for numerical stability (especially on Mac/MPS)
        device_map="auto",  # Automatically choose device (GPU if available)
        attn_implementation="eager"  # Force eager attention to reduce buffer allocation
    )
    
    # Load processor with strict pixel budget to prevent memory explosion
    processor = AutoProcessor.from_pretrained(
        model_name,
        min_pixels=256 * 28 * 28,  # Conservative minimum
        max_pixels=768 * 28 * 28   # Cap max pixels to prevent 18GB buffer issue
    )
    
    print("Model loaded successfully!")
    return model, processor

def example_vision_language_inference(model, processor, image_path, question):
    """
    Example of using Qwen 2.5 VL for vision-language tasks.
    """
    
    # Load and downscale image to prevent vision token explosion
    image = Image.open(image_path)
    
    # Downscale to max 1024px on longest edge to reduce vision patches
    max_dim = 1024
    scale = max_dim / max(image.width, image.height)
    if scale < 1:
        new_size = (int(image.width * scale), int(image.height * scale))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        print(f"Resized image from {Image.open(image_path).size} to {image.size} for memory management")
    
    # Prepare the conversation format
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": question}
            ]
        }
    ]
    
    # Process the input with proper device handling
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=text, images=image, return_tensors="pt")
    
    # Ensure all inputs are on the same device for stability
    device = model.device
    for k, v in inputs.items():
        if hasattr(v, "to"):
            inputs[k] = v.to(device)
    
    # Force pixel_values to float32 for numerical stability
    if "pixel_values" in inputs:
        inputs["pixel_values"] = inputs["pixel_values"].to(dtype=torch.float32)
    
    # Set up generation config for stability
    model.generation_config.pad_token_id = processor.tokenizer.pad_token_id
    model.generation_config.eos_token_id = processor.tokenizer.eos_token_id
    
    # Generate response with deterministic decoding to avoid sampling instability
    with torch.no_grad():
        # Optional debug check for NaN/Inf logits
        try:
            debug_out = model(**inputs, return_dict=True)
            logits = debug_out.logits
            if torch.isnan(logits).any() or torch.isinf(logits).any():
                print("WARNING: Model produced NaN/Inf logits before sampling")
        except Exception as e:
            print(f"Debug logits check failed: {e}")
        
        # Use deterministic decoding to avoid probability tensor errors
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=128,  # Reduced from 512
            do_sample=False,     # Force deterministic (greedy) decoding
            num_beams=1,         # Single beam for stability
            temperature=None,    # Not used in greedy mode
            top_p=None          # Not used in greedy mode
        )
    
    # Decode the response
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    response = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    
    return response

if __name__ == "__main__":
    # Download and load the model
    model, processor = download_qwen25_vl()
    
    # Example usage (uncomment and provide an image path to test)
    # image_path = "path/to/your/image.jpg"
    # question = "What do you see in this image?"
    # response = example_vision_language_inference(model, processor, image_path, question)
    # print(f"Model response: {response}")
    
    print("\nModel is ready to use!")
    print("You can now use the model for vision-language tasks.")