"""An independent branch of the graph for checking selective invalidation."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--data', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
content = args.data.read_bytes()
rows = [line for line in content.decode().splitlines() if line.strip() and not line.lstrip().startswith('#')]
args.output.write_text(json.dumps({'rows': len(rows), 'sha256': hashlib.sha256(content).hexdigest()}, sort_keys=True) + '\n')
