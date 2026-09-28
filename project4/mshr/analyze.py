#!/usr/bin/env python3
"""Verify the one-variable L2 MSHR experiment and summarize raw evidence."""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parent
P4 = ROOT.parent
sys.path.insert(0, str(P4))
from run import parse_log, sha


def load(path):
    return json.loads(path.read_text())


old = load(P4 / 'results/l3-16m/metadata.json')
baseline_b = load(P4 / 'results/b-64tm/metadata.json')['metrics']
baseline_c = load(P4 / 'results/c-l3-4m/metadata.json')['metrics']
workload = load(ROOT / 'results/workload/metadata.json')
assert workload == load(P4 / 'results/workload/metadata.json')
assert sha(ROOT / 'results/workload/kernel') == old['kernel_sha256']
reference = Image.open(P4 / 'validation/cpu-reference.png').convert('RGBA').tobytes()
original_pixels = Image.open(P4 / 'results/l3-16m/out.png').convert('RGBA').tobytes()
records = {}
rows = []
template = None
for count in (192, 384, 768):
    case = f'l2-mshr{count}'
    path = ROOT / 'results' / case
    meta = load(path / 'metadata.json')
    assert meta['returncode'] == 0
    assert meta['configuration'] == dict(P4_NUM_TMS=64, P4_ENABLE_L3=1,
                                         P4_L3_MIB=16, P4_L3_LATENCY=480, P4_L2_MSHRS=count)
    assert meta['kernel_sha256'] == old['kernel_sha256']
    assert meta['simulation_command'] == old['simulation_command']
    assert sha(path / 'main.cpp') == meta['main_sha256']
    source = (path / 'main.cpp').read_text()
    normalized, n = re.subn(r'^#define P4_L2_MSHRS \d+$', '#define P4_L2_MSHRS <count>', source, flags=re.M)
    assert n == 1
    assert template is None or normalized == template, 'Changes beyond L2 MSHR count'
    template = normalized
    log = (path / 'trax_log.txt').read_text()
    assert f'Project 4: L2 MSHRs/slice={count}, L3 MSHRs/slice=192' in log
    metrics = parse_log(path / 'trax_log.txt')
    assert metrics == meta['metrics']
    assert metrics['RT_rays'] == old['metrics']['RT_rays']
    assert metrics['DRAM_write_bytes'] == 512 * 512 * 4
    image = Image.open(path / 'out.png').convert('RGBA')
    assert image.size == (512, 512)
    assert image.getchannel('A').getextrema() == (255, 255)
    pixels = image.tobytes()
    assert pixels == original_pixels
    assert hashlib.sha256(pixels).hexdigest() == meta['image_pixels_sha256']
    assert sha(path / 'out.png') == meta['image_file_sha256']
    cpu_differences = sum(pixels[i:i+4] != reference[i:i+4] for i in range(0, len(pixels), 4))
    assert cpu_differences == 3  # Known, explicitly reported first-stage oracle discrepancy.
    if count == 192:
        assert metrics == old['metrics'], '192-MSHR baseline did not reproduce the previous study'
    row = dict(mshrs_per_l2=count, total_local_l2_mshrs=8*count,
               cycles=metrics['cycles'], frame_ms=metrics['frame_ms'],
               speedup_vs_192=old['metrics']['cycles']/metrics['cycles'],
               speedup_vs_c=baseline_c['cycles']/metrics['cycles'],
               speedup_vs_b=baseline_b['cycles']/metrics['cycles'],
               l2_hit_percent=metrics['L2']['Hits percent'],
               l2_half_miss_percent=metrics['L2']['Half Misses percent'],
               l2_misses=metrics['L2']['Misses'],
               l2_misses_per_cycle=metrics['L2']['Misses']/metrics['cycles'],
               l2_mshr_stalls=metrics['L2']['MSHR Stalls'],
               l1_mshr_stalls=metrics['L1d']['MSHR Stalls'],
               l3_hit_percent=metrics['L3']['Hits percent'],
               dram_read_mib=metrics['DRAM_read_bytes']/2**20)
    rows.append(row)
    records[case] = dict(configuration=meta['configuration'], metrics=metrics,
                         cpu_reference_differing_pixels=cpu_differences)

best = min(records, key=lambda name: records[name]['metrics']['cycles'])
repeat_checks = {}
for path in (ROOT / 'repeat').glob('*/metadata.json'):
    name = path.parent.name
    if name == 'workload':
        continue
    meta = load(path)
    first = load(ROOT / 'results' / name / 'metadata.json')
    assert meta['returncode'] == 0
    assert meta['kernel_sha256'] == first['kernel_sha256']
    assert meta['main_sha256'] == first['main_sha256'] == sha(path.parent / 'main.cpp')
    assert meta['configuration'] == first['configuration']
    assert Image.open(path.parent / 'out.png').convert('RGBA').tobytes() == original_pixels
    assert parse_log(path.parent / 'trax_log.txt') == meta['metrics'] == first['metrics']
    repeat_checks[name] = dict(all_recorded_metrics_identical=True, pixels_identical=True,
                              cycles=meta['metrics']['cycles'])

summary = dict(workload=workload, fixed_l3_mib=16, fixed_l3_latency=480,
               best_case=best, validation=dict(only_l2_mshr_macro_varies=True,
               baseline192_reproduces_previous_metrics=True, all_pixels_identical=True,
               all_pixels_opaque=True, cpu_reference_differing_pixels=3,
               same_total_rays=old['metrics']['RT_rays']),
               cases=records, repeat_checks=repeat_checks)
(ROOT / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
buf = io.StringIO()
w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator='\n')
w.writeheader()
w.writerows(rows)
(ROOT / 'summary.csv').write_text(buf.getvalue())
lines = ['# L2 MSHR sweep — measured results', '',
         'Sponza 512×512; 64 TMs; eight local L2s; fixed 16 MiB L3, 480-cycle latency.', '',
         '| MSHRs/local L2 | Cycles | Frame ms | Speedup vs 192 | L2 hit % | L2 MSHR stalls | DRAM read MiB |',
         '|---|---:|---:|---:|---:|---:|---:|']
for r in rows:
    lines.append(f"| {r['mshrs_per_l2']} | {r['cycles']:,} | {r['frame_ms']:.6f} | {r['speedup_vs_192']:.4f}× | {r['l2_hit_percent']:.3f} | {r['l2_mshr_stalls']:,} | {r['dram_read_mib']:.3f} |")
lines += ['', f'Best measured case: **{best}**.', '',
          '192 reproduces every recorded performance counter from the previous capacity study.',
          'All images match the previous study exactly; the known three CPU-reference pixel differences remain.',
          'MSHR Stalls includes return/miss-queue backpressure and is not a direct MSHR-occupancy metric.',
          f'Repeat checks: {json.dumps(repeat_checks)}', '']
(ROOT / 'summary.md').write_text('\n'.join(lines))
print('\n'.join(lines))
