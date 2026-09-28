#!/usr/bin/env python3
"""Validate raw results and produce summary.json/csv/md. Run via uv with pillow."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from PIL import Image
from run import CASES, parse_log, sha

ROOT = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--results', type=Path, default=ROOT / 'results')
p.add_argument('--reference', type=Path, required=True, help='CPU reference, unflipped RGBA bytes')
p.add_argument('--reference-metrics', type=Path, required=True)
args = p.parse_args()
workload = json.loads((args.results / 'workload/metadata.json').read_text())
size = workload['size']
reference = args.reference.read_bytes()
assert len(reference) == size * size * 4
reference_metrics = json.loads(args.reference_metrics.read_text())
reference_image = Image.frombytes('RGBA', (size, size), reference)
reference_image = reference_image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
reference = reference_image.tobytes()

records = {}
main_template = None
pixels_hash = None
order = {name: i for i, name in enumerate(CASES)}
for path in sorted(args.results.glob('*/metadata.json'), key=lambda p: order.get(p.parent.name, -1)):
    if path.parent.name == 'workload':
        continue
    meta = json.loads(path.read_text())
    assert meta['returncode'] == 0
    assert sha(path.parent / 'main.cpp') == meta['main_sha256']
    assert meta['kernel_sha256'] == workload['kernel_sha256'] == sha(args.results / 'workload/kernel')
    template = re.sub(r'^#define P4_\w+ \d+$', '', (path.parent / 'main.cpp').read_text(), flags=re.M)
    assert main_template is None or main_template == template, 'Non-parameter simulator differences'
    main_template = template
    metrics = parse_log(path.parent / 'trax_log.txt')
    assert metrics == meta['metrics']
    image = Image.open(path.parent / 'out.png').convert('RGBA')
    assert image.size == (size, size)
    assert image.getchannel('A').getextrema() == (255, 255)
    pixels = image.tobytes()
    digest = hashlib.sha256(pixels).hexdigest()
    assert pixels_hash is None or digest == pixels_hash, 'Configurations have different images'
    pixels_hash = digest
    assert digest == meta['image_pixels_sha256']
    mismatches = sum(pixels[i:i+4] != reference[i:i+4] for i in range(0, len(pixels), 4))
    # Cross-configuration equality is strict. Report CPU-oracle discrepancies
    # explicitly rather than silently treating near-boundary pixels as equal.
    assert metrics['RT_rays'] == reference_metrics['rays'], 'CPU/simulator ray counts differ'
    records[path.parent.name] = dict(configuration=meta['configuration'], **metrics,
                                      cpu_reference_pixel_mismatches=mismatches)

assert records
base_b, base_c = records['b-64tm'], records['c-l3-4m']
rows = []
for name, r in records.items():
    r['speedup_vs_b'] = base_b['cycles'] / r['cycles']
    r['speedup_vs_c'] = base_c['cycles'] / r['cycles']
    rows.append(dict(case=name, cycles=r['cycles'], frame_ms=r['frame_ms'],
                     speedup_vs_b=r['speedup_vs_b'], speedup_vs_c=r['speedup_vs_c'],
                     dram_read_mib=r['DRAM_read_bytes'] / (1 << 20),
                     l2_hit_pct=r['L2']['Hits percent'], l2_half_miss_pct=r['L2']['Half Misses percent'],
                     l2_miss_pct=r['L2']['Misses percent'],
                     l3_hit_pct=r.get('L3', {}).get('Hits percent', ''),
                     l3_half_miss_pct=r.get('L3', {}).get('Half Misses percent', ''),
                     l3_miss_pct=r.get('L3', {}).get('Misses percent', '')))

repeat_checks = {}
for path in sorted((ROOT / 'repeat').glob('*/metadata.json')):
    name = path.parent.name
    if name == 'workload':
        continue
    meta = json.loads(path.read_text())
    original = json.loads((args.results / name / 'metadata.json').read_text())
    assert meta['returncode'] == 0
    assert meta['kernel_sha256'] == original['kernel_sha256']
    assert meta['main_sha256'] == original['main_sha256']
    assert meta['image_pixels_sha256'] == original['image_pixels_sha256']
    assert sha(path.parent / 'out.png') == meta['image_file_sha256']
    measured = parse_log(path.parent / 'trax_log.txt')
    assert measured == meta['metrics']
    repeat_checks[name] = {'all_recorded_metrics_identical': measured == original['metrics'],
                           'original_cycles': original['metrics']['cycles'],
                           'repeat_cycles': measured['cycles'], 'pixels_identical': True}

summary = {'workload': workload, 'cpu_reference': reference_metrics, 'repeat_checks': repeat_checks,
           'validation': {'all_images_identical': True, 'all_pixels_opaque': True,
                          'cpu_reference_pixel_mismatches': mismatches,
                          'cpu_reference_exact_pixel_match': mismatches == 0,
                          'cpu_reference_pixel_agreement_percent': 100 * (1 - mismatches / (size * size)),
                          'cpu_reference_differing_pixels_png_xy': [
                              [(i // 4) % size, (i // 4) // size]
                              for i in range(0, len(pixels), 4) if pixels[i:i+4] != reference[i:i+4]],
                          'cpu_reference_ray_count_matches': True,
                          'only_four_configuration_macros_vary': True, 'image_pixels_sha256': pixels_hash},
           'cases': records}
(ROOT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
buffer = io.StringIO()
writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator='\n')
writer.writeheader()
writer.writerows(rows)
(ROOT / 'summary.csv').write_text(buffer.getvalue())
lines = ['# Project 4 — measured results', '',
         f'Sponza, {size}×{size}, 1 sample/pixel, up to 3 ray segments, 1.515 GHz, cold caches.', '',
         '| Case | Cycles | Frame (ms) | Speedup vs C | DRAM reads (MiB) | L2 hit % | L3 hit % |',
         '|---|---:|---:|---:|---:|---:|---:|']
for r in rows:
    l3_hit = '-' if r['l3_hit_pct'] == '' else f"{r['l3_hit_pct']:.2f}"
    lines.append(f"| {r['case']} | {r['cycles']:,} | {r['frame_ms']:.6f} | {r['speedup_vs_c']:.4f}× | {r['dram_read_mib']:.3f} | {r['l2_hit_pct']:.2f} | {l3_hit} |")
lines += ['', f'All configurations produce identical opaque pixels and the same total traced rays as the CPU reference. CPU reference differing pixels: {mismatches}/{size * size} (not claimed bit-exact unless zero).',
          '', 'Hit percentages exclude uncached stores; half-misses are requests merged into an outstanding miss, not ordinary cache hits.',
          'The CPU reference shares scene/geometry code; it is an independent execution path, not an independently implemented geometry library.',
          'Cache power parameters are uncalibrated; no energy/area/physical 3D-stacking conclusions are drawn.', '']
(ROOT / 'summary.md').write_text('\n'.join(lines))
validation = ROOT / 'validation'
validation.mkdir(exist_ok=True)
reference_image.save(validation / 'cpu-reference.png')
(validation / 'reference-metrics.json').write_text(json.dumps(reference_metrics, indent=2) + '\n')
(validation / 'checks.json').write_text(json.dumps(dict(**summary['validation'], repeat_checks=repeat_checks), indent=2) + '\n')
print('\n'.join(lines))
