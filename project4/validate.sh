#!/usr/bin/env bash
# Run inside tmux after completing the simulation batch.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p project4/validation
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
# Match the simulator RT core's native contraction setting, while keeping
# the reference shader aligned with the RISC-V kernel's -ffp-contract=off.
g++ -std=c++20 -O3 -march=native -I include -I src/trax-kernel \
    -c project4/reference-trace.cpp -o "$tmp/trace.o" \
    > project4/validation/build.log 2>&1
g++ -std=c++20 -O3 -march=native -ffp-contract=off -I include -I src/trax-kernel \
    project4/reference.cpp src/trax-kernel/stbi.cpp "$tmp/trace.o" -o "$tmp/reference" \
    >> project4/validation/build.log 2>&1
"$tmp/reference" /root/datasets 512 "$tmp/reference.rgba" "$tmp/reference.json" \
    > project4/validation/reference.log 2>&1
uv run --with pillow python project4/analyze.py \
    --reference "$tmp/reference.rgba" --reference-metrics "$tmp/reference.json"
