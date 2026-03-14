# Cox Mate

Cox Mate is a Python project designed to process images and interact with Google Generative AI. This project aims to make your cox point tracking simple and persistent, if you like to use spreadsheet based drop analysis. This guide will help you set up the project and use the `cox_mate` script effectively. After setting it up and running it, you will be able to interact with your data in a csv. You should leave the .csv file in the root directory of the project, so on subsequent runs, it can only process new photos that have been added.

Further versions will further develop the web/ directory to allow for a local streamlit mini app to interact with your data, and completion photos.

## Things to note:

- Currently item detection is hit or miss, most of the purple chests are identified but there will be false negatives and false positives.
- If your screenshots do not have the points interface in the top right of your UI to the left of the map, you will need to modify the prompt in prompt.txt to tell it more about your interface.
- I suggest running this on a subset of your boss kills to get a baseline, then modify as you see fit. If you think the prompt can be further improved, please make a pr.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1. **Python 3.8 or higher**
2. **Poetry** (Python dependency management tool)
3. **Google Generative AI SDK**

## Setting Up Poetry

Poetry is used to manage dependencies and virtual environments for this project. Follow these steps to install Poetry:

1. Install Poetry by running the following command:

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Add Poetry to your PATH by following the instructions provided after installation.

3. Verify the installation:
   ```bash
   poetry --version
   ```

## Setting Up the Project

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd cox_mate
   ```

2. Install the project dependencies:

   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry env activate
   ```

## Using the `cox_mate` Script

The `cox_mate` script processes images and interacts with Google Generative AI. Follow these steps to use it:

1. Ensure you have a directory of `.png` images to process. This directory should be your "Boss Kills" directory from RuneLite, typically located at:

   ```
   HOME/.runelite/screenshots/user/Boss Kills
   ```

   The script will automatically handle non-Chambers of Xeric screenshots and ignore them.

2. Run the script:

   ```bash
   python -m cox_mate.cox_mate <photos-directory> --store <store-file> --api-key <your-api-key>
   ```

   - `<photos-directory>`: Path to the directory containing `.png` images.
   - `--store`: (Optional) Path to the CSV file where processed data will be stored. Defaults to `./data.csv`. If the file does not exist, it will be created with the defined schema. If you choose a different path, you must specify it on each run.
   - `--api-key`: Your Google Generative AI API key. If not provided, the script will use the `GEMINI_API_KEY` environment variable.

## Example

```bash
python -m cox_mate.cox_mate HOME/.runelite/screenshots/user/Boss Kills --api-key YOUR_API_KEY
```

## Notes

- Ensure your API key is valid and has the necessary permissions to interact with Google Generative AI.
- The `store-file` should be writable if it already exists.

## Updated Notes on Using the `cox_mate` Script

The `cox_mate` script processes images and interacts with Google Generative AI. Follow these steps to use it:

1. Ensure you have a directory of `.png` images to process. This directory should be your "Boss Kills" directory from RuneLite, typically located at:

   ```
   HOME/.runelite/screenshots/user/Boss Kills
   ```

   The script will automatically handle non-Chambers of Xeric screenshots and ignore them.

2. Run the script:

   ```bash
   python -m cox_mate.cox_mate <photos-directory> --store <store-file> --api-key <your-api-key>
   ```

   - `<photos-directory>`: Path to the directory containing `.png` images.
   - `--store`: (Optional) Path to the CSV file where processed data will be stored. Defaults to `./data.csv`. If the file does not exist, it will be created with the defined schema. If you choose a different path, you must specify it on each run.
   - `--api-key`: Your Google Generative AI API key. If not provided, the script will use the `GEMINI_API_KEY` environment variable.

## Example

```bash
python -m cox_mate.cox_mate HOME/.runelite/screenshots/user/Boss Kills --api-key YOUR_API_KEY
```

## Troubleshooting

- If you encounter issues with Poetry, refer to the [Poetry documentation](https://python-poetry.org/docs/).
- For issues with the Google Generative AI SDK, consult the [SDK documentation](https://developers.google.com/generative-ai/).

## License

This project is licensed under the MIT License.
