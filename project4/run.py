#!/usr/bin/env python3
"""Serial, reproducible Project 4 experiments. Launch through tmux.

Run with: uv run --with pillow python project4/run.py
Refuses to overwrite results; --results selects a new run directory.
Only the four P4_* constants in simulator main.cpp change between cases.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / 'src/arches-v2/main.cpp'
KDIR = REPO / 'src/trax-kernel'
SIM = REPO / 'build/src/arches-v2/arches-v2'
CASES = {
    'a-8tm': (8, 0, 4, 480),
    'b-64tm': (64, 0, 4, 480),
    'c-l3-4m': (64, 1, 4, 480),
    'l3-8m': (64, 1, 8, 480),
    'l3-16m': (64, 1, 16, 480),
    'l3-8m-lat528': (64, 1, 8, 528),
    'l3-8m-lat576': (64, 1, 8, 576),
    'l3-16m-lat528': (64, 1, 16, 528),
    'l3-16m-lat576': (64, 1, 16, 576),
}
MACROS = ('P4_NUM_TMS', 'P4_ENABLE_L3', 'P4_L3_MIB', 'P4_L3_LATENCY')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def variant(template, values):
    for key, value in zip(MACROS, values):
        template, count = re.subn(rf'^#define {key} \d+$', f'#define {key} {value}', template, flags=re.M)
        assert count == 1, key
    return template


def run(command, log, cwd=REPO):
    with log.open('w') as f:
        subprocess.run(command, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, check=True)


def parse_log(path):
    text = path.read_text()
    metrics = {'cycles': int(re.search(r'^Cycles: (\d+)$', text, re.M)[1])}
    metrics['frame_ms'] = metrics['cycles'] / 1_515_000
    for key, value in re.findall(r'(DRAM_read_bytes|DRAM_write_bytes|RT_rays)=(\d+)', text):
        metrics[key] = int(value)
    for level in ('L1d', 'L2', 'L3'):
        section = re.search(rf'^-+{level}\$-+\n(.*?)(?=^-{{5,}})', text, re.M | re.S)
        if not section:
            continue
        counters = {}
        for label in ('Total', 'Hits', 'Half Misses', 'Misses', 'MSHR Stalls', 'Uncached Requests'):
            counters[label] = int(re.search(rf'^{label}: (\d+)', section[1], re.M)[1])
        for label in ('Hits', 'Half Misses', 'Misses'):
            counters[label + ' percent'] = 100 * counters[label] / counters['Total']
        metrics[level] = counters
    assert metrics['DRAM_read_bytes'] == metrics['L3' if 'L3' in metrics else 'L2']['Misses'] * 32
    return metrics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results', type=Path, default=REPO / 'project4/results')
    p.add_argument('--scene', default='sponza')
    p.add_argument('--size', type=int, default=512)
    p.add_argument('--cases', nargs='+', choices=CASES, default=list(CASES)[:5])
    p.add_argument('--dataset-dir', type=Path, default=Path('/root/datasets'))
    args = p.parse_args()
    if args.size <= 0 or args.size % 8:
        p.error('Square dimensions must be positive multiples of 8 (handout tile mapping).')
    results = args.results.resolve()
    results.mkdir(parents=True, exist_ok=True)
    for name in args.cases:
        if (results / name).exists():
            raise FileExistsError(f'Refusing to overwrite {results / name}')

    compiler = shutil.which('riscv64-unknown-elf-g++') or '/opt/riscv/bin/riscv64-unknown-elf-g++'
    objdump = str(Path(compiler).with_name('riscv64-unknown-elf-objdump'))
    source = REPO / 'project4/kernel.cpp'
    assert source.read_bytes() == (KDIR / 'main.cpp').read_bytes()
    workload = results / 'workload'
    if not workload.exists():
        workload.mkdir()
        shutil.copy2(source, workload / 'kernel.cpp')
        command = [compiler, '-march=rv64imaf', '-mabi=lp64f', '-mno-relax',
                   '-nostartfiles', '-emain', '-Wstack-usage=512', '-O3', '-ffp-contract=off',
                   '-I', str(REPO / 'include'), '-I', str(KDIR),
                   str(source), '-o', str(KDIR / 'riscv/kernel')]
        run(command, workload / 'build.log')
        shutil.copy2(KDIR / 'riscv/kernel', workload / 'kernel')
        run([objdump, '-d', '-x', str(workload / 'kernel')], workload / 'kernel.dump')
        shutil.copy2(workload / 'kernel.dump', KDIR / 'riscv/kernel.dump')
        (workload / 'metadata.json').write_text(json.dumps({
            'compiler_command': command, 'kernel_sha256': sha(workload / 'kernel'),
            'scene': args.scene, 'size': args.size, 'source_sha256': sha(source),
            'obj_sha256': sha(args.dataset_dir / (args.scene + '.obj')),
            'mtl_sha256': sha(args.dataset_dir / (args.scene + '.mtl')),
        }, indent=2) + '\n')
    wmeta = json.loads((workload / 'metadata.json').read_text())
    assert (wmeta['scene'], wmeta['size'], wmeta['source_sha256']) == (args.scene, args.size, sha(source))
    assert wmeta['obj_sha256'] == sha(args.dataset_dir / (args.scene + '.obj'))
    shutil.copy2(workload / 'kernel', KDIR / 'riscv/kernel')
    shutil.copy2(workload / 'kernel.dump', KDIR / 'riscv/kernel.dump')
    expected_image = None
    for previous in results.glob('*/metadata.json'):
        if previous.parent.name != 'workload':
            expected_image = json.loads(previous.read_text())['image_pixels_sha256']
            break

    template = MAIN.read_text()
    try:
        for name in args.cases:
            output = results / name
            output.mkdir()
            values = CASES[name]
            MAIN.write_text(variant(template, values))
            shutil.copy2(MAIN, output / 'main.cpp')
            print(f'{name}: building {dict(zip(MACROS, values))}', flush=True)
            run(['cmake', '--build', 'build', '--target', 'arches-v2', '-j', '6'], output / 'build.log')
            command = ['stdbuf', '-oL', '-eL', str(SIM), '--arch-name=TRaX', f'--dataset-dir={args.dataset_dir.resolve()}',
                       f'--scene-name={args.scene}', f'--framebuffer-width={args.size}',
                       f'--framebuffer-height={args.size}', '--pregen-rays=0',
                       '--bvh-preset=0', '--bvh-merging=0', '--logging-interval=100000']
            meta = {'configuration': dict(zip(MACROS, values)), 'simulation_command': command,
                    'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
                    'kernel_sha256': sha(workload / 'kernel'), 'main_sha256': sha(MAIN),
                    'simulator_sha256': sha(SIM)}
            (output / 'metadata.json').write_text(json.dumps(meta, indent=2) + '\n')
            print(f'{name}: simulating {args.scene} {args.size}x{args.size}', flush=True)
            start = time.perf_counter()
            run(command, output / 'trax_log.txt', cwd=output)
            meta['wall_seconds'] = time.perf_counter() - start
            meta['returncode'] = 0
            meta['metrics'] = parse_log(output / 'trax_log.txt')
            image = Image.open(output / 'out.png').convert('RGBA')
            assert image.size == (args.size, args.size)
            assert image.getchannel('A').getextrema() == (255, 255), 'Unwritten pixels'
            assert len(set(image.get_flattened_data())) > 1, 'Blank/uniform image'
            meta['image_pixels_sha256'] = hashlib.sha256(image.tobytes()).hexdigest()
            meta['image_file_sha256'] = sha(output / 'out.png')
            meta['image_matches_other_configurations'] = expected_image is None or expected_image == meta['image_pixels_sha256']
            (output / 'metadata.json').write_text(json.dumps(meta, indent=2) + '\n')
            print(f"{name}: {meta['metrics']['cycles']} cycles, {meta['wall_seconds']:.1f}s wall, image match={meta['image_matches_other_configurations']}", flush=True)
            assert meta['image_matches_other_configurations'], 'Hardware configurations disagree on pixels'
            expected_image = meta['image_pixels_sha256']
    finally:
        MAIN.write_text(template)


if __name__ == '__main__':
    main()
