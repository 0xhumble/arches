#!/usr/bin/env python3
"""uv run --with typst python project3/package.py"""
import hashlib
import json
from pathlib import Path
import shutil
import typst

project = Path(__file__).resolve().parent
submission = project / 'submission'
submission.mkdir(exist_ok=True)
source = project.parent / 'src/trax-kernel/main.cpp'
validation = json.loads((project / 'validation.json').read_text())
assert validation['mapping']['complete_unique_coverage']
assert validation['part_a']['pixel_mismatches'] == 0
logs = []
for scene in ('triangle', 'teapot'):
    assert validation[scene]['pixel_mismatches'] == 0
    assert validation[scene]['all_pixels_opaque']
    result = project / f'results/{scene}-350'
    metadata = json.loads((result / 'metadata.json').read_text())
    assert metadata['returncode'] == 0
    assert metadata['source_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert source.read_bytes() == (result / 'main.cpp').read_bytes()
    logs += [(result / 'trax_log.txt').read_text(), '\n']
shutil.copy2(source, submission / 'main.cpp')
(submission / 'trax_log.txt').write_text(''.join(logs))
typst.compile(str(project / 'report.typ'), output=str(submission / 'report.pdf'), root=str(project))
print(submission)
