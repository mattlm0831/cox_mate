# Qwen 2.5 VL Setup Guide

This guide will help you download and set up Qwen 2.5 VL for your project.

## Installation

1. **Install dependencies:**

```bash
# Install the project dependencies
pip install -e .

# Or install manually:
pip install transformers torch torchvision pillow accelerate sentencepiece
```

2. **Download the model:**

The model will be automatically downloaded when you first run the script. Choose from:

- **Qwen2-VL-2B-Instruct** (~4GB): Faster, less resource intensive
- **Qwen2-VL-7B-Instruct** (~14GB): Better performance, requires more resources

## Quick Start

```python
from cox_mate.models.qwen_vl_setup import download_qwen25_vl, example_vision_language_inference

# Load the model
model, processor = download_qwen25_vl()

# Use it with an image
response = example_vision_language_inference(
    model, processor,
    "path/to/image.jpg",
    "What do you see in this image?"
)
print(response)
```

## Alternative Download Methods

### Option 1: Manual Download from Hugging Face

```bash
# Using git lfs (requires git-lfs installed)
git lfs clone https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct
```

### Option 2: Using Hugging Face Hub

```python
from huggingface_hub import snapshot_download

# Download to specific directory
snapshot_download(
    repo_id="Qwen/Qwen2-VL-2B-Instruct",
    local_dir="./models/qwen2-vl-2b",
    local_dir_use_symlinks=False
)
```

### Option 3: Cache Location

Models are automatically cached in:

- **Linux/Mac**: `~/.cache/huggingface/hub/`
- **Windows**: `C:\Users\{username}\.cache\huggingface\hub\`

## Memory Requirements

- **2B Model**: ~4GB RAM/VRAM
- **7B Model**: ~14GB RAM/VRAM

For GPU acceleration, ensure you have CUDA installed and compatible PyTorch version.

## Model Capabilities

Qwen 2.5 VL can handle:

- Image understanding and description
- Visual question answering
- OCR (text extraction from images)
- Multi-turn conversations about images
- Chart and diagram analysis

## Example Use Cases for Your Project

```python
# Analyze game screenshots
response = example_vision_language_inference(
    model, processor,
    "game_screenshot.png",
    "What items can you see in this inventory?"
)

# Extract text from images
response = example_vision_language_inference(
    model, processor,
    "score_screenshot.png",
    "What are the points or scores shown in this image?"
)
```
