#!/usr/bin/env python3
"""uv run --with pillow python project2/validate.py"""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from PIL import Image

repo = Path(__file__).resolve().parents[1]
checks = {}
with tempfile.TemporaryDirectory() as temp:
    native = str(Path(temp) / 'reference')
    subprocess.run(['g++', '-std=c++20', '-O3', '-ffp-contract=off', '-march=native',
                    '-I', str(repo/'include'), str(repo/'project2/reference.cpp'),
                    '-o', native], check=True)
    for metadata_path in sorted((repo/'project2/results').rglob('metadata.json')):
        directory = metadata_path.parent
        label = str(directory.relative_to(repo/'project2/results'))
        meta = json.loads(metadata_path.read_text())
        assert meta['returncode'] == 0, label
        assert hashlib.sha256((directory/'main.cpp').read_bytes()).hexdigest() == meta['source_sha256'], label
        assert hashlib.sha256((directory/'kernel').read_bytes()).hexdigest() == meta['kernel_sha256'], label
        n = meta['size']
        image = Image.open(directory/'out.png').convert('RGBA')
        assert image.size == (n, n)
        actual = image.tobytes()
        if meta['case'] == 'mandelbrot':
            expected = subprocess.check_output([native, str(n), str(n)])
            mismatch = sum(actual[i:i+4] != expected[i:i+4] for i in range(0, len(actual), 4))
            checks[label] = dict(pixels=n*n, mismatched_pixels=mismatch,
                                          opaque_pixels=sum(a == 255 for a in actual[3::4]))
        else:
            written = 0
            mismatch = 0
            for row in range(n):
                y = n - 1 - row
                for x in range(n):
                    tid = y*n+x
                    px = image.getpixel((x, row))
                    is_written = meta['case'] == 'gradient' or tid < 46*64*8
                    if is_written:
                        written += 1
                        mismatch += px != (255*x//n, 255*y//n, 0, 255)
                    else:
                        mismatch += px != (0, 0, 0, 0)
            checks[label] = dict(expected_written_pixels=written, mismatched_pixels=mismatch)
print(json.dumps(checks, indent=2))
(repo/'project2/validation.json').write_text(json.dumps(checks, indent=2)+'\n')
assert {'gradient-256', 'single-pass-256', 'mandelbrot-512'} <= checks.keys(), 'Missing required runs'
assert all(c['mismatched_pixels'] == 0 for c in checks.values()), 'Pixel validation failed'
