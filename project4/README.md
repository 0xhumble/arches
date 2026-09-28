# Project 4 — TRaX hardware configuration and L3 capacity study

## Scope

The experiments in this directory cover the prescribed A/B/C configurations and **only the first proposed research axis: L3 capacity, followed by latency sensitivity**. It does not tune L2 sharing groups, bank counts, MSHRs, merging capacity, clock frequency, or the workload between configurations.

- Upstream base: `146642691df5b1101a25ba5821dce6a67ece318f` (L3 cache-omit flag support).
- The Project 3 store-drain and halted-thread correctness fixes are retained.
- The experimental simulator is `src/arches-v2/main.cpp`. Four `P4_*` constants select the configuration; each run archives its complete `main.cpp`.
- Start with [findings.md](findings.md) for the Chinese interpretation. `summary.md`, `summary.csv`, and `summary.json` contain measured results; `results/` contains unedited simulator logs, images, build logs and provenance.
- `submission/` contains the four required raw logs and the best **three-level** simulator `main.cpp` (16 MiB, 480 cycles). The original two-level B remains faster overall. This is a staged result package, not the final PDF report.

## Controlled workload

- Dataset `/root/datasets/sponza.obj`, 262,267 triangles; the dataset's built-in Sponza camera.
- 512 × 512 pixels, SPP=1, 4 × 8 tiles, at most three traced ray segments per pixel; per-pixel deterministic RNG seeds.
- Identical compiled RISC-V ELF for every run, `pregen-rays=0`, BVH preset 0, merging disabled.
- Cold simulated caches and identical data placement each run. A cached host BVH file speeds preprocessing only; it does **not** warm simulated caches.
- 1.515 GHz simulated core clock, unchanged DRAM, 64 TPs/TM and 8 hardware threads/TP.
- Image dimensions divide the handout tile dimensions exactly; no scheduler or edge-handling changes are needed.

`kernel.cpp` follows the handout with these corrections only: add missing constant types, correct normal indices `0,2,3` to `0,1,2` (consistent with the intersection barycentrics), and make the alpha shift unsigned. The handout's radiance/clamping rules are retained: any path escaping within three segments saturates to white; paths not escaping are black. No image postprocessing is applied to simulator images.

Sponza was selected rather than teapot to exercise a substantial footprint. Compressed BVH nodes and primitive blocks alone occupy about 26.6 MiB, excluding normal indices/normals. This is allocated footprint, **not** a measurement of the active working set. An initial 64² crytek-sponza smoke attempt failed in the existing material loader with that dataset's empty material definitions; no results from that attempt are included in the experiment. No loader patch or dataset modification was made.

## Hardware configurations

| Case | TMs | L1/TM | L2 organization | L3 total | L2/L3 latency |
|---|---:|---:|---|---:|---|
| A | 8 | 64 KiB | 8 global 512 KiB partitions | none | 160 / — |
| B | 64 | 64 KiB | same as A | none | 160 / — |
| C | 64 | 64 KiB | 8 groups × 512 KiB, 8 TMs/group | 4 MiB | 160 / 480 cycles |
| Capacity | 64 | 64 KiB | same as C | 8 or 16 MiB | 160 / 480 cycles |
| Sensitivity | 64 | 64 KiB | same as C | expanded capacity | 160 / 528 or 576 cycles |

For C, each local L2 has **one slice, four banks, eight L1 ports, 192 MSHRs per slice and four subentries/MSHR**. It connects to one crossbar client port. The original global L2 becomes eight global L3 partitions, each with four slices and one bank/slice. All original associativity, allocation policy and memory parameters are retained. The original L2 latency remains 160 cycles; the tutorial's higher L3 latency is 480 cycles.

The capacity sweep changes only per-partition L3 capacity (512 KiB → 1 MiB → 2 MiB). Sensitivity then changes only L3 latency. 528/576 cycles represent hypothetical +10%/+20% latency penalties, **not measured AMD hardware latencies**. This studies a large shared last-level-cache idea; it does not model physical 3D stacking, thermal limits, area, coherence or heterogeneous SoC clients.

A/B keep per-TM resources constant, but total L1 and RT-core resources naturally scale with the TM count; their speedup must not be attributed exclusively to arithmetic cores.

## Reproduction

Run long commands **inside tmux**, from the repository root. Requires the existing CMake build, `/opt/riscv` toolchain, `/root/datasets`, `uv` and native G++.

```bash
# A, B, C, then 8/16 MiB at constant 480-cycle L3 latency:
uv run --with pillow python project4/run.py --results /tmp/project4-results

# Additional sensitivity cases (select the promising expanded capacity):
uv run --with pillow python project4/run.py --results /tmp/project4-results \
  --cases l3-16m-lat528 l3-16m-lat576

# Cold-start reproducibility check of the best three-level case:
uv run --with pillow python project4/run.py --results /tmp/project4-repeat --cases l3-16m

# Validate the archived project4/results and project4/repeat; regenerate summaries:
bash project4/validate.sh
```

`run.py` refuses to overwrite existing case directories. Compilation and simulation are serial because Arches loads one fixed ELF path. On exit the script restores the original simulator source template; the last executable still corresponds to the last case, so rebuild before manually invoking it with the restored source. No case uses a persistent/warmed simulator process.

Each run records the configuration, exact command, source/ELF/executable SHA-256, raw log, PNG, cycle count, cache counters and DRAM bytes. The metadata's Git HEAD is the base at execution time; modified source provenance is provided by the archived `main.cpp` plus its hash, not falsely represented as that commit's unmodified code. Workload metadata fingerprints the OBJ, MTL, source and ELF.

## Correctness and interpretation

- A 64² smoke test verifies that A/B/C render the same pixels before the formal runs.
- Every formal run must produce fully opaque, nonuniform output identical **pixel for pixel** across hardware configurations. The final analysis also compares traced-ray counts and verifies that only the four configuration constants vary between simulator source snapshots.
- `reference.cpp` + `reference-trace.cpp` provide a CPU software-traversal reference, sharing the scene and geometry library but not the simulator/cache/RT-unit execution path. The host oracle explicitly sequences the RNG coordinates because `vec2(randf(), randf())` has compiler-dependent argument evaluation order; it does not change the RISC-V workload. The reference shader disables FP contraction like the RISC-V kernel, while its traversal translation unit uses native simulator contraction settings.
- CPU-oracle pixel discrepancies, if any, are recorded explicitly in `validation/checks.json`, not hidden by a tolerance or claimed to be zero. Cross-configuration image equality is always strict. Equal ray totals and near-identical CPU output are useful checks, not a proof of bit-exact geometry equivalence.
- Report performance using **simulated cycles** (and derived frame time), not host wall time. Host simulation parallelism changes with unit grouping and is not hardware performance.
- Cache rates are aggregate counts across all modules. `Half Misses` are coalesced requests to an outstanding miss, not ordinary data-array hits. True non-hit rate is `Half Misses + Misses`; only `Misses` generates a new lower-level sector request in this no-prefetch setup.
- The simulator's `MSHR Stalls` counter also includes blocked return/miss queues; do not interpret it as an exact count of cycles with a full MSHR table.
- Power configurations are uncalibrated/zero in this setup; power/energy output is not used for conclusions.
