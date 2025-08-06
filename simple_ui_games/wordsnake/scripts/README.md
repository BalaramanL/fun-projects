
# Scripts

This directory contains scripts for the Word Snake game.

## `generate_dictionary.py`

This script fetches a list of English words, filters them according to the game's rules, and saves them as a JSON file (`database.json`) in the `public` directory. This dictionary is then used by the game to validate words.

### Usage

1.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the script:
    ```bash
    python generate_dictionary.py
    ```
