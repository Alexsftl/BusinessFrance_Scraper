from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import logging

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METRICS_PATH = DATA_DIR / "metrics.jsonl"

class ErrorCounter(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.count = 0
    def emit(self, record):
        self.count += 1

def count_unchecked(offers):
    return sum(
        1 for o in offers.values() if o.get("relevancy_check") == "unchecked"
    )

def append_run(scraped, new, relevant, stored, unchecked, errors, runtime, path=METRICS_PATH):
    record = {
        "timestamp": datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds"),
        "scraped": scraped,
        "new": new,
        "relevant": relevant,
        "stored": stored,
        "unchecked": unchecked,
        "runtime": runtime,
        "errors": errors,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record