# Project 5 — Adding Custom Instructions

Base: upstream `146642691df5b1101a25ba5821dce6a67ece318f`, in a fresh worktree. Hardware and build flags remain upstream defaults; no Project 4 hardware changes are included.

## Changes

- `src/trax-kernel/main.cpp`: the handout kernel, completed software interpolation and the specified inline assembly.
- `src/arches-v2/main.cpp`: BaryInterp3 execution callback and BARYINT3 name registration.
- `src/arches-v2/units/trax/unit-tp.hpp`: the handout's input-register dependency check.
- At the user's explicit request, the previous termination fixes are ported unchanged into `unit-tp.cpp`, `unit-cache.cpp`, `unit-crossbar.hpp`, and `unit-dram.cpp`: do not re-execute halted threads; keep posted stores alive until functional DRAM memory is updated. These fixes are not part of the handout.

## Results

- `software/`: completed Part B kernel and its disassembly, before using the instruction.
- `custom/`: original run before the termination fix, preserved unchanged.
- `custom-fixed/`: final run after the fix, with raw log, image, build log and validation record.
- `0001800b` appears at two compiler-generated sites in the custom dump and is absent from the software dump; the simulation logs BARYINT3 execution.
- Final run: 118,489 cycles, normal exit. All 262,144 pixels are opaque. The 17 previously unwritten pixels are filled; all previously written pixels are unchanged.

Build with `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`, `cmake --build build --target arches-v2 -j 6`, and `make -C src/trax-kernel`. Run long commands through tmux. Simulation command, from a new output directory two levels below the repository root:

```sh
../../build/src/arches-v2/arches-v2 --arch-name=TRaX --dataset-dir=/root/datasets --scene-name=sponza --framebuffer-width=512 --framebuffer-height=512 --pregen-rays=0 --bvh-preset=0 --bvh-merging=0 --logging-interval=100000
```

## Submission

`submission/` contains exactly the four handout items:

- `trax_log.txt`
- `kernel/main.cpp`
- `arches/main.cpp`
- `report.pdf`

The two source files use separate directories to retain their required `main.cpp` names. `report.typ` is the report source. The report answers each question in two sentences and includes the final rendered image. The dependency check and termination fixes remain in the repository, rather than adding unrequested files to the submission.
