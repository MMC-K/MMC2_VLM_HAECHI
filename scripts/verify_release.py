"""Read-only checks for archived HAECHI responses, metrics and publication files."""
import hashlib
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / 'evaluation/2026-11-16'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    manifest = json.loads((EVAL / 'dataset_manifest.json').read_text())
    for filename, key in [('inputs.jsonl', 'inputs_sha256'), ('answers.jsonl', 'answers_sha256')]:
        assert sha(EVAL / filename) == manifest[key], f'Changed original: {filename}'
    inputs = rows(EVAL / 'inputs.jsonl')
    answers = rows(EVAL / 'answers.jsonl')
    ids = [row['sample_id'] for row in inputs]
    assert len(ids) == len(set(ids)) == 300
    assert set(ids) == {row['sample_id'] for row in answers}
    counts = {task: sum(row['task'] == task for row in inputs) for task in manifest['counts']}
    assert counts == manifest['counts'] == {'h400_direct': 100, 'h400_knowledge_image': 100, 'ocr': 100}
    for row in inputs:
        image = EVAL / 'images' / Path(row['image']).name
        assert sha(image) == row['image_sha256'], f'Image hash mismatch: {image.name}'
    engine = runpy.run_path(str(EVAL / 'score_results.py'))
    for label in ['qwen_base', 'qwen_haechi', 'hyperclova_base', 'hyperclova_haechi']:
        predictions = rows(EVAL / (label + '_predictions.jsonl'))
        assert len(predictions) == len({row['sample_id'] for row in predictions}) == 300
        assert set(ids) == {row['sample_id'] for row in predictions}
        assert all(not row.get('error') for row in predictions)
        calculated = engine['score'](label)
        archived = json.loads((EVAL / (label + '_scores.json')).read_text())
        assert calculated == archived, f'Rescoring differs: {label}'
    summary = json.loads((EVAL / 'summary.json').read_text())
    expected = {
        'qwen_base': (0.0, 0.54, 0.34),
        'qwen_haechi': (0.28, 0.56, 0.41),
        'hyperclova_base': (0.05, 0.54, 0.42),
        'hyperclova_haechi': (0.63, 0.56, 0.41),
    }
    for label, values in expected.items():
        tasks = summary['results'][label]['tasks']
        actual = (tasks['h400_direct']['normalized_exact'], tasks['ocr']['normalized_exact'], tasks['ocr']['strict_exact'])
        assert actual == values, f'V2.0 table mismatch: {label}'
    source_manifest = ROOT / 'SOURCE_MANIFEST.json'
    if source_manifest.exists():
        for entry in json.loads(source_manifest.read_text())['files']:
            assert sha(ROOT / entry['path']) == entry['published_sha256'], f"Publication hash mismatch: {entry['path']}"
    print('PASS: 300 input/image hashes, 1,200 saved responses, exact rescoring, V2.0 core metrics and publication hashes')


if __name__ == '__main__':
    main()
