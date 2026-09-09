#!/usr/bin/env python3
"""Compile and simulate serially: Arches loads one fixed kernel pathname.
Run in tmux. Requires the course toolchain, simulator build and datasets.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

repo = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--dataset-dir', default='/root/datasets')
parser.add_argument('--results', type=Path, default=repo / 'project2/results')
parser.add_argument('--case', choices=['all', 'gradient', 'single-pass', 'mandelbrot'], default='all')
parser.add_argument('--size', type=int, help='Default: 256 for gradients, 512 for Mandelbrot')
args = parser.parse_args()
compiler = shutil.which('riscv64-unknown-elf-g++') or '/opt/riscv/bin/riscv64-unknown-elf-g++'
objdump = str(Path(compiler).with_name('riscv64-unknown-elf-objdump'))
kernel_dir = repo / 'src/trax-kernel'
cases = ['gradient', 'single-pass', 'mandelbrot'] if args.case == 'all' else [args.case]
for case in cases:
    size = args.size if args.size is not None else (512 if case == 'mandelbrot' else 256)
    if size <= 200:
        raise ValueError('The assignment requests dimensions greater than 200')
    output = args.results.resolve() / f'{case}-{size}'
    if output.exists():
        raise FileExistsError(f'Preserving existing results: {output}. Use --results with a new directory.')
    output.mkdir(parents=True)
    source = kernel_dir / 'main.cpp' if case == 'mandelbrot' else repo / 'project2/gradient.cpp'
    shutil.copy2(source, output / 'main.cpp')
    command = [compiler, '-march=rv64imaf', '-mabi=lp64f', '-mno-relax',
               '-nostartfiles', '-emain', '-Wstack-usage=512', '-O3', '-ffp-contract=off',
               '-I', str(repo / 'include'), '-I', str(kernel_dir)]
    if case == 'single-pass':
        command += ['-DGRADIENT_SINGLE_PASS']
    command += [str(source), '-o', str(kernel_dir / 'riscv/kernel')]
    with (output / 'build.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    shutil.copy2(kernel_dir / 'riscv/kernel', output / 'kernel')
    with (output / 'kernel.dump').open('w') as log:
        subprocess.run([objdump, '-d', '-x', str(output / 'kernel')], stdout=log, check=True)
    shutil.copy2(output / 'kernel.dump', kernel_dir / 'riscv/kernel.dump')
    sim_command = [str(repo / 'build/src/arches-v2/arches-v2'), '--arch-name=TRaX',
                   f'--dataset-dir={Path(args.dataset_dir).resolve()}', '--scene-name=teapot',
                   f'--framebuffer-width={size}', f'--framebuffer-height={size}',
                   '--pregen-rays=0', '--logging-interval=100000']
    print(f'Starting {case} at {size}x{size}', flush=True)
    start = time.perf_counter()
    with (output / 'trax_log.txt').open('w') as log:
        result = subprocess.run(sim_command, cwd=output, stdout=log, stderr=subprocess.STDOUT)
    metadata = dict(case=case, size=size, compiler_command=command,
                    simulation_command=sim_command, wall_seconds=time.perf_counter()-start,
                    returncode=result.returncode, upstream='97bebdcd75948baf72d6334890d2793ccd66afe6',
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    kernel_sha256=hashlib.sha256((output/'kernel').read_bytes()).hexdigest())
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps(metadata), flush=True)
    result.check_returncode()
    if not (output / 'out.png').is_file():
        raise RuntimeError('Simulator did not produce out.png')
