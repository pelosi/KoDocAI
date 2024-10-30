import json
from typing import Any

def save_to_json(data: Any, file_path: str) -> None:
    """
    Save data to a JSON file.

    :param data: The data to be saved (must be JSON-serializable).
    :param file_path: Path to the output JSON file.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
    except Exception as e:
        raise RuntimeError(f"Error saving JSON to file: {e}")
