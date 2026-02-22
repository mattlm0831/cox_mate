# COX Mate Testing & Optimization Guide

This document covers the comprehensive testing framework and DSPy optimization system for COX Mate.

## Testing Framework

### Setup

The project uses pytest with comprehensive test coverage:

```bash
# Run all tests
poetry run pytest

# Run specific test categories
poetry run pytest -m unit          # Unit tests only
poetry run pytest -m integration   # Integration tests only
poetry run pytest -m "not slow"    # Exclude slow tests

# Run with coverage
poetry run pytest --cov=cox_mate --cov-report=html

# Verbose output
poetry run pytest -v --tb=short
```

### Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── test_database.py           # Database operations
├── test_filename_parsing.py   # Filename parsing logic
├── test_file_processing.py    # File discovery & filtering
├── test_integration.py        # End-to-end integration
└── test_dspy_optimization.py  # DSPy optimization tests
```

### Key Fixtures

- `temp_dir` - Temporary directory for test files
- `test_db` - Isolated test database
- `cox_tracker` - COXDropTracker with test database
- `sample_screenshot_files` - Mock PNG files with proper naming
- `validation_data` - Sample validation data for DSPy

### Test Categories

**Unit Tests** (`-m unit`)

- Filename parsing logic
- Database operations
- Icon management
- Individual component functionality

**Integration Tests** (`-m integration`)

- Full processing workflow
- Database persistence
- Component interaction

**VLM Tests** (`-m vlm`)

- Tests requiring actual VLM models
- Slower, run separately

## Item Icons System

### Directory Structure

```
assets/
└── item_icons/
    ├── README.md
    ├── icon_mapping.json
    ├── twisted_bow.png
    ├── dragon_claws.png
    └── ... (other item icons)
```

### Setup Item Icons

1. **Initialize the system:**

   ```bash
   poetry run python cox_mate/item_icons.py
   ```

2. **Add icon files:**
   - Save item icons as PNG/JPG in `assets/item_icons/`
   - Use descriptive names (e.g., `twisted_bow.png`)

3. **Update mapping:**

   ```json
   {
     \"twisted_bow.png\": \"Twisted bow\",
     \"dragon_claws.png\": \"Dragon claws\"
   }
   ```

4. **Validate icons:**
   ```python
   from cox_mate.item_icons import ItemIconManager
   manager = ItemIconManager()
   validation = manager.validate_icons()
   ```

### ItemIconManager API

```python
manager = ItemIconManager(\"assets/item_icons\")

# Add new icon mapping
manager.add_icon(\"new_item.png\", \"New Item Name\")

# Get item name for icon
item_name = manager.get_item_name(\"twisted_bow.png\")

# Load icon image
image = manager.load_icon_image(\"twisted_bow.png\")

# Validate icon consistency
validation = manager.validate_icons()

# Create VLM prompt section
prompt_section = manager.create_icon_reference_prompt()
```

## DSPy Optimization System

### Overview

DSPy optimizes VLM prompts for better accuracy using validation data.

### Setup

1. **Install DSPy (optional):**

   ```bash
   poetry install --extras dspy
   ```

2. **Prepare validation images:**
   - Add screenshots to `validation_images/`
   - Follow naming convention from `validation_mapping.json`

3. **Configure expected results:**
   - Edit `validation_mapping.json` with expected drops/points
   - Include diverse scenarios (purple drops, regular loot, edge cases)

### Running Optimization

```bash
# Full optimization
poetry run python optimize_prompt.py

# Test current prompt performance
poetry run python -c \"
from optimize_prompt import COXPromptOptimizer
opt = COXPromptOptimizer()
scores = opt.evaluate_prompt('current prompt text')
print(scores)
\"
```

### Validation Data Format

Each validation entry includes:

```json
{
  \"image_path\": \"validation_images/cox_drop_twisted_bow.png\",
  \"description\": \"Screenshot showing Twisted bow drop\",
  \"expected_drops\": [
    {
      \"item\": \"Twisted bow\",
      \"quantity\": 1,
      \"confidence\": \"high\"
    }
  ],
  \"expected_points\": 35000,
  \"raid_type\": \"regular\",
  \"completion_count\": 125,
  \"notes\": \"Clear purple drop with good visibility\",
  \"difficulty\": \"easy\"
}
```

### Optimization Workflow

1. **Load validation data** from `validation_mapping.json`
2. **Evaluate baseline** prompt performance
3. **Generate prompt variations** using DSPy
4. **Test variations** against validation set
5. **Select best performing** prompt
6. **Save optimized prompt** to `optimized_prompt.txt`

### Metrics

- **Accuracy**: Overall prediction correctness
- **Item F1**: Item identification accuracy
- **Points MAE**: Mean absolute error for points prediction
- **Total Evaluated**: Number of validation samples processed

## Adding New Test Cases

### 1. Unit Tests

```python
def test_new_functionality(test_db):
    \"\"\"Test new feature\"\"\"
    # Arrange
    setup_data = create_test_data()

    # Act
    result = function_under_test(setup_data)

    # Assert
    assert result.expected_property == expected_value
```

### 2. Integration Tests

```python
@pytest.mark.integration
def test_end_to_end_workflow(cox_tracker, sample_screenshot_files):
    \"\"\"Test complete workflow\"\"\"
    # Mock VLM responses
    with patch.object(cox_tracker, 'analyze_drop_screenshot') as mock_drops:
        mock_drops.return_value = {\"drops\": [...]}

        # Test workflow
        result = cox_tracker.record_raid(...)
        assert result is not None
```

### 3. Validation Cases

1. **Add screenshot** to `validation_images/`
2. **Update** `validation_mapping.json` with expected results
3. **Run optimization** to include in testing
4. **Verify** expected results match game behavior

## Continuous Integration

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### GitHub Actions (example)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.10"
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest --cov=cox_mate
```

## Performance Testing

### Benchmarking VLM Performance

```python
# Benchmark prompt performance
from optimize_prompt import COXPromptOptimizer
optimizer = COXPromptOptimizer()

# Test different prompt strategies
prompts = [\"strategy_1\", \"strategy_2\", \"strategy_3\"]
for prompt in prompts:
    scores = optimizer.evaluate_prompt(prompt)
    print(f\"{prompt}: {scores['accuracy']:.3f}\")
```

### Memory Usage

```bash
# Profile memory usage
poetry run python -m memory_profiler main.py test_screenshots/
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `poetry install` completed successfully
2. **Missing Dependencies**: Install optional dependencies with `--extras`
3. **Test Failures**: Check file paths and temporary directory cleanup
4. **VLM Loading**: Verify sufficient memory and GPU access
5. **DSPy Configuration**: Check language model setup

### Debug Mode

```bash
# Enable debug logging
poetry run python main.py test_screenshots/ --log-level DEBUG

# Run tests with debugging
poetry run pytest --pdb --tb=long
```

### Performance Issues

```bash
# Profile code performance
poetry run python -m cProfile -o profile.stats main.py test_screenshots/
python -c \"import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)\"
```

## Best Practices

### Test Writing

- Use descriptive test names
- Include setup, action, and assertion phases
- Mock external dependencies (VLM, file system)
- Test edge cases and error conditions
- Keep tests isolated and independent

### Validation Data

- Include diverse scenarios (different drops, raid types, edge cases)
- Verify expected results match actual game behavior
- Update validation data when game UI changes
- Document unusual cases in notes field

### Optimization

- Start with small validation sets for faster iteration
- Include both easy and difficult cases
- Monitor for overfitting to validation data
- Regular re-validation with new screenshots
- Version control optimized prompts

This comprehensive testing and optimization framework ensures reliable COX Mate performance and continuous improvement through data-driven prompt optimization.
