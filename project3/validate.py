#!/usr/bin/env python3
"""Run with: uv run --with pillow python project3/validate.py"""
import json
from pathlib import Path
import subprocess
import tempfile
from PIL import Image

repo = Path(__file__).resolve().parents[1]
report = {}
# Exhaustive small/non-square dimensions plus course boundary examples.
cases = [(w, h) for w in range(1, 34) for h in range(1, 34)]
cases += [(255, 256), (256, 256), (257, 256), (350, 350), (360, 360), (512, 512)]
for w, h in cases:
    nx, ny = (w + 3) // 4, (h + 7) // 8
    seen = bytearray(w * h)
    for tid in range(nx * ny * 32):
        tile, offset = divmod(tid, 32)
        x, y = tile % nx * 4 + offset % 4, tile // nx * 8 + offset // 4
        if x >= w or y >= h:
            continue
        assert not seen[y * w + x], (w, h, x, y)
        seen[y * w + x] = 1
    assert all(seen), (w, h)
report['mapping'] = {'dimensions_tested': len(cases), 'complete_unique_coverage': True}

# Model the UNMODIFIED Part A, including writes beyond the framebuffer.
w = h = 350
expected = [(0, 0, 0, 0)] * (w * h)
out_of_bounds = 0
for tid in range(w * h):
    tile, offset = divmod(tid, 32)
    tx, ty = tile % (w // 4), tile // (w // 4)
    x, y = tx * 4 + offset % 4, ty * 8 + offset // 4
    if y * w + x >= w * h:
        out_of_bounds += 1
        continue
    expected[y * w + x] = (255, 0, 0, 255) if (tx & 1) ^ (not (ty & 1)) else (0, 255, 0, 255)
image = Image.open(repo / 'project3/results/part-a-350/out.png').convert('RGBA')
assert image.size == (w, h)
# Arches flips framebuffer rows when writing PNGs.
assert list(image.transpose(Image.Transpose.FLIP_TOP_BOTTOM).get_flattened_data()) == expected
report['part_a'] = {'pixel_mismatches': 0, 'unwritten_pixels': expected.count((0, 0, 0, 0)),
                    'out_of_framebuffer_writes_in_original': out_of_bounds}

with tempfile.TemporaryDirectory() as tmp:
    binary = Path(tmp) / 'reference'
    subprocess.run(['g++', '-std=c++20', '-O3', '-ffp-contract=off',
                    '-I', str(repo / 'include'), '-I', str(repo / 'src/trax-kernel'),
                    str(repo / 'project3/reference.cpp'), '-o', str(binary)], check=True)
    for scene in ('triangle', 'teapot'):
        mask = Path(tmp) / f'{scene}.mask'
        subprocess.run([str(binary), f'/root/datasets/{scene}.obj', str(w), str(h), str(mask)], check=True)
        oracle = mask.read_bytes()
        image = Image.open(repo / f'project3/results/{scene}-350/out.png').convert('RGBA')
        assert image.size == (w, h)
        pixels = list(image.transpose(Image.Transpose.FLIP_TOP_BOTTOM).get_flattened_data())
        expected = [(255, 0, 0, 255) if hit else (75, 75, 75, 255) for hit in oracle]
        mismatches = sum(a != b for a, b in zip(pixels, expected))
        assert len(oracle) == len(pixels) == w * h
        assert mismatches == 0, (scene, mismatches)
        assert 0 < sum(oracle) < len(oracle)
        report[scene] = {'pixel_mismatches': mismatches, 'hit_pixels': sum(oracle),
                         'miss_pixels': len(oracle) - sum(oracle), 'all_pixels_opaque': True}
path = repo / 'project3/validation.json'
path.write_text(json.dumps(report, indent=2) + '\n')
print(path.read_text())
