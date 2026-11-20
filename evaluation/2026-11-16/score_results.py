from pathlib import Path
import json,re,unicodedata,math,statistics,hashlib
from difflib import SequenceMatcher
OUT=Path(__file__).resolve().parent
inputs=[json.loads(x) for x in (OUT/'inputs.jsonl').read_text().splitlines()]
gold={r['sample_id']:r for r in map(json.loads,(OUT/'answers.jsonl').read_text().splitlines())}

