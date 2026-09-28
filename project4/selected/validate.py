#!/usr/bin/env python3
"""Validate the selected final optimization against the prescribed C baseline."""
import hashlib
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


path = ROOT / 'results/c-mshr384'
meta = load(path / 'metadata.json')
c = load(P4 / 'results/c-l3-4m/metadata.json')
assert meta['returncode'] == 0
expected = dict(P4_NUM_TMS=64, P4_ENABLE_L3=1, P4_L3_MIB=4,
                P4_L3_LATENCY=480, P4_L2_MSHRS=384)
assert meta['configuration'] == expected
assert {k: v for k, v in expected.items() if k != 'P4_L2_MSHRS'} == c['configuration']
assert meta['kernel_sha256'] == c['kernel_sha256'] == sha(ROOT / 'results/workload/kernel')
assert load(ROOT / 'results/workload/metadata.json') == load(P4 / 'results/workload/metadata.json')
assert meta['simulation_command'] == c['simulation_command']
assert sha(path / 'main.cpp') == meta['main_sha256']
source = (path / 'main.cpp').read_text()
for key, value in expected.items():
    assert re.search(rf'^#define {key} {value}$', source, re.M)
log = (path / 'trax_log.txt').read_text()
assert 'Project 4: L2 total=4096 KiB, L3 total=4096 KiB' in log
assert 'Project 4: L2 MSHRs/slice=384, L3 MSHRs/slice=192' in log
metrics = parse_log(path / 'trax_log.txt')
assert metrics == meta['metrics']
assert parse_log(P4 / 'results/c-l3-4m/trax_log.txt') == c['metrics']
assert metrics['cycles'] < c['metrics']['cycles'], 'Selected optimization must improve on C'
assert metrics['RT_rays'] == c['metrics']['RT_rays']
assert metrics['DRAM_write_bytes'] == c['metrics']['DRAM_write_bytes']
image = Image.open(path / 'out.png').convert('RGBA')
assert image.size == (512, 512)
assert image.getchannel('A').getextrema() == (255, 255)
pixels = image.tobytes()
assert pixels == Image.open(P4 / 'results/c-l3-4m/out.png').convert('RGBA').tobytes()
assert hashlib.sha256(pixels).hexdigest() == meta['image_pixels_sha256']
assert sha(path / 'out.png') == meta['image_file_sha256']
reference = Image.open(P4 / 'validation/cpu-reference.png').convert('RGBA').tobytes()
differences = sum(pixels[i:i+4] != reference[i:i+4] for i in range(0, len(pixels), 4))
assert differences == 3
summary = dict(configuration=expected, baseline_c=c['metrics'], selected=metrics,
               speedup_vs_c=c['metrics']['cycles']/metrics['cycles'],
               time_reduction_percent=100*(1-metrics['cycles']/c['metrics']['cycles']),
               validation=dict(same_workload_and_elf=True, pixels_identical_to_c=True,
                               all_pixels_opaque=True, same_total_rays=True,
                               cpu_reference_differing_pixels= differences))
(ROOT / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, indent=2))
