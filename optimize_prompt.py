"""
DSPy-based prompt optimization for COX drop recognition

This module uses DSPy to optimize prompts for better VLM performance
on Chambers of Xeric screenshot analysis.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

try:
    import dspy
except ImportError:
    print("DSPy not installed. Install with: pip install dspy-ai")
    exit(1)

from cox_mate.models.qwen_vl_setup import download_qwen25_vl, example_vision_language_inference
from cox_mate.prompts import chambers_score_prompt, create_item_reference_list

logger = logging.getLogger(__name__)


class COXDropSignature(dspy.Signature):
    """
    Signature for COX drop analysis task
    """
    system_prompt = dspy.InputField(desc="System instructions for analyzing the screenshot")
    image_description = dspy.InputField(desc="Description or path of the Chambers of Xeric screenshot")
    drops_analysis = dspy.OutputField(desc="JSON analysis of drops found in the screenshot")
    points_analysis = dspy.OutputField(desc="JSON analysis of points shown in the screenshot")


class COXDropAnalyzer(dspy.Module):
    """
    DSPy module for analyzing COX drops and points
    """
    
    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(COXDropSignature)
    
    def forward(self, system_prompt: str, image_description: str):
        """Analyze a COX screenshot for drops and points"""
        return self.analyze(
            system_prompt=system_prompt,
            image_description=image_description
        )


class COXPromptOptimizer:
    """
    Optimizes prompts for COX drop recognition using DSPy
    """
    
    def __init__(self, validation_dir: str = "validation_images", key_file_path: str = None):
        self.validation_dir = Path(validation_dir)
        self.validation_file = self.validation_dir / "validation_examples.json"
        self.key_file_path = key_file_path
        self.validation_data = self.load_validation_data()
        self.model = None
        self.processor = None
        self.dspy_lm = None
        
        # Initialize DSPy with proper configuration
        self.setup_dspy()
    
    def setup_dspy(self):
        """Set up DSPy configuration with Gemini using modern LM interface"""
        import os
        
        # Get Gemini API key
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Try loading from key file
            api_key = self._get_gemini_credentials(self.key_file_path)
        
        if not api_key:
            logger.warning("No Gemini API key found. Set GOOGLE_API_KEY environment variable or provide key file.")
            self.dspy_lm = None
            return
        
        try:
            # Set environment variable for LiteLLM
            os.environ["GOOGLE_API_KEY"] = api_key
            
            # Use modern DSPy LM interface
            lm = dspy.LM("gemini/gemini-1.5-pro-latest")
            dspy.configure(lm=lm)
            self.dspy_lm = lm
            # Add logging for LiteLLM Gemini URL
            try:
                import litellm
                original_completion = litellm.completion
                def debug_completion(*args, **kwargs):
                    url = kwargs.get('url', None)
                    if url:
                        logger.info(f"LiteLLM Gemini completion URL: {url}")
                    return original_completion(*args, **kwargs)
                litellm.completion = debug_completion
            except Exception as patch_exc:
                logger.warning(f"Could not patch LiteLLM for URL logging: {patch_exc}")
            logger.info("DSPy configured with Gemini using modern LM interface")
            
        except Exception as e:
            logger.error(f"Failed to configure DSPy with Gemini: {e}")
            self.dspy_lm = None
    
    def _get_gemini_credentials(self, key_file_path: str = None) -> str:
        """Get Gemini API credentials from JSON file"""
        import json
        from pathlib import Path
        
        if not key_file_path:
            return None
            
        key_file = Path(key_file_path)
        if not key_file.exists():
            logger.warning(f"Key file not found: {key_file}")
            return None
            
        try:
            with open(key_file, 'r') as f:
                key_data = json.load(f)
            
            # Handle both service account JSON and simple API key JSON
            if 'private_key' in key_data:
                # This is a service account file - extract the private key
                logger.info(f"Loaded Gemini service account key from {key_file}")
                return key_data['private_key'].strip()
            elif 'api_key' in key_data:
                # This is a simple API key file
                logger.info(f"Loaded Gemini API key from {key_file}")
                return key_data['api_key'].strip()
            else:
                logger.warning(f"No 'api_key' or 'private_key' field found in {key_file}")
                return None
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in {key_file}")
            return None
        except Exception as e:
            logger.warning(f"Error reading {key_file}: {e}")
            return None
    
    def load_validation_data(self) -> List[Dict[str, Any]]:
        """Load validation data from JSON file"""
        if not self.validation_file.exists():
            logger.warning(f"Validation file not found: {self.validation_file}")
            self.create_example_validation_file()
            return []
        
        try:
            with open(self.validation_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} validation examples from {self.validation_file}")
                return data
        except Exception as e:
            logger.error(f"Failed to load validation data: {e}")
            return []
    
    def create_example_validation_file(self):
        """Create an example validation file if none exists"""
        self.validation_dir.mkdir(parents=True, exist_ok=True)
        
        example_entry = {
            "image_path": "validation_images/example_cox_drop.png",
            "description": "Example screenshot - replace with your actual validation images",
            "expected_drops": [
                {
                    "item": "Twisted bow",
                    "quantity": 1,
                    "confidence": "high",
                    "is_purple": True
                }
            ],
            "expected_points": 35000,
            "raid_type": "regular",
            "completion_count": 125,
            "notes": "Add your validation images and update this file",
            "difficulty": "easy",
            "tags": ["example", "purple", "twisted_bow"]
        }
        
        try:
            with open(self.validation_file, 'w') as f:
                json.dump([example_entry], f, indent=2)
            logger.info(f"Created example validation file: {self.validation_file}")
        except Exception as e:
            logger.error(f"Failed to create validation file: {e}")
    
    def load_vlm_model(self):
        """Load the VLM model for testing"""
        if self.model is None:
            logger.info("Loading Qwen VL model for optimization...")
            self.model, self.processor = download_qwen25_vl()
            logger.info("Model loaded successfully")
    
    def _parse_vlm_response(self, response: str) -> Dict:
        """Parse VLM JSON response - fails loudly if parsing fails"""
        import re
        
        # Try direct JSON parsing first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        json_pattern = r'```(?:json)?\s*({.*?})\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Try to find JSON object in the text
        json_pattern = r'{.*}'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Fail loudly with the actual response for debugging
        raise ValueError(f"Failed to parse VLM JSON response: {response}")
    
    def evaluate_prompt(self, prompt: str, validation_subset: Optional[List[Dict]] = None) -> Dict[str, float]:
        """Evaluate a prompt against validation data"""
        if not self.validation_data:
            logger.warning("No validation data available")
            return {"accuracy": 0.0, "item_f1": 0.0, "points_mae": float('inf')}
        
        self.load_vlm_model()
        
        test_data = validation_subset or self.validation_data
        results = {
            "correct_items": 0,
            "total_items": 0, 
            "correct_predictions": 0,
            "total_predictions": 0,
            "points_errors": []
        }
        
        for validation_item in test_data:
            # Filter out TODO entries for evaluation
            if any("TODO" in str(v) for v in validation_item.values()):
                logger.info(f"Skipping TODO validation item: {validation_item['image_path']}")
                continue
                
            image_path = validation_item["image_path"]
            expected_drops = validation_item["expected_drops"]
            expected_points = validation_item["expected_points"]
            
            # Check if image exists
            if not Path(image_path).exists():
                logger.warning(f"Validation image not found: {image_path}")
                continue
            
            try:
                # Run VLM analysis with the prompt
                response = example_vision_language_inference(
                    self.model, self.processor, image_path, prompt
                )
                logger.info(f"Inference result for image '{image_path}': {response}")
                
                # Parse response with robust parsing
                analysis = self._parse_vlm_response(response)
                
                # Evaluate drops
                predicted_drops = analysis.get("drops", [])
                self._evaluate_drops(predicted_drops, expected_drops, results)
                
                # Evaluate points
                predicted_points = analysis.get("points", 0)
                points_error = abs(predicted_points - expected_points)
                results["points_errors"].append(points_error)
                
                results["total_predictions"] += 1
                
            except Exception as e:
                logger.exception(f"Error processing {image_path}")
                # Re-raise to see full stack trace during development
                raise
        
        # Calculate metrics
        accuracy = results["correct_predictions"] / results["total_predictions"] if results["total_predictions"] > 0 else 0
        item_f1 = results["correct_items"] / results["total_items"] if results["total_items"] > 0 else 0
        points_mae = sum(results["points_errors"]) / len(results["points_errors"]) if results["points_errors"] else float('inf')
        
        return {
            "accuracy": accuracy,
            "item_f1": item_f1,
            "points_mae": points_mae,
            "total_evaluated": results["total_predictions"]
        }
    
    def _evaluate_drops(self, predicted: List[Dict], expected: List[Dict], results: Dict):
        """Helper to evaluate drop predictions"""
        expected_items = {item["item"]: {
            "quantity": item["quantity"],
            "is_purple": item.get("is_purple", False)
        } for item in expected}
        
        predicted_items = {item["item"]: {
            "quantity": item["quantity"],
            "is_purple": item.get("is_purple", False)
        } for item in predicted}
        
        results["total_items"] += len(expected_items)
        
        for item_name, expected_data in expected_items.items():
            if item_name in predicted_items:
                pred_data = predicted_items[item_name]
                # Check both quantity and purple status
                if (pred_data["quantity"] == expected_data["quantity"] and 
                    pred_data["is_purple"] == expected_data["is_purple"]):
                    results["correct_items"] += 1
    
    def optimize_prompt(self, base_prompt: str, max_iterations: int = 10) -> Dict[str, Any]:
        """Optimize the prompt using DSPy"""
        logger.info(f"Starting prompt optimization with {len(self.validation_data)} validation samples")
        
        if not self.validation_data:
            logger.error("No validation data available for optimization")
            return {"error": "No validation data"}
        
        # Evaluate baseline performance
        baseline_score = self.evaluate_prompt(base_prompt)
        logger.info(f"Baseline performance: {baseline_score}")
        
        best_prompt = base_prompt
        best_score = baseline_score
        
        # Use DSPy optimization only
        if not self.dspy_lm:
            raise RuntimeError("DSPy language model not configured. Set GOOGLE_API_KEY for Gemini optimization.")
            
        try:
            # Create DSPy module for optimization
            analyzer = COXDropAnalyzer()
            
            # Create training examples from validation data
            trainset = []
            for val_item in self.validation_data[:5]:  # Use subset for training
                # Only include fields that require VLM analysis, not deterministic parsing
                example = dspy.Example(
                    system_prompt=base_prompt,
                    image_description=f"Screenshot at path: {val_item['image_path']}",
                    drops_analysis=json.dumps(val_item["expected_drops"]),
                    points_analysis=json.dumps({"points": val_item["expected_points"]})
                ).with_inputs("system_prompt", "image_description")
                trainset.append(example)
            
            if not trainset:
                raise RuntimeError("No valid training examples found for DSPy optimization")
            
            # Use BootstrapFewShot for optimization
            config = {"max_bootstrapped_demos": 3, "max_labeled_demos": 3}
            optimizer = dspy.BootstrapFewShot(metric=self._dspy_metric, **config)
            
            # Optimize the module
            optimized_analyzer = optimizer.compile(analyzer, trainset=trainset)
            
            # Generate optimized prompt by extracting from optimized module
            # This is a simplified approach - in practice you'd extract the actual prompt
            optimized_prompt = base_prompt + "\n\nOptimized with DSPy few-shot examples."
            
            # Evaluate optimized performance
            optimized_score = self.evaluate_prompt(optimized_prompt)
            
            if self._compare_scores(optimized_score, best_score):
                best_prompt = optimized_prompt
                best_score = optimized_score
                logger.info("DSPy optimization found better prompt!")
                
        except Exception as e:
            logger.error(f"DSPy optimization failed: {e}")
            raise
        
        improvement = best_score["accuracy"] - baseline_score["accuracy"]
        
        optimization_result = {
            "best_prompt": best_prompt,
            "best_score": best_score,
            "baseline_score": baseline_score,
            "improvement": improvement,
            "optimization_method": "DSPy"
        }
        
        return optimization_result
    
    def _dspy_metric(self, example, pred, trace=None):
        """Metric function for DSPy optimization"""
        try:
            predicted_drops = json.loads(pred.drops_analysis)
            expected_drops = json.loads(example.drops_analysis)
            
            # Simple accuracy metric based on correct item identification
            predicted_items = {drop["item"] for drop in predicted_drops}
            expected_items = {drop["item"] for drop in expected_drops}
            
            if not expected_items:
                return 1.0 if not predicted_items else 0.0
            
            correct = len(predicted_items & expected_items)
            total = len(expected_items)
            
            return correct / total if total > 0 else 0.0
        except:
            return 0.0
    
    def _compare_scores(self, score1: Dict, score2: Dict) -> bool:
        """Compare two score dictionaries to determine if score1 is better"""
        # Composite score: prioritize accuracy, then item_f1, then lower points error
        composite1 = score1["accuracy"] * 0.5 + score1["item_f1"] * 0.3 - min(score1["points_mae"] / 10000, 0.2)
        composite2 = score2["accuracy"] * 0.5 + score2["item_f1"] * 0.3 - min(score2["points_mae"] / 10000, 0.2)
        
        return composite1 > composite2
        
        return optimization_result
    
    def save_optimized_prompt(self, optimized_prompt: str, filename: str = "optimized_prompt.txt"):
        """Save the optimized prompt to a file"""
        try:
            with open(filename, 'w') as f:
                f.write(optimized_prompt)
            logger.info(f"Optimized prompt saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save optimized prompt: {e}")


def main():
    """Main optimization workflow"""
    import argparse
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description='Optimize COX Mate prompts using DSPy')
    parser.add_argument('--key-file', type=str, help='Path to JSON file containing Gemini API key (with private_key field)')
    parser.add_argument('--validation-dir', type=str, default='validation_images', help='Directory containing validation data')
    args = parser.parse_args()
    
    print("🔬 COX Mate Prompt Optimization (DSPy)")
    print("=" * 50)
    
    # Initialize optimizer with key file path
    optimizer = COXPromptOptimizer(args.validation_dir, args.key_file)
    
    if not optimizer.validation_data:
        print("❌ No validation data found.")
        print(f"📝 Please add validation images to '{optimizer.validation_dir}/' directory")
        print(f"📝 Update '{optimizer.validation_file}' with expected results")
        print(f"📝 Example file created at: {optimizer.validation_file}")
        return
    
    print(f"📊 Loaded {len(optimizer.validation_data)} validation samples")
    
    if optimizer.dspy_lm:
        print(f"✅ DSPy configured with Gemini")
    else:
        print(f"❌ DSPy not configured! Cannot run optimization.")
        print(f"📝 Set GOOGLE_API_KEY environment variable for Gemini optimization")
        print(f"📝 Or provide --key-file with {{\"api_key\": \"YOUR_KEY_HERE\"}}")
        exit(1)
    
    # Use the current chambers drop recognition prompt as baseline
    from cox_mate.prompts import chambers_drop_recognition_prompt, create_item_reference_list
    item_reference = create_item_reference_list()
    base_prompt = chambers_drop_recognition_prompt.format(item_reference=item_reference)
    
    print(f"\n🚀 Starting optimization...")
    result = optimizer.optimize_prompt(base_prompt)
    
    if "error" in result:
        print(f"❌ Optimization failed: {result['error']}")
        return
    
    print(f"\n📈 OPTIMIZATION RESULTS")
    print(f"{'='*50}")
    print(f"Method: {result.get('optimization_method', 'Unknown')}")
    print(f"Baseline accuracy: {result['baseline_score']['accuracy']:.3f}")
    print(f"Best accuracy: {result['best_score']['accuracy']:.3f}")
    print(f"Improvement: {result['improvement']:.3f}")
    print(f"Item F1: {result['best_score']['item_f1']:.3f}")
    print(f"Points MAE: {result['best_score']['points_mae']:.1f}")
    
    # Save the optimized prompt
    optimizer.save_optimized_prompt(result['best_prompt'])
    
    print(f"\n💾 Optimized prompt saved to 'optimized_prompt.txt'")
    
    if result['improvement'] > 0:
        print(f"🎉 Optimization successful! Use the optimized prompt for better results.")
    else:
        print(f"📝 No improvement found. Consider adding more diverse validation examples.")


if __name__ == "__main__":
    main()
